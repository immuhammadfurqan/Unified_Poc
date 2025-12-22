from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.repositories.integration_repository import IntegrationRepository
from app.services.oauth_service import OAuthService
from app.services.github_service import GitHubService
from app.services.figma_service import FigmaService
from app.services.trello_service import TrelloService
from app.clients.github_client import GitHubClient
from app.clients.figma_client import FigmaClient
from app.clients.trello_client import TrelloClient
from pydantic import BaseModel

router = APIRouter()

# DTOs
class RepoCreate(BaseModel):
    name: str
    private: bool = False

class BoardCreate(BaseModel):
    name: str

class CardCreate(BaseModel):
    list_id: str
    name: str
    desc: str = ""

# Dependencies
def get_oauth_service(db: AsyncSession = Depends(get_db)) -> OAuthService:
    return OAuthService(IntegrationRepository(db))

def get_github_service(oauth_service: OAuthService = Depends(get_oauth_service)) -> GitHubService:
    return GitHubService(oauth_service, GitHubClient())

def get_figma_service(oauth_service: OAuthService = Depends(get_oauth_service)) -> FigmaService:
    return FigmaService(oauth_service, FigmaClient())

def get_trello_service(oauth_service: OAuthService = Depends(get_oauth_service)) -> TrelloService:
    return TrelloService(oauth_service, TrelloClient())

# GitHub Endpoints
@router.post("/github/repos")
async def create_github_repo(
    repo: RepoCreate,
    user: User = Depends(get_current_user),
    service: GitHubService = Depends(get_github_service)
):
    return await service.create_repo(user.id, repo.name, repo.private)

@router.get("/github/repos")
async def list_github_repos(
    user: User = Depends(get_current_user),
    service: GitHubService = Depends(get_github_service)
):
    return await service.list_repos(user.id)

# Figma Endpoints
@router.get("/figma/analyze/{file_key}")
async def analyze_figma_design(
    file_key: str,
    user: User = Depends(get_current_user),
    service: FigmaService = Depends(get_figma_service)
):
    return await service.analyze_design(user.id, file_key)

# Trello Endpoints
@router.post("/trello/boards")
async def create_trello_board(
    board: BoardCreate,
    user: User = Depends(get_current_user),
    service: TrelloService = Depends(get_trello_service)
):
    return await service.create_board(user.id, board.name)

@router.post("/trello/cards")
async def create_trello_card(
    card: CardCreate,
    user: User = Depends(get_current_user),
    service: TrelloService = Depends(get_trello_service)
):
    return await service.create_card(user.id, card.list_id, card.name, card.desc)

@router.get("/trello/boards")
async def list_trello_boards(
    user: User = Depends(get_current_user),
    service: TrelloService = Depends(get_trello_service)
):
    return await service.list_boards(user.id)

@router.get("/trello/boards/{board_id}/lists")
async def list_trello_lists(
    board_id: str,
    user: User = Depends(get_current_user),
    service: TrelloService = Depends(get_trello_service)
):
    return await service.get_lists(user.id, board_id)

