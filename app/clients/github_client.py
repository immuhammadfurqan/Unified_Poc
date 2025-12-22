import httpx
from typing import Dict, Any, List

class GitHubClient:
    BASE_URL = "https://api.github.com"

    async def create_repo(self, token: str, name: str, private: bool = False) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "name": name,
            "private": private
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.BASE_URL}/user/repos", json=data, headers=headers)
            response.raise_for_status()
            return response.json()

    async def list_repos(self, token: str) -> List[Dict[str, Any]]:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}/user/repos", headers=headers)
            response.raise_for_status()
            return response.json()

