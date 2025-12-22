from typing import Any, Dict, List
from app.clients.github_client import GitHubClient
from app.services.oauth_service import OAuthService

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

