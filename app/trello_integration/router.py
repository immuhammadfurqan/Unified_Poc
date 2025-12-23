from typing import Annotated
from fastapi import APIRouter, Depends
from app.core.deps import get_current_user
from app.users.models import User
from app.trello_integration.service import TrelloService
from app.trello_integration.schemas import BoardCreate, CardCreate
from app.trello_integration.dependencies import get_trello_service

router = APIRouter()

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
