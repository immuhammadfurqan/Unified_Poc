from typing import Any, Dict, List
from app.trello_integration.client import TrelloClient
from app.integrations.service import OAuthService

class TrelloService:
    def __init__(self, oauth_service: OAuthService, client: TrelloClient):
        self.oauth_service = oauth_service
        self.client = client

    async def create_board(self, user_id: int, name: str) -> Dict[str, Any]:
        token = await self.oauth_service.get_token(user_id, "trello")
        return await self.client.create_board(token, name)

    async def create_card(self, user_id: int, list_id: str, name: str, desc: str) -> Dict[str, Any]:
        token = await self.oauth_service.get_token(user_id, "trello")
        return await self.client.create_card(token, list_id, name, desc)

    async def list_boards(self, user_id: int) -> List[Dict[str, Any]]:
        token = await self.oauth_service.get_token(user_id, "trello")
        return await self.client.list_boards(token)

    async def get_lists(self, user_id: int, board_id: str) -> List[Dict[str, Any]]:
        token = await self.oauth_service.get_token(user_id, "trello")
        return await self.client.get_lists_on_board(token, board_id)

