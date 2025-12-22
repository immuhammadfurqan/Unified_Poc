from typing import List
import logging
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    PROJECT_NAME: str = "Unified POC Backend"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "changethis"  # Change in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./sql_app.db"

    # Frontend URL for OAuth redirects
    FRONTEND_URL: str = "http://localhost:8000"

    # AI Provider
    OPENAI_API_KEY: str = ""

    # Integrations
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    
    FIGMA_CLIENT_ID: str = ""
    FIGMA_CLIENT_SECRET: str = ""
    
    TRELLO_API_KEY: str = ""
    TRELLO_API_SECRET: str = ""

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000", "http://localhost:8000"]

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()

# Log configuration on startup
logger.info("=" * 50)
logger.info("Configuration loaded:")
logger.info(f"GITHUB_CLIENT_ID: {settings.GITHUB_CLIENT_ID[:10] + '...' if settings.GITHUB_CLIENT_ID else 'NOT SET'}")
logger.info(f"GITHUB_CLIENT_SECRET: {'SET' if settings.GITHUB_CLIENT_SECRET else 'NOT SET'}")
logger.info(f"OPENAI_API_KEY: {'SET' if settings.OPENAI_API_KEY else 'NOT SET'}")
logger.info(f"FRONTEND_URL: {settings.FRONTEND_URL}")
logger.info("=" * 50)

