from typing import Optional
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
        self, user_id: int, provider: str, access_token: str, refresh_token: str = None, expires_at: datetime = None
    ) -> Integration:
        integration = await self.get_by_user_and_provider(user_id, provider)
        if integration:
            integration.access_token = access_token
            integration.refresh_token = refresh_token
            integration.expires_at = expires_at
        else:
            integration = Integration(
                user_id=user_id,
                provider=provider,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at
            )
            self.db.add(integration)
        
        await self.db.commit()
        await self.db.refresh(integration)
        return integration

