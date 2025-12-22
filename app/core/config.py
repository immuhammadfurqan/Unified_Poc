from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Unified POC Backend"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "changethis"  # Change in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./sql_app.db"

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

