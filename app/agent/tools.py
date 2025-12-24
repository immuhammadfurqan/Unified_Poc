"""
Agent Tool Definitions

OpenAI function calling tool definitions.
Each tool is defined as a separate constant for clarity and maintainability.
"""

from typing import List, Dict, Any
from app.agent.constants import SUPPORTED_IMAGES


def _create_tool(name: str, description: str, properties: Dict, required: List[str] = None) -> Dict:
    """Factory function to create a tool definition with consistent structure."""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required or [],
            },
        },
    }


# --- GitHub Tools ---

CREATE_REPO_TOOL = _create_tool(
    name="create_repo",
    description="Create a new GitHub repository for the user",
    properties={
        "name": {"type": "string", "description": "The name of the repository to create"},
        "private": {"type": "boolean", "description": "Whether the repository should be private. Defaults to false (public)."},
    },
    required=["name"],
)

LIST_REPOS_TOOL = _create_tool(
    name="list_repos",
    description="List all GitHub repositories for the user",
    properties={},
)

CREATE_ISSUE_TOOL = _create_tool(
    name="create_issue",
    description="Create a new issue in a GitHub repository",
    properties={
        "repo_name": {"type": "string", "description": "The name of the repository (e.g., 'my-repo' or 'owner/my-repo')"},
        "title": {"type": "string", "description": "The title of the issue"},
        "body": {"type": "string", "description": "The body/description of the issue"},
    },
    required=["repo_name", "title", "body"],
)

LIST_ISSUES_TOOL = _create_tool(
    name="list_issues",
    description="List all issues in a GitHub repository",
    properties={
        "repo_name": {"type": "string", "description": "The name of the repository"},
    },
    required=["repo_name"],
)

GET_FILE_CONTENT_TOOL = _create_tool(
    name="get_file_content",
    description="Get the content of a file from a GitHub repository",
    properties={
        "repo_name": {"type": "string", "description": "The name of the repository"},
        "path": {"type": "string", "description": "The file path within the repository (e.g., 'README.md' or 'src/main.py')"},
    },
    required=["repo_name", "path"],
)

CREATE_FILE_TOOL = _create_tool(
    name="create_file",
    description="Create or update a file in a GitHub repository",
    properties={
        "repo_name": {"type": "string", "description": "The name of the repository"},
        "path": {"type": "string", "description": "The file path within the repository (e.g., 'README.md' or '.gitignore')"},
        "content": {"type": "string", "description": "The content of the file to create"},
        "message": {"type": "string", "description": "The commit message for this file creation"},
    },
    required=["repo_name", "path", "content", "message"],
)

# --- Sandbox Tools ---

SETUP_DEV_ENV_TOOL = _create_tool(
    name="setup_dev_environment",
    description="Setup a new development environment (sandbox) for running code. The sandbox has resource limits and will auto-cleanup after 30 minutes.",
    properties={
        "image": {
            "type": "string",
            "description": "The image to use (e.g., 'node:18' or 'python:3.11')",
            "enum": SUPPORTED_IMAGES,
        },
    },
    required=["image"],
)

RUN_COMMAND_TOOL = _create_tool(
    name="run_terminal_command",
    description="Run a shell command in the sandbox environment",
    properties={
        "container_id": {"type": "string", "description": "The ID of the sandbox container"},
        "command": {"type": "string", "description": "The shell command to execute"},
        "background": {"type": "boolean", "description": "Whether to run in background (for servers). Defaults to false."},
    },
    required=["container_id", "command"],
)

WRITE_FILE_TOOL = _create_tool(
    name="write_sandbox_file",
    description="Write a file to the sandbox environment",
    properties={
        "container_id": {"type": "string", "description": "The ID of the sandbox container"},
        "path": {"type": "string", "description": "The file path relative to /app"},
        "content": {"type": "string", "description": "The content of the file"},
    },
    required=["container_id", "path", "content"],
)

READ_FILE_TOOL = _create_tool(
    name="read_sandbox_file",
    description="Read a file from the sandbox environment",
    properties={
        "container_id": {"type": "string", "description": "The ID of the sandbox container"},
        "path": {"type": "string", "description": "The file path relative to /app"},
    },
    required=["container_id", "path"],
)

LIST_FILES_TOOL = _create_tool(
    name="list_sandbox_files",
    description="List files in the sandbox environment",
    properties={
        "container_id": {"type": "string", "description": "The ID of the sandbox container"},
        "path": {"type": "string", "description": "The directory path to list (defaults to /app)"},
    },
    required=["container_id"],
)

DESTROY_SANDBOX_TOOL = _create_tool(
    name="destroy_sandbox",
    description="Destroy a sandbox container and free resources. Call this after the task is complete to clean up.",
    properties={
        "container_id": {"type": "string", "description": "The ID of the sandbox container to destroy"},
    },
    required=["container_id"],
)

PUSH_TO_GITHUB_TOOL = _create_tool(
    name="push_sandbox_to_github",
    description="Push the current sandbox code to a GitHub repository. Creates the repo if it doesn't exist.",
    properties={
        "container_id": {"type": "string", "description": "The ID of the sandbox container"},
        "repo_name": {"type": "string", "description": "The name for the GitHub repository"},
        "commit_message": {"type": "string", "description": "The commit message for this push"},
        "private": {"type": "boolean", "description": "Whether the repository should be private. Defaults to false."},
    },
    required=["container_id", "repo_name"],
)


def get_all_tools() -> List[Dict[str, Any]]:
    """Returns all available tools as a list for OpenAI API."""
    return [
        # GitHub Tools
        CREATE_REPO_TOOL,
        LIST_REPOS_TOOL,
        CREATE_ISSUE_TOOL,
        LIST_ISSUES_TOOL,
        GET_FILE_CONTENT_TOOL,
        CREATE_FILE_TOOL,
        # Sandbox Tools
        SETUP_DEV_ENV_TOOL,
        RUN_COMMAND_TOOL,
        WRITE_FILE_TOOL,
        READ_FILE_TOOL,
        LIST_FILES_TOOL,
        DESTROY_SANDBOX_TOOL,
        PUSH_TO_GITHUB_TOOL,
    ]

