from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.integrations.repository import IntegrationRepository
from app.integrations.service import OAuthService
from app.trello_integration.service import TrelloService
from app.trello_integration.client import TrelloClient

def get_oauth_service(db: AsyncSession = Depends(get_db)) -> OAuthService:
    return OAuthService(IntegrationRepository(db))

def get_trello_service(oauth_service: OAuthService = Depends(get_oauth_service)) -> TrelloService:
    return TrelloService(oauth_service, TrelloClient())

