from datetime import datetime
from typing import Dict, Any, Optional
from app.integrations.repository import IntegrationRepository
from app.integrations.models import Integration


class OAuthService:
    def __init__(self, integration_repo: IntegrationRepository):
        self.integration_repo = integration_repo

    async def save_token(
        self,
        user_id: int,
        provider: str,
        access_token: str,
        refresh_token: str = None,
        expires_at: datetime = None,
        provider_metadata: Dict[str, Any] = None
    ) -> Integration:
        return await self.integration_repo.create_or_update(
            user_id, provider, access_token, refresh_token, expires_at, provider_metadata
        )

    async def get_token(self, user_id: int, provider: str) -> str:
        integration = await self.integration_repo.get_by_user_and_provider(user_id, provider)
        if not integration:
            raise ValueError(f"No connection found for {provider}")
        return integration.access_token

    async def get_integration(self, user_id: int, provider: str) -> Optional[Integration]:
        """Get the full integration object including metadata."""
        return await self.integration_repo.get_by_user_and_provider(user_id, provider)

    async def delete_integration(self, user_id: int, provider: str) -> bool:
        """Delete an integration. Returns True if deleted, False if not found."""
        return await self.integration_repo.delete_by_user_and_provider(user_id, provider)

