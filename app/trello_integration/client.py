import httpx
from typing import Dict, Any, List
from app.core.config import settings

class TrelloClient:
    BASE_URL = "https://api.trello.com/1"
    
    # Note: Trello OAuth1 is complex, often Trello uses API Key + Token.
    # We will assume the 'token' passed here is the user's OAuth access token.
    # Trello often requires Key + Token in query params.

    def _get_auth_params(self, token: str) -> Dict[str, str]:
        return {
            "key": settings.TRELLO_API_KEY,
            "token": token
        }

    async def create_board(self, token: str, name: str) -> Dict[str, Any]:
        params = self._get_auth_params(token)
        params["name"] = name
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.BASE_URL}/boards", params=params)
            response.raise_for_status()
            return response.json()

    async def create_card(self, token: str, list_id: str, name: str, desc: str = "") -> Dict[str, Any]:
        params = self._get_auth_params(token)
        params["idList"] = list_id
        params["name"] = name
        params["desc"] = desc
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.BASE_URL}/cards", params=params)
            response.raise_for_status()
            return response.json()
            
    async def list_boards(self, token: str) -> List[Dict[str, Any]]:
        params = self._get_auth_params(token)
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}/members/me/boards", params=params)
            response.raise_for_status()
            return response.json()

    async def get_lists_on_board(self, token: str, board_id: str) -> List[Dict[str, Any]]:
        params = self._get_auth_params(token)
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}/boards/{board_id}/lists", params=params)
            response.raise_for_status()
            return response.json()

