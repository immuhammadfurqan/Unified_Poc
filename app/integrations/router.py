from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.deps import get_current_user
from app.users.models import User
from app.integrations.repository import IntegrationRepository
from app.integrations.service import OAuthService
from app.core.config import settings
import httpx
from pydantic import BaseModel

router = APIRouter()

class TokenInput(BaseModel):
    provider: str
    token: str

@router.post("/token")
async def save_token_manually(
    token_in: TokenInput,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Manually save a token for a provider. Useful for Trello or testing.
    """
    integration_repo = IntegrationRepository(db)
    oauth_service = OAuthService(integration_repo)
    
    await oauth_service.save_token(user.id, token_in.provider, token_in.token)
    return {"message": f"Successfully connected to {token_in.provider}"}

@router.get("/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Generic callback. In reality, each provider needs specific handling for token exchange.
    We will implement basic exchange for GitHub and Figma here.
    """
    integration_repo = IntegrationRepository(db)
    oauth_service = OAuthService(integration_repo)
    
    token = ""
    
    async with httpx.AsyncClient() as client:
        if provider == "github":
            resp = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code
                }
            )
            data = resp.json()
            token = data.get("access_token")
            
        elif provider == "figma":
            resp = await client.post(
                "https://www.figma.com/api/oauth/token",
                data={
                    "client_id": settings.FIGMA_CLIENT_ID,
                    "client_secret": settings.FIGMA_CLIENT_SECRET,
                    "redirect_uri": "http://localhost:8000/api/v1/oauth/figma/callback", # Adjust as needed
                    "code": code,
                    "grant_type": "authorization_code"
                }
            )
            data = resp.json()
            token = data.get("access_token")

        # Trello auth is tricky (client side token often), skipping backend exchange for simplicity or assuming similar flow.
    
    if not token:
        raise HTTPException(status_code=400, detail="Failed to retrieve token")
        
    await oauth_service.save_token(user.id, provider, token)
    return {"message": f"Successfully connected to {provider}"}

