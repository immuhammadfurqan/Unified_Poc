"""
Agent Service

AI-powered assistant that uses OpenAI with function calling
to execute operations via natural language instructions.

This module follows Clean Code principles:
- Single Responsibility: Each class/function does one thing
- DRY: Common logic extracted to helper methods
- Small Functions: Complex logic broken into focused methods
- Dependency Injection: Dependencies passed via constructor
"""

from typing import List, Dict, Any, AsyncGenerator
import json

from openai import AsyncOpenAI

from app.github_integration.service import GitHubService
from app.sandbox.service import SandboxService
from app.core.config import settings
from app.agent.constants import DEFAULT_MODEL
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.tools import get_all_tools
from app.agent.handlers import GitHubToolHandler, SandboxToolHandler, ToolExecutor


class AgentService:
    """
    AI agent service that processes natural language instructions
    and executes operations using OpenAI's function calling capabilities.
    
    Responsibilities:
    - Manage chat conversations with OpenAI
    - Coordinate tool execution via ToolExecutor
    """

    def __init__(self, github_service: GitHubService):
        self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self._tools = get_all_tools()
        self._tool_executor = self._create_tool_executor(github_service)

    def _create_tool_executor(self, github_service: GitHubService) -> ToolExecutor:
        """Factory method to create the tool executor with its dependencies."""
        sandbox_service = SandboxService()
        github_handler = GitHubToolHandler(github_service)
        sandbox_handler = SandboxToolHandler(sandbox_service, github_handler)
        return ToolExecutor(github_handler, sandbox_handler)

    async def chat(self, user_id: int, messages: List[Dict[str, str]]) -> str:
        """
        Process a chat conversation with tool calling support.

        Args:
            user_id: The ID of the user making the request
            messages: List of message dicts with 'role' and 'content' keys

        Returns:
            The assistant's response as a string
        """
        self._ensure_system_message(messages)
        
        response = await self._call_openai(messages)
        response_message = response.choices[0].message

        if not response_message.tool_calls:
            return response_message.content

        messages.append(response_message)
        await self._execute_tool_calls(user_id, response_message.tool_calls, messages)
        
        final_response = await self._call_openai(messages, include_tools=False)
        return final_response.choices[0].message.content

    async def chat_stream(self, user_id: int, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """
        Process a chat conversation with streaming response and tool calling.
        
        Yields:
            JSON-formatted strings containing content or tool execution updates
        """
        self._ensure_system_message(messages)
        while True:
            tool_calls = []
            async for chunk in await self._call_openai_stream(messages):
                delta = chunk.choices[0].delta
                
                if delta.tool_calls:
                    self._accumulate_tool_calls(delta.tool_calls, tool_calls)
                
                if delta.content:
                    yield self._format_content_chunk(delta.content)

            if not tool_calls:
                break

            formatted_calls = self._format_accumulated_tool_calls(tool_calls)
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": formatted_calls,
            })

            for tool_call in tool_calls:
                async for chunk in self._execute_and_yield_tool_result(user_id, tool_call, messages):
                    yield chunk

    def _ensure_system_message(self, messages: List[Dict[str, str]]) -> None:
        """Ensures the conversation has a system message."""
        if not messages or messages[0].get("role") != "system":
            messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})

    async def _call_openai(self, messages: List[Dict], include_tools: bool = True):
        """Makes a non-streaming call to OpenAI API."""
        kwargs = {"model": DEFAULT_MODEL, "messages": messages}
        if include_tools:
            kwargs["tools"] = self._tools
            kwargs["tool_choice"] = "auto"
        return await self._client.chat.completions.create(**kwargs)

    async def _call_openai_stream(self, messages: List[Dict]):
        """Makes a streaming call to OpenAI API."""
        return await self._client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages,
            tools=self._tools,
            tool_choice="auto",
            stream=True,
        )

    async def _execute_tool_calls(
        self, 
        user_id: int, 
        tool_calls: List, 
        messages: List[Dict]
    ) -> None:
        """Executes tool calls and appends results to messages."""
        for tool_call in tool_calls:
            result = await self._execute_single_tool(user_id, tool_call)
            messages.append(self._format_tool_result(tool_call, result))

    async def _execute_single_tool(self, user_id: int, tool_call) -> Any:
        """Executes a single tool call."""
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        return await self._tool_executor.execute(user_id, function_name, function_args)

    @staticmethod
    def _format_tool_result(tool_call, result: Any) -> Dict[str, Any]:
        """Formats a tool result for the messages list."""
        return {
            "tool_call_id": tool_call.id,
            "role": "tool",
            "name": tool_call.function.name,
            "content": json.dumps(result),
        }

    @staticmethod
    def _format_content_chunk(content: str) -> str:
        """Formats a content chunk for streaming."""
        return json.dumps({"type": "content", "content": content}) + "\n"

    @staticmethod
    def _accumulate_tool_calls(delta_tool_calls: List, accumulated: List) -> None:
        """Accumulates streaming tool call chunks."""
        for tc in delta_tool_calls:
            if tc.index >= len(accumulated):
                accumulated.append({
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": "", "arguments": ""},
                })
            
            if tc.function.name:
                accumulated[tc.index]["function"]["name"] += tc.function.name
            if tc.function.arguments:
                accumulated[tc.index]["function"]["arguments"] += tc.function.arguments

    async def _process_streamed_tool_calls(
        self, 
        user_id: int, 
        tool_calls: List[Dict], 
        messages: List[Dict]
    ) -> AsyncGenerator[str, None]:
        """Processes accumulated tool calls from streaming and yields updates."""
        formatted_calls = self._format_accumulated_tool_calls(tool_calls)
        messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": formatted_calls,
        })

        for tool_call in tool_calls:
            async for chunk in self._execute_and_yield_tool_result(user_id, tool_call, messages):
                yield chunk

        async for chunk in self._stream_final_response(messages):
            yield chunk

    @staticmethod
    def _format_accumulated_tool_calls(tool_calls: List[Dict]) -> List[Dict]:
        """Formats accumulated tool calls for the messages list."""
        return [
            {
                "id": tc["id"],
                "type": "function",
                "function": {
                    "name": tc["function"]["name"],
                    "arguments": tc["function"]["arguments"],
                },
            }
            for tc in tool_calls
        ]

    async def _execute_and_yield_tool_result(
        self, 
        user_id: int, 
        tool_call: Dict, 
        messages: List[Dict]
    ) -> AsyncGenerator[str, None]:
        """Executes a tool and yields start/result updates."""
        function_name = tool_call["function"]["name"]
        function_args = json.loads(tool_call["function"]["arguments"])

        yield json.dumps({
            "type": "tool_start", 
            "name": function_name, 
            "args": function_args
        }) + "\n"

        result = await self._tool_executor.execute(user_id, function_name, function_args)

        yield json.dumps({
            "type": "tool_result",
            "name": function_name,
            "result": result,
        }) + "\n"

        messages.append({
            "tool_call_id": tool_call["id"],
            "role": "tool",
            "name": function_name,
            "content": json.dumps(result),
        })

    async def _stream_final_response(self, messages: List[Dict]) -> AsyncGenerator[str, None]:
        """Streams the final response after tool execution."""
        response = await self._client.chat.completions.create(
            model=DEFAULT_MODEL, 
            messages=messages, 
            stream=True
        )
        
        async for chunk in response:
            delta = chunk.choices[0].delta
            if delta.content:
                yield self._format_content_chunk(delta.content)
