"""
GitHub Integration Router

Handles:
1. OAuth flow (connect, callback, status, disconnect)
2. Resource management (repos, issues, etc.)
"""

from typing import Annotated
from urllib.parse import urlencode
import secrets
import logging
import httpx

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import get_current_user
from app.users.models import User
from app.integrations.repository import IntegrationRepository
from app.integrations.service import OAuthService
from app.github_integration.service import GitHubService
from app.core.config import settings
from app.github_integration.schemas import (
    GitHubConnectResponse, GitHubStatusResponse, GitHubDisconnectResponse,
    GitHubCallbackRequest, RepoCreate
)
from app.github_integration.dependencies import get_oauth_service, get_github_service

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory state storage (use Redis in production)
_oauth_states: dict[str, int] = {}

# --- OAuth Endpoints ---

@router.get("/connect", response_model=GitHubConnectResponse)
async def connect_github(
    user: Annotated[User, Depends(get_current_user)],
) -> GitHubConnectResponse:
    """Initiates GitHub OAuth flow."""
    logger.info(f"GitHub OAuth connect called for user {user.id}")
    
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GitHub OAuth not configured. Set GITHUB_CLIENT_ID in environment."
        )
    
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = user.id
    
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": f"{settings.FRONTEND_URL}/ui?callback=github",
        "scope": "repo user",
        "state": state,
    }
    
    authorization_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
    return GitHubConnectResponse(authorization_url=authorization_url)

@router.post("/callback")
async def github_callback(
    request: GitHubCallbackRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> dict:
    """Exchanges authorization code for access token."""
    code = request.code
    state = request.state
    
    stored_user_id = _oauth_states.pop(state, None)
    if stored_user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state parameter"
        )
    
    if not settings.GITHUB_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GitHub OAuth not configured."
        )
    
    oauth_service = OAuthService(IntegrationRepository(db))
    
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": f"{settings.FRONTEND_URL}/ui?callback=github"
            }
        )
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange code")
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(status_code=400, detail=token_data.get("error_description", "No token"))
        
        # Fetch user info
        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3+json"
            }
        )
        
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to verify GitHub token")
        
        github_user = user_response.json()
        github_username = github_user.get("login")
        
        await oauth_service.save_token(
            user_id=user.id,
            provider="github",
            access_token=access_token,
            provider_metadata={"github_username": github_username}
        )
    
    return {"message": "GitHub connected successfully", "username": github_username}

@router.get("/status", response_model=GitHubStatusResponse)
async def github_status(
    user: Annotated[User, Depends(get_current_user)],
    oauth_service: Annotated[OAuthService, Depends(get_oauth_service)]
) -> GitHubStatusResponse:
    """Check connection status."""
    integration = await oauth_service.get_integration(user.id, "github")
    
    if not integration:
        return GitHubStatusResponse(connected=False)
    
    # Optional: Verify token validity here if needed
    
    username = None
    if integration.provider_metadata:
        username = integration.provider_metadata.get("github_username")
    
    return GitHubStatusResponse(connected=True, username=username)

@router.delete("/disconnect", response_model=GitHubDisconnectResponse)
async def disconnect_github(
    user: Annotated[User, Depends(get_current_user)],
    oauth_service: Annotated[OAuthService, Depends(get_oauth_service)]
) -> GitHubDisconnectResponse:
    deleted = await oauth_service.delete_integration(user.id, "github")
    if not deleted:
        raise HTTPException(status_code=404, detail="GitHub integration not found")
    return GitHubDisconnectResponse(message="GitHub disconnected successfully")

# --- Resource Endpoints ---

@router.post("/repos")
async def create_github_repo(
    repo: RepoCreate,
    user: User = Depends(get_current_user),
    service: GitHubService = Depends(get_github_service)
):
    return await service.create_repo(user.id, repo.name, repo.private)

@router.get("/repos")
async def list_github_repos(
    user: User = Depends(get_current_user),
    service: GitHubService = Depends(get_github_service)
):
    return await service.list_repos(user.id)
