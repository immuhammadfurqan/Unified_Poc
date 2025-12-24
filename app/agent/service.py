"""
Agent Service

AI-powered assistant that uses OpenAI with function calling
to execute GitHub operations via natural language instructions.
"""

from typing import List, Dict, Any
import json

from openai import AsyncOpenAI

from app.github_integration.service import GitHubService
from app.sandbox.service import SandboxService
from app.core.config import settings


class AgentService:
    """
    AI agent service that processes natural language instructions
    and executes GitHub operations using OpenAI's function calling capabilities.
    """

    def __init__(self, github_service: GitHubService):
        self.github_service = github_service
        self.sandbox_service = SandboxService()
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        # Define tools in OpenAI's format
        self.tools = [
            # --- GitHub Tools ---
            {
                "type": "function",
                "function": {
                    "name": "create_repo",
                    "description": "Create a new GitHub repository for the user",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "The name of the repository to create",
                            },
                            "private": {
                                "type": "boolean",
                                "description": "Whether the repository should be private. Defaults to false (public).",
                            },
                        },
                        "required": ["name"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_repos",
                    "description": "List all GitHub repositories for the user",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_issue",
                    "description": "Create a new issue in a GitHub repository",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "repo_name": {
                                "type": "string",
                                "description": "The name of the repository (e.g., 'my-repo' or 'owner/my-repo')",
                            },
                            "title": {
                                "type": "string",
                                "description": "The title of the issue",
                            },
                            "body": {
                                "type": "string",
                                "description": "The body/description of the issue",
                            },
                        },
                        "required": ["repo_name", "title", "body"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_issues",
                    "description": "List all issues in a GitHub repository",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "repo_name": {
                                "type": "string",
                                "description": "The name of the repository",
                            }
                        },
                        "required": ["repo_name"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_file_content",
                    "description": "Get the content of a file from a GitHub repository",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "repo_name": {
                                "type": "string",
                                "description": "The name of the repository",
                            },
                            "path": {
                                "type": "string",
                                "description": "The file path within the repository (e.g., 'README.md' or 'src/main.py')",
                            },
                        },
                        "required": ["repo_name", "path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_file",
                    "description": "Create or update a file in a GitHub repository",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "repo_name": {
                                "type": "string",
                                "description": "The name of the repository",
                            },
                            "path": {
                                "type": "string",
                                "description": "The file path within the repository (e.g., 'README.md' or '.gitignore')",
                            },
                            "content": {
                                "type": "string",
                                "description": "The content of the file to create",
                            },
                            "message": {
                                "type": "string",
                                "description": "The commit message for this file creation",
                            },
                        },
                        "required": ["repo_name", "path", "content", "message"],
                    },
                },
            },
            # --- Sandbox Tools ---
            {
                "type": "function",
                "function": {
                    "name": "setup_dev_environment",
                    "description": "Setup a new development environment (sandbox) for running code",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "image": {
                                "type": "string",
                                "description": "The image to use (e.g., 'node:18' or 'python:3.11')",
                                "enum": ["node:18", "python:3.11"],
                            }
                        },
                        "required": ["image"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "run_terminal_command",
                    "description": "Run a shell command in the sandbox environment",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "container_id": {
                                "type": "string",
                                "description": "The ID of the sandbox container",
                            },
                            "command": {
                                "type": "string",
                                "description": "The shell command to execute",
                            },
                            "background": {
                                "type": "boolean",
                                "description": "Whether to run in background (for servers). Defaults to false.",
                            },
                        },
                        "required": ["container_id", "command"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "write_sandbox_file",
                    "description": "Write a file to the sandbox environment",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "container_id": {
                                "type": "string",
                                "description": "The ID of the sandbox container",
                            },
                            "path": {
                                "type": "string",
                                "description": "The file path relative to /app",
                            },
                            "content": {
                                "type": "string",
                                "description": "The content of the file",
                            },
                        },
                        "required": ["container_id", "path", "content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "read_sandbox_file",
                    "description": "Read a file from the sandbox environment",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "container_id": {
                                "type": "string",
                                "description": "The ID of the sandbox container",
                            },
                            "path": {
                                "type": "string",
                                "description": "The file path relative to /app",
                            },
                        },
                        "required": ["container_id", "path"],
                    },
                },
            },
        ]

    async def chat(self, user_id: int, messages: List[Dict[str, str]]) -> str:
        """
        Process a chat conversation with tool calling support.

        Args:
            user_id: The ID of the user making the request
            messages: List of message dicts with 'role' and 'content' keys

        Returns:
            The assistant's response as a string
        """
        # Ensure system message is present
        if not messages or messages[0].get("role") != "system":
            messages.insert(
                0,
                {
                    "role": "system",
                    "content": """You are an autonomous AI software engineer (Replit-style). 
Your goal is to build, execute, and deliver working code immediately.

**CORE RULES:**
1. **ACTION OVER TALK**: Do NOT explain your plan. Do NOT say "I will create a file". JUST CREATE IT.
2. **USE TOOLS IMMEDIATELY**: When a user asks for a task, start calling tools in your FIRST response.
3. **FULL IMPLEMENTATION**: Create ALL necessary files (main.py, requirements.txt, etc.) to make the app runnable.
4. **EXECUTE & VERIFY**: Always run the code you wrote to prove it works.
   - For web apps: Run the server in the background binding to 0.0.0.0 (required for access) and tell the user the URL.
   - For scripts: Run the script and show the output.
5. **GIT PERSISTENCE**: If the user mentions "push", "save", or "github", use the GitHub tools to save the work.

**Workflow for "Create a [App]":**
1. `setup_dev_environment(image=...)`
2. `write_sandbox_file(...)` (Repeat for all files)
3. `run_terminal_command("pip install ...")`
4. `run_terminal_command("python main.py", background=True)` (Ensure host=0.0.0.0)
5. Final Response: "App is running at [URL]. I have created [Files]."

**Workflow for "Push to GitHub":**
1. `create_repo(...)`
2. `run_terminal_command("git init && git add . && git commit -m 'init' && git push ...")`

Be fast, efficient, and precise. Do not chat unless asking for clarification.""",
                },
            )

        # Initial API call
        response = await self.client.chat.completions.create(
            model="gpt-5", messages=messages, tools=self.tools, tool_choice="auto"
        )

        response_message = response.choices[0].message

        # Process tool calls if any
        if response_message.tool_calls:
            # Append the assistant's message with tool calls
            messages.append(response_message)

            # Execute each tool and add results
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                tool_result = await self._execute_tool(
                    user_id, function_name, function_args
                )

                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps(tool_result),
                    }
                )

            # Get final response after tool execution
            second_response = await self.client.chat.completions.create(
                model="gpt-5", messages=messages
            )
            return second_response.choices[0].message.content

        return response_message.content

    async def chat_stream(self, user_id: int, messages: List[Dict[str, str]]):
        """
        Process a chat conversation with streaming response and tool calling.
        """
        # Ensure system message is present
        if not messages or messages[0].get("role") != "system":
            messages.insert(
                0,
                {
                    "role": "system",
                    "content": """You are an autonomous AI software engineer (Replit-style). 
Your goal is to build, execute, and deliver working code immediately.

**CORE RULES:**
1. **ACTION OVER TALK**: Do NOT explain your plan. Do NOT say "I will create a file". JUST CREATE IT.
2. **USE TOOLS IMMEDIATELY**: When a user asks for a task, start calling tools in your FIRST response.
3. **FULL IMPLEMENTATION**: Create ALL necessary files (main.py, requirements.txt, etc.) to make the app runnable.
4. **EXECUTE & VERIFY**: Always run the code you wrote to prove it works.
   - For web apps: Run the server in the background binding to 0.0.0.0 (required for access) and tell the user the URL.
   - For scripts: Run the script and show the output.
5. **GIT PERSISTENCE**: If the user mentions "push", "save", or "github", use the GitHub tools to save the work.

**Workflow for "Create a [App]":**
1. `setup_dev_environment(image=...)`
2. `write_sandbox_file(...)` (Repeat for all files)
3. `run_terminal_command("pip install ...")`
4. `run_terminal_command("python main.py", background=True)` (Ensure host=0.0.0.0)
5. Final Response: "App is running at [URL]. I have created [Files]."

**Workflow for "Push to GitHub":**
1. `create_repo(...)`
2. `run_terminal_command("git init && git add . && git commit -m 'init' && git push ...")`

Be fast, efficient, and precise. Do not chat unless asking for clarification.""",
                },
            )

        # Initial API call with stream=True
        response = await self.client.chat.completions.create(
            model="gpt-5",
            messages=messages,
            tools=self.tools,
            tool_choice="auto",
            stream=True,
        )

        # Buffer for accumulating tool calls
        tool_calls = []

        async for chunk in response:
            delta = chunk.choices[0].delta

            # handle tool calls
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    if tc.index >= len(tool_calls):
                        tool_calls.append(
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {"name": "", "arguments": ""},
                            }
                        )

                    if tc.function.name:
                        tool_calls[tc.index]["function"]["name"] += tc.function.name
                    if tc.function.arguments:
                        tool_calls[tc.index]["function"][
                            "arguments"
                        ] += tc.function.arguments

            # handle regular content
            if delta.content:
                yield json.dumps({"type": "content", "content": delta.content}) + "\n"

        # If we collected tool calls, execute them
        if tool_calls:
            # Reconstruct tool call objects properly
            # OpenAI expects the full tool call object structure in messages
            formatted_tool_calls = []
            for tc in tool_calls:
                formatted_tool_calls.append(
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["function"]["name"],
                            "arguments": tc["function"]["arguments"],
                        },
                    }
                )

            messages.append(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": formatted_tool_calls,
                }
            )

            for tool_call in tool_calls:
                function_name = tool_call["function"]["name"]
                function_args = json.loads(tool_call["function"]["arguments"])

                # Yield tool execution status
                yield json.dumps(
                    {"type": "tool_start", "name": function_name, "args": function_args}
                ) + "\n"

                tool_result = await self._execute_tool(
                    user_id, function_name, function_args
                )

                yield json.dumps(
                    {
                        "type": "tool_result",
                        "name": function_name,
                        "result": tool_result,
                    }
                ) + "\n"

                messages.append(
                    {
                        "tool_call_id": tool_call["id"],
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps(tool_result),
                    }
                )

            # Get final response after tool execution (streaming)
            second_response = await self.client.chat.completions.create(
                model="gpt-5", messages=messages, stream=True
            )

            async for chunk in second_response:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield json.dumps(
                        {"type": "content", "content": delta.content}
                    ) + "\n"

    async def _execute_tool(self, user_id: int, name: str, args: Dict[str, Any]) -> Any:
        """
        Execute a tool by name with the given arguments.
        """
        try:
            # GitHub Tools
            if name == "create_repo":
                return await self.github_service.create_repo(
                    user_id, args["name"], args.get("private", False)
                )
            elif name == "list_repos":
                repos = await self.github_service.list_repos(user_id)
                return [
                    {
                        "name": repo.get("name"),
                        "full_name": repo.get("full_name"),
                        "private": repo.get("private"),
                        "url": repo.get("html_url"),
                    }
                    for repo in repos
                ]
            elif name == "create_issue":
                return await self.github_service.create_issue(
                    user_id, args["repo_name"], args["title"], args["body"]
                )
            elif name == "list_issues":
                issues = await self.github_service.list_issues(
                    user_id, args["repo_name"]
                )
                return [
                    {
                        "number": issue.get("number"),
                        "title": issue.get("title"),
                        "state": issue.get("state"),
                        "url": issue.get("html_url"),
                    }
                    for issue in issues
                ]
            elif name == "get_file_content":
                return await self.github_service.get_file_content(
                    user_id, args["repo_name"], args["path"]
                )
            elif name == "create_file":
                return await self.github_service.create_file(
                    user_id,
                    args["repo_name"],
                    args["path"],
                    args["content"],
                    args.get("message", f"Add {args['path']}"),
                )

            # Sandbox Tools
            elif name == "setup_dev_environment":
                result = self.sandbox_service.create_sandbox(user_id, args["image"])

                # Try to inject git credentials
                try:
                    token = await self.github_service.get_token(user_id)
                    # Configure git with token-based auth URL for push
                    # We don't expose the token in the response
                    container_id = result["container_id"]

                    self.sandbox_service.execute_command(
                        container_id,
                        "git config --global user.email 'agent@example.com' && git config --global user.name 'AI Agent'",
                    )

                    self.sandbox_service.execute_command(
                        container_id, f"export GITHUB_TOKEN={token}"
                    )
                except Exception as e:
                    pass

                return result
            elif name == "run_terminal_command":
                return self.sandbox_service.execute_command(
                    args["container_id"],
                    args["command"],
                    background=args.get("background", False),
                )
            elif name == "write_sandbox_file":
                return self.sandbox_service.write_file(
                    args["container_id"], args["path"], args["content"]
                )
            elif name == "read_sandbox_file":
                return self.sandbox_service.read_file(
                    args["container_id"], args["path"]
                )

            else:
                return {"error": f"Unknown tool: {name}"}
        except ValueError as e:
            # Handle missing integration errors
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}
