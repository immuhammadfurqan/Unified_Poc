"""
Agent Service

AI-powered assistant that uses OpenAI with function calling
to execute GitHub operations via natural language instructions.
"""

from typing import List, Dict, Any
import json

from openai import AsyncOpenAI

from app.github_integration.service import GitHubService
from app.core.config import settings


class AgentService:
    """
    AI agent service that processes natural language instructions
    and executes GitHub operations using OpenAI's function calling capabilities.
    """
    
    def __init__(self, github_service: GitHubService):
        self.github_service = github_service
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Define tools in OpenAI's format
        self.tools = [
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
                                "description": "The name of the repository to create"
                            },
                            "private": {
                                "type": "boolean",
                                "description": "Whether the repository should be private. Defaults to false (public)."
                            }
                        },
                        "required": ["name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_repos",
                    "description": "List all GitHub repositories for the user",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
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
                                "description": "The name of the repository (e.g., 'my-repo' or 'owner/my-repo')"
                            },
                            "title": {
                                "type": "string",
                                "description": "The title of the issue"
                            },
                            "body": {
                                "type": "string",
                                "description": "The body/description of the issue"
                            }
                        },
                        "required": ["repo_name", "title", "body"]
                    }
                }
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
                                "description": "The name of the repository"
                            }
                        },
                        "required": ["repo_name"]
                    }
                }
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
                                "description": "The name of the repository"
                            },
                            "path": {
                                "type": "string",
                                "description": "The file path within the repository (e.g., 'README.md' or 'src/main.py')"
                            }
                        },
                        "required": ["repo_name", "path"]
                    }
                }
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
                                "description": "The name of the repository"
                            },
                            "path": {
                                "type": "string",
                                "description": "The file path within the repository (e.g., 'README.md' or '.gitignore')"
                            },
                            "content": {
                                "type": "string",
                                "description": "The content of the file to create"
                            },
                            "message": {
                                "type": "string",
                                "description": "The commit message for this file creation"
                            }
                        },
                        "required": ["repo_name", "path", "content", "message"]
                    }
                }
            }
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
            messages.insert(0, {
                "role": "system",
                "content": """You are a helpful GitHub assistant. You help users manage their GitHub repositories, issues, and files.

When users ask you to perform GitHub operations, use the available tools to complete their requests. Always confirm what you're doing and provide clear feedback about the results.

Available capabilities:
- Create repositories (public or private)
- List user's repositories
- Create issues in repositories
- List issues in repositories
- Read file contents from repositories
- Create or update files in repositories (README.md, .gitignore, etc.)

Be concise but informative in your responses. If an operation fails, explain what went wrong and suggest alternatives."""
            })

        # Initial API call
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=self.tools,
            tool_choice="auto"
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
                
                tool_result = await self._execute_tool(user_id, function_name, function_args)
                
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(tool_result)
                })
            
            # Get final response after tool execution
            second_response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )
            return second_response.choices[0].message.content
        
        return response_message.content

    async def _execute_tool(self, user_id: int, name: str, args: Dict[str, Any]) -> Any:
        """
        Execute a tool by name with the given arguments.
        
        Args:
            user_id: The ID of the user making the request
            name: The name of the tool to execute
            args: The arguments to pass to the tool
            
        Returns:
            The result of the tool execution
        """
        try:
            if name == "create_repo":
                return await self.github_service.create_repo(
                    user_id, 
                    args["name"], 
                    args.get("private", False)
                )
            elif name == "list_repos":
                repos = await self.github_service.list_repos(user_id)
                # Return a simplified list for better readability
                return [
                    {
                        "name": repo.get("name"),
                        "full_name": repo.get("full_name"),
                        "private": repo.get("private"),
                        "url": repo.get("html_url")
                    }
                    for repo in repos
                ]
            elif name == "create_issue":
                return await self.github_service.create_issue(
                    user_id, 
                    args["repo_name"], 
                    args["title"], 
                    args["body"]
                )
            elif name == "list_issues":
                issues = await self.github_service.list_issues(user_id, args["repo_name"])
                # Return a simplified list
                return [
                    {
                        "number": issue.get("number"),
                        "title": issue.get("title"),
                        "state": issue.get("state"),
                        "url": issue.get("html_url")
                    }
                    for issue in issues
                ]
            elif name == "get_file_content":
                return await self.github_service.get_file_content(
                    user_id, 
                    args["repo_name"], 
                    args["path"]
                )
            elif name == "create_file":
                return await self.github_service.create_file(
                    user_id,
                    args["repo_name"],
                    args["path"],
                    args["content"],
                    args.get("message", f"Add {args['path']}")
                )
            else:
                return {"error": f"Unknown tool: {name}"}
        except ValueError as e:
            # Handle missing integration errors
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}

