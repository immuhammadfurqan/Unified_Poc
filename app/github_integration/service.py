from typing import Any, Dict, List
from app.github_integration.client import GitHubClient
from app.integrations.service import OAuthService

class GitHubService:
    def __init__(self, oauth_service: OAuthService, client: GitHubClient):
        self.oauth_service = oauth_service
        self.client = client

    async def create_repo(self, user_id: int, name: str, private: bool) -> Dict[str, Any]:
        token = await self.oauth_service.get_token(user_id, "github")
        return await self.client.create_repo(token, name, private)

    async def list_repos(self, user_id: int) -> List[Dict[str, Any]]:
        token = await self.oauth_service.get_token(user_id, "github")
        return await self.client.list_repos(token)

    async def create_issue(self, user_id: int, repo_name: str, title: str, body: str) -> Dict[str, Any]:
        token = await self.oauth_service.get_token(user_id, "github")
        owner, repo = await self._resolve_owner_repo(token, repo_name)
        return await self.client.create_issue(token, owner, repo, title, body)

    async def list_issues(self, user_id: int, repo_name: str) -> List[Dict[str, Any]]:
        token = await self.oauth_service.get_token(user_id, "github")
        owner, repo = await self._resolve_owner_repo(token, repo_name)
        return await self.client.list_issues(token, owner, repo)

    async def get_file_content(self, user_id: int, repo_name: str, path: str) -> Dict[str, Any]:
        token = await self.oauth_service.get_token(user_id, "github")
        owner, repo = await self._resolve_owner_repo(token, repo_name)
        return await self.client.get_file_content(token, owner, repo, path)

    async def get_token(self, user_id: int) -> str:
        """
        Retrieves the GitHub access token for the user.
        """
        return await self.oauth_service.get_token(user_id, "github")

    async def create_file(self, user_id: int, repo_name: str, path: str, content: str, message: str) -> Dict[str, Any]:
        token = await self.oauth_service.get_token(user_id, "github")
        owner, repo = await self._resolve_owner_repo(token, repo_name)
        return await self.client.create_file(token, owner, repo, path, content, message)

    async def _resolve_owner_repo(self, token: str, repo_name: str) -> tuple[str, str]:
        if "/" in repo_name:
            return repo_name.split("/", 1)
        
        # Fetch current user to get owner
        user = await self.client.get_user(token)
        return user["login"], repo_name
