from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.integrations.repository import IntegrationRepository
from app.integrations.service import OAuthService
from app.github_integration.service import GitHubService
from app.github_integration.client import GitHubClient

def get_oauth_service(db: AsyncSession = Depends(get_db)) -> OAuthService:
    return OAuthService(IntegrationRepository(db))

def get_github_service(oauth_service: OAuthService = Depends(get_oauth_service)) -> GitHubService:
    return GitHubService(oauth_service, GitHubClient())

