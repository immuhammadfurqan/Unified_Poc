from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.integrations.repository import IntegrationRepository
from app.integrations.service import OAuthService
from app.figma_integration.service import FigmaService
from app.figma_integration.client import FigmaClient

def get_oauth_service(db: AsyncSession = Depends(get_db)) -> OAuthService:
    return OAuthService(IntegrationRepository(db))

def get_figma_service(oauth_service: OAuthService = Depends(get_oauth_service)) -> FigmaService:
    return FigmaService(oauth_service, FigmaClient())

