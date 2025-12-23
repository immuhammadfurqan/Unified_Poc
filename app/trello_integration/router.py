from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.core.deps import get_current_user
from app.users.models import User
from app.integrations.repository import IntegrationRepository
from app.integrations.service import OAuthService
from app.trello_integration.service import TrelloService
from app.trello_integration.client import TrelloClient

router = APIRouter()

# --- DTOs ---

class BoardCreate(BaseModel):
    name: str

class CardCreate(BaseModel):
    list_id: str
    name: str
    desc: str = ""

# --- Dependencies ---

def get_oauth_service(db: AsyncSession = Depends(get_db)) -> OAuthService:
    return OAuthService(IntegrationRepository(db))

def get_trello_service(oauth_service: OAuthService = Depends(get_oauth_service)) -> TrelloService:
    return TrelloService(oauth_service, TrelloClient())

# --- Endpoints ---

@router.post("/boards")
async def create_trello_board(
    board: BoardCreate,
    user: User = Depends(get_current_user),
    service: TrelloService = Depends(get_trello_service)
):
    return await service.create_board(user.id, board.name)

@router.post("/cards")
async def create_trello_card(
    card: CardCreate,
    user: User = Depends(get_current_user),
    service: TrelloService = Depends(get_trello_service)
):
    return await service.create_card(user.id, card.list_id, card.name, card.desc)

@router.get("/boards")
async def list_trello_boards(
    user: User = Depends(get_current_user),
    service: TrelloService = Depends(get_trello_service)
):
    return await service.list_boards(user.id)

@router.get("/boards/{board_id}/lists")
async def list_trello_lists(
    board_id: str,
    user: User = Depends(get_current_user),
    service: TrelloService = Depends(get_trello_service)
):
    return await service.get_lists(user.id, board_id)

