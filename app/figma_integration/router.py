from typing import Annotated
from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.users.models import User
from app.figma_integration.service import FigmaService
from app.figma_integration.dependencies import get_figma_service

router = APIRouter()

# --- Endpoints ---

@router.get("/analyze/{file_key}")
async def analyze_figma_design(
    file_key: str,
    user: User = Depends(get_current_user),
    service: FigmaService = Depends(get_figma_service)
):
    return await service.analyze_design(user.id, file_key)
