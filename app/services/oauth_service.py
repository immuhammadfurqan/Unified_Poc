from datetime import datetime
from app.repositories.integration_repository import IntegrationRepository

class OAuthService:
    def __init__(self, integration_repo: IntegrationRepository):
        self.integration_repo = integration_repo

    async def save_token(
        self, user_id: int, provider: str, access_token: str, refresh_token: str = None, expires_at: datetime = None
    ):
        return await self.integration_repo.create_or_update(
            user_id, provider, access_token, refresh_token, expires_at
        )

    async def get_token(self, user_id: int, provider: str) -> str:
        integration = await self.integration_repo.get_by_user_and_provider(user_id, provider)
        if not integration:
            raise ValueError(f"No connection found for {provider}")
        return integration.access_token

