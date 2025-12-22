"""
GitHub OAuth Router

Handles GitHub OAuth flow with proper state validation for CSRF protection.
Endpoints:
- GET /connect: Returns GitHub authorization URL
- GET /callback: Handles OAuth callback, exchanges code for token
- GET /status: Returns connection status and username
- DELETE /disconnect: Removes GitHub integration
"""

from typing import Annotated
from urllib.parse import urlencode
import secrets
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import httpx

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.repositories.integration_repository import IntegrationRepository
from app.services.oauth_service import OAuthService
from app.core.config import settings

logger = logging.getLogger(__name__)


router = APIRouter()

# In-memory state storage (use Redis in production for distributed systems)
_oauth_states: dict[str, int] = {}


class GitHubConnectResponse(BaseModel):
    authorization_url: str


class GitHubStatusResponse(BaseModel):
    connected: bool
    username: str | None = None
    error: str | None = None


class GitHubDisconnectResponse(BaseModel):
    message: str


def _get_oauth_service(db: AsyncSession = Depends(get_db)) -> OAuthService:
    return OAuthService(IntegrationRepository(db))


@router.get("/connect", response_model=GitHubConnectResponse)
async def connect_github(
    user: Annotated[User, Depends(get_current_user)],
) -> GitHubConnectResponse:
    """
    Initiates GitHub OAuth flow.
    Returns the GitHub authorization URL for the user to redirect to.
    """
    logger.info(f"GitHub OAuth connect called for user {user.id}")
    logger.info(f"GITHUB_CLIENT_ID value: '{settings.GITHUB_CLIENT_ID}'")
    logger.info(f"GITHUB_CLIENT_ID type: {type(settings.GITHUB_CLIENT_ID)}")
    logger.info(f"GITHUB_CLIENT_ID bool check: {bool(settings.GITHUB_CLIENT_ID)}")
    
    if not settings.GITHUB_CLIENT_ID:
        logger.error("GITHUB_CLIENT_ID is empty or None!")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GitHub OAuth not configured. Set GITHUB_CLIENT_ID in environment."
        )
    
    # Generate state token for CSRF protection
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


class GitHubCallbackRequest(BaseModel):
    code: str
    state: str


@router.post("/callback")
async def github_callback(
    request: GitHubCallbackRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> dict:
    """
    GitHub OAuth callback endpoint (POST).
    Exchanges the authorization code for an access token and stores it.
    Authenticated endpoint - uses Bearer token from frontend.
    """
    code = request.code
    state = request.state
    
    # Verify state matches the one stored for this user
    stored_user_id = _oauth_states.pop(state, None)
    if stored_user_id != user.id:
        # If state not found or user ID mismatch (though state is random, so mismatch implies interception)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state parameter"
        )
    
    if not settings.GITHUB_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GitHub OAuth not configured. Set GITHUB_CLIENT_SECRET in environment."
        )
    
    oauth_service = OAuthService(IntegrationRepository(db))
    
    async with httpx.AsyncClient() as client:
        # Exchange code for access token
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange code for token"
            )
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            error = token_data.get("error_description", "No access token received")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
        
        # Fetch GitHub user info to verify token and get username
        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3+json"
            }
        )
        
        if user_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to verify GitHub token"
            )
        
        github_user = user_response.json()
        github_username = github_user.get("login")
        
        # Save token with metadata
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
    oauth_service: Annotated[OAuthService, Depends(_get_oauth_service)]
) -> GitHubStatusResponse:
    """
    Check if user has connected their GitHub account.
    Optionally verifies the token is still valid.
    """
    integration = await oauth_service.get_integration(user.id, "github")
    
    if not integration:
        return GitHubStatusResponse(connected=False)
    
    # Verify token is still valid
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {integration.access_token}",
                "Accept": "application/vnd.github.v3+json"
            }
        )
        
        if response.status_code == 401:
            # Token expired or revoked - clean up
            await oauth_service.delete_integration(user.id, "github")
            return GitHubStatusResponse(connected=False, error="Token expired or revoked")
    
    username = None
    if integration.provider_metadata:
        username = integration.provider_metadata.get("github_username")
    
    return GitHubStatusResponse(connected=True, username=username)


@router.delete("/disconnect", response_model=GitHubDisconnectResponse)
async def disconnect_github(
    user: Annotated[User, Depends(get_current_user)],
    oauth_service: Annotated[OAuthService, Depends(_get_oauth_service)]
) -> GitHubDisconnectResponse:
    """
    Disconnect GitHub integration for the current user.
    """
    deleted = await oauth_service.delete_integration(user.id, "github")
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GitHub integration not found"
        )
    
    return GitHubDisconnectResponse(message="GitHub disconnected successfully")

