"""
Agent Tool Handlers

Implements the Strategy pattern for tool execution.
Each handler is a focused, single-responsibility function.
"""

from typing import Dict, Any
from app.agent.constants import (
    TOOL_CREATE_REPO, TOOL_LIST_REPOS, TOOL_CREATE_ISSUE, TOOL_LIST_ISSUES,
    TOOL_GET_FILE_CONTENT, TOOL_CREATE_FILE, TOOL_SETUP_DEV_ENV, TOOL_RUN_COMMAND,
    TOOL_WRITE_FILE, TOOL_READ_FILE, TOOL_LIST_FILES, TOOL_DESTROY_SANDBOX,
    TOOL_PUSH_TO_GITHUB, DEFAULT_WORKING_DIR, DEFAULT_COMMIT_MESSAGE,
)
from app.github_integration.client import GitHubClient


class GitHubToolHandler:
    """Handles all GitHub-related tool executions."""
    
    def __init__(self, github_service):
        self._github_service = github_service
    
    async def create_repo(self, user_id: int, args: Dict[str, Any]) -> Dict[str, Any]:
        return await self._github_service.create_repo(
            user_id, args["name"], args.get("private", False)
        )
    
    async def list_repos(self, user_id: int) -> list:
        repos = await self._github_service.list_repos(user_id)
        return [self._format_repo(repo) for repo in repos]
    
    async def create_issue(self, user_id: int, args: Dict[str, Any]) -> Dict[str, Any]:
        return await self._github_service.create_issue(
            user_id, args["repo_name"], args["title"], args["body"]
        )
    
    async def list_issues(self, user_id: int, args: Dict[str, Any]) -> list:
        issues = await self._github_service.list_issues(user_id, args["repo_name"])
        return [self._format_issue(issue) for issue in issues]
    
    async def get_file_content(self, user_id: int, args: Dict[str, Any]) -> Dict[str, Any]:
        return await self._github_service.get_file_content(
            user_id, args["repo_name"], args["path"]
        )
    
    async def create_file(self, user_id: int, args: Dict[str, Any]) -> Dict[str, Any]:
        return await self._github_service.create_file(
            user_id,
            args["repo_name"],
            args["path"],
            args["content"],
            args.get("message", f"Add {args['path']}"),
        )
    
    async def get_token(self, user_id: int) -> str:
        return await self._github_service.get_token(user_id)
    
    @staticmethod
    def _format_repo(repo: Dict) -> Dict[str, Any]:
        return {
            "name": repo.get("name"),
            "full_name": repo.get("full_name"),
            "private": repo.get("private"),
            "url": repo.get("html_url"),
        }
    
    @staticmethod
    def _format_issue(issue: Dict) -> Dict[str, Any]:
        return {
            "number": issue.get("number"),
            "title": issue.get("title"),
            "state": issue.get("state"),
            "url": issue.get("html_url"),
        }


class SandboxToolHandler:
    """Handles all sandbox-related tool executions."""
    
    def __init__(self, sandbox_service, github_handler: GitHubToolHandler):
        self._sandbox_service = sandbox_service
        self._github_handler = github_handler
        self._active_containers: Dict[int, str] = {}
    
    async def setup_dev_environment(self, user_id: int, args: Dict[str, Any]) -> Dict[str, Any]:
        result = self._sandbox_service.create_sandbox(user_id, args["image"])
        container_id = result["container_id"]
        
        self._active_containers[user_id] = container_id
        await self._setup_git_credentials_if_available(user_id, container_id)
        
        return result
    
    def run_command(self, args: Dict[str, Any]) -> Dict[str, Any]:
        return self._sandbox_service.execute_command(
            args["container_id"],
            args["command"],
            background=args.get("background", False),
        )
    
    def write_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        return self._sandbox_service.write_file(
            args["container_id"], args["path"], args["content"]
        )
    
    def read_file(self, args: Dict[str, Any]) -> str:
        return self._sandbox_service.read_file(args["container_id"], args["path"])
    
    def list_files(self, args: Dict[str, Any]) -> Dict[str, Any]:
        return self._sandbox_service.list_files(
            args["container_id"], args.get("path", DEFAULT_WORKING_DIR)
        )
    
    def destroy_sandbox(self, args: Dict[str, Any]) -> Dict[str, Any]:
        container_id = args["container_id"]
        result = self._sandbox_service.destroy_sandbox(container_id)
        self._remove_from_active_containers(container_id)
        return result
    
    async def push_to_github(self, user_id: int, args: Dict[str, Any]) -> Dict[str, Any]:
        container_id = args["container_id"]
        repo_name = args["repo_name"]
        commit_message = args.get("commit_message", DEFAULT_COMMIT_MESSAGE)
        private = args.get("private", False)
        
        try:
            username, token = await self._get_github_credentials(user_id)
            self._sandbox_service.setup_git_credentials(container_id, token, username)
            await self._create_repo_if_not_exists(user_id, repo_name, private)
            return self._execute_git_push(container_id, username, token, repo_name, commit_message)
        except Exception as e:
            return {"status": "error", "message": f"Failed to push to GitHub: {str(e)}"}
    
    async def _setup_git_credentials_if_available(self, user_id: int, container_id: str) -> None:
        try:
            token = await self._github_handler.get_token(user_id)
            self._sandbox_service.setup_git_credentials(container_id, token)
        except Exception:
            pass  # GitHub not connected, git push won't work but sandbox still usable
    
    async def _get_github_credentials(self, user_id: int) -> tuple:
        token = await self._github_handler.get_token(user_id)
        client = GitHubClient()
        user_info = await client.get_user(token)
        return user_info["login"], token
    
    async def _create_repo_if_not_exists(self, user_id: int, repo_name: str, private: bool) -> None:
        try:
            await self._github_handler.create_repo(user_id, {"name": repo_name, "private": private})
        except Exception:
            pass  # Repo might already exist
    
    def _execute_git_push(
        self, container_id: str, username: str, token: str, repo_name: str, commit_message: str
    ) -> Dict[str, Any]:
        remote_url = f"https://{username}:{token}@github.com/{username}/{repo_name}.git"
        commands = self._build_git_commands(commit_message, remote_url)
        
        for cmd in commands:
            result = self._sandbox_service.execute_command(container_id, cmd)
            if "push" in cmd and result["exit_code"] != 0:
                return self._build_push_error_response(username, repo_name, result["output"])
        
        return self._build_push_success_response(username, repo_name)
    
    @staticmethod
    def _build_git_commands(commit_message: str, remote_url: str) -> list:
        return [
            "git init",
            "git add -A",
            f'git commit -m "{commit_message}"',
            "git branch -M main",
            f"git remote remove origin 2>/dev/null; git remote add origin {remote_url}",
            "git push -u origin main --force",
        ]
    
    @staticmethod
    def _build_push_error_response(username: str, repo_name: str, output: str) -> Dict[str, Any]:
        return {
            "status": "error",
            "message": f"Git push failed: {output}",
            "repo_url": f"https://github.com/{username}/{repo_name}",
        }
    
    @staticmethod
    def _build_push_success_response(username: str, repo_name: str) -> Dict[str, Any]:
        return {
            "status": "success",
            "message": "Code pushed to GitHub successfully",
            "repo_url": f"https://github.com/{username}/{repo_name}",
            "repo_name": repo_name,
        }
    
    def _remove_from_active_containers(self, container_id: str) -> None:
        for uid, cid in list(self._active_containers.items()):
            if cid == container_id:
                del self._active_containers[uid]
                break


