import httpx
from typing import Dict, Any, List

class GitHubClient:
    BASE_URL = "https://api.github.com"

    async def get_user(self, token: str) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}/user", headers=headers)
            response.raise_for_status()
            return response.json()

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

    async def create_issue(self, token: str, owner: str, repo: str, title: str, body: str) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {"title": title, "body": body}
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.BASE_URL}/repos/{owner}/{repo}/issues", json=data, headers=headers)
            response.raise_for_status()
            return response.json()

    async def list_issues(self, token: str, owner: str, repo: str) -> List[Dict[str, Any]]:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}/repos/{owner}/{repo}/issues", headers=headers)
            response.raise_for_status()
            return response.json()

    async def get_file_content(self, token: str, owner: str, repo: str, path: str) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{path}", headers=headers)
            response.raise_for_status()
            return response.json()

    async def create_file(self, token: str, owner: str, repo: str, path: str, content: str, message: str) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # GitHub API expects content to be base64 encoded
        import base64
        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        
        data = {
            "message": message,
            "content": encoded_content
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.put(f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{path}", json=data, headers=headers)
            response.raise_for_status()
            return response.json()

