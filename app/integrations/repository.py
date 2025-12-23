from typing import Optional
from sqlalchemy.future import select
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.integrations.models import Integration
from datetime import datetime
from typing import Dict, Any

class IntegrationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_and_provider(self, user_id: int, provider: str) -> Optional[Integration]:
        result = await self.db.execute(
            select(Integration).filter(
                Integration.user_id == user_id,
                Integration.provider == provider
            )
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
            if refresh_token:
                integration.refresh_token = refresh_token
            if expires_at:
                integration.expires_at = expires_at
            if provider_metadata:
                # Merge existing metadata with new
                existing_meta = integration.provider_metadata or {}
                existing_meta.update(provider_metadata)
                integration.provider_metadata = existing_meta
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
        result = await self.db.execute(
            delete(Integration).filter(
                Integration.user_id == user_id,
                Integration.provider == provider
            )
        )
        await self.db.commit()
        return result.rowcount > 0

