"""
Agent Constants

Centralized constants for the agent module.
Eliminates magic strings and numbers throughout the codebase.
"""

# OpenAI Configuration
DEFAULT_MODEL = "gpt-4o"

# Container Configuration
DEFAULT_CONTAINER_PORT = "3000/tcp"
DEFAULT_WORKING_DIR = "/app"
SUPPORTED_IMAGES = ["node:18", "python:3.11"]

# Git Configuration
DEFAULT_GIT_EMAIL = "agent@example.com"
DEFAULT_GIT_USER = "AI Agent"
DEFAULT_COMMIT_MESSAGE = "Initial commit from AI sandbox"

# Tool Names - GitHub
TOOL_CREATE_REPO = "create_repo"
TOOL_LIST_REPOS = "list_repos"
TOOL_CREATE_ISSUE = "create_issue"
TOOL_LIST_ISSUES = "list_issues"
TOOL_GET_FILE_CONTENT = "get_file_content"
TOOL_CREATE_FILE = "create_file"

# Tool Names - Sandbox
TOOL_SETUP_DEV_ENV = "setup_dev_environment"
TOOL_RUN_COMMAND = "run_terminal_command"
TOOL_WRITE_FILE = "write_sandbox_file"
TOOL_READ_FILE = "read_sandbox_file"
TOOL_LIST_FILES = "list_sandbox_files"
TOOL_DESTROY_SANDBOX = "destroy_sandbox"
TOOL_PUSH_TO_GITHUB = "push_sandbox_to_github"

