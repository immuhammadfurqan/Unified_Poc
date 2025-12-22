from typing import Optional, Dict, Any
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.integration import Integration
from datetime import datetime


class IntegrationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_and_provider(self, user_id: int, provider: str) -> Optional[Integration]:
        result = await self.db.execute(
            select(Integration).filter(Integration.user_id == user_id, Integration.provider == provider)
        )
        return result.scalars().first()

    async def create_or_update(
        self,
        user_id: int,
        provider: str,
        access_token: str,
        refresh_token: str = None,
        expires_at: datetime = None,
        provider_metadata: Dict[str, Any] = None
    ) -> Integration:
        integration = await self.get_by_user_and_provider(user_id, provider)
        if integration:
            integration.access_token = access_token
            integration.refresh_token = refresh_token
            integration.expires_at = expires_at
            if provider_metadata is not None:
                integration.provider_metadata = provider_metadata
        else:
            integration = Integration(
                user_id=user_id,
                provider=provider,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
                provider_metadata=provider_metadata
            )
            self.db.add(integration)
        
        await self.db.commit()
        await self.db.refresh(integration)
        return integration

    async def delete_by_user_and_provider(self, user_id: int, provider: str) -> bool:
        """Delete an integration for a user and provider. Returns True if deleted, False if not found."""
        integration = await self.get_by_user_and_provider(user_id, provider)
        if integration:
            await self.db.delete(integration)
            await self.db.commit()
            return True
        return False

