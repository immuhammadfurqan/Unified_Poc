from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import get_current_user
from app.users.models import User
from app.integrations.repository import IntegrationRepository
from app.integrations.service import OAuthService
from app.figma_integration.service import FigmaService
from app.figma_integration.client import FigmaClient

router = APIRouter()

# --- Dependencies ---

def get_oauth_service(db: AsyncSession = Depends(get_db)) -> OAuthService:
    return OAuthService(IntegrationRepository(db))

def get_figma_service(oauth_service: OAuthService = Depends(get_oauth_service)) -> FigmaService:
    return FigmaService(oauth_service, FigmaClient())

# --- Endpoints ---

@router.get("/analyze/{file_key}")
async def analyze_figma_design(
    file_key: str,
    user: User = Depends(get_current_user),
    service: FigmaService = Depends(get_figma_service)
):
    return await service.analyze_design(user.id, file_key)