class ToolExecutor:
    """
    Orchestrates tool execution using the appropriate handler.
    Implements the Strategy pattern to dispatch tool calls.
    """
    
    def __init__(self, github_handler: GitHubToolHandler, sandbox_handler: SandboxToolHandler):
        self._github_handler = github_handler
        self._sandbox_handler = sandbox_handler
        self._tool_map = self._build_tool_map()
    
    def _build_tool_map(self) -> Dict[str, callable]:
        """Maps tool names to their handler methods."""
        return {
            # GitHub tools
            TOOL_CREATE_REPO: self._handle_create_repo,
            TOOL_LIST_REPOS: self._handle_list_repos,
            TOOL_CREATE_ISSUE: self._handle_create_issue,
            TOOL_LIST_ISSUES: self._handle_list_issues,
            TOOL_GET_FILE_CONTENT: self._handle_get_file_content,
            TOOL_CREATE_FILE: self._handle_create_file,
            # Sandbox tools
            TOOL_SETUP_DEV_ENV: self._handle_setup_dev_env,
            TOOL_RUN_COMMAND: self._handle_run_command,
            TOOL_WRITE_FILE: self._handle_write_file,
            TOOL_READ_FILE: self._handle_read_file,
            TOOL_LIST_FILES: self._handle_list_files,
            TOOL_DESTROY_SANDBOX: self._handle_destroy_sandbox,
            TOOL_PUSH_TO_GITHUB: self._handle_push_to_github,
        }
    
    async def execute(self, user_id: int, tool_name: str, args: Dict[str, Any]) -> Any:
        """Execute a tool by name with the given arguments."""
        try:
            handler = self._tool_map.get(tool_name)
            if not handler:
                return {"error": f"Unknown tool: {tool_name}"}
            return await handler(user_id, args)
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}
    
    # GitHub tool handlers
    async def _handle_create_repo(self, user_id: int, args: Dict) -> Any:
        return await self._github_handler.create_repo(user_id, args)
    
    async def _handle_list_repos(self, user_id: int, _args: Dict) -> Any:
        return await self._github_handler.list_repos(user_id)
    
    async def _handle_create_issue(self, user_id: int, args: Dict) -> Any:
        return await self._github_handler.create_issue(user_id, args)
    
    async def _handle_list_issues(self, user_id: int, args: Dict) -> Any:
        return await self._github_handler.list_issues(user_id, args)
    
    async def _handle_get_file_content(self, user_id: int, args: Dict) -> Any:
        return await self._github_handler.get_file_content(user_id, args)
    
    async def _handle_create_file(self, user_id: int, args: Dict) -> Any:
        return await self._github_handler.create_file(user_id, args)
    
    # Sandbox tool handlers
    async def _handle_setup_dev_env(self, user_id: int, args: Dict) -> Any:
        return await self._sandbox_handler.setup_dev_environment(user_id, args)
    
    async def _handle_run_command(self, _user_id: int, args: Dict) -> Any:
        return self._sandbox_handler.run_command(args)
    
    async def _handle_write_file(self, _user_id: int, args: Dict) -> Any:
        return self._sandbox_handler.write_file(args)
    
    async def _handle_read_file(self, _user_id: int, args: Dict) -> Any:
        return self._sandbox_handler.read_file(args)
    
    async def _handle_list_files(self, _user_id: int, args: Dict) -> Any:
        return self._sandbox_handler.list_files(args)
    
    async def _handle_destroy_sandbox(self, _user_id: int, args: Dict) -> Any:
        return self._sandbox_handler.destroy_sandbox(args)
    
    async def _handle_push_to_github(self, user_id: int, args: Dict) -> Any:
        return await self._sandbox_handler.push_to_github(user_id, args)

