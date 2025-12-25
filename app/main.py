import uvicorn
from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import engine
from app.db.base import Base

# Import Feature Routers
from app.users.router import router as users_router
from app.integrations.router import router as integrations_router
from app.github_integration.router import router as github_router
from app.trello_integration.router import router as trello_router
from app.figma_integration.router import router as figma_router
from app.agent.router import router as agent_router

app = FastAPI(title=settings.PROJECT_NAME)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all for local dev ease, or keep specific list
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Construct API Router
api_router = APIRouter()
api_router.include_router(users_router, prefix="/auth", tags=["Auth"])
api_router.include_router(
    integrations_router, prefix="/integrations", tags=["Integrations"]
)
api_router.include_router(github_router, prefix="/github", tags=["GitHub"])
api_router.include_router(trello_router, prefix="/trello", tags=["Trello"])
api_router.include_router(figma_router, prefix="/figma", tags=["Figma"])
api_router.include_router(agent_router, prefix="/agent", tags=["Agent"])

app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount frontend
app.mount("/ui", StaticFiles(directory="frontend", html=True), name="static")


@app.get("/")
async def root():
    return {"message": "Go to /ui to view the dashboard"}


if __name__ == "__main__":
    import sys
    # Use reload only if --reload flag is passed or running interactively
    use_reload = "--reload" in sys.argv or sys.stdin.isatty()
    
    uvicorn.run(
        "app.main:app", 
        host="127.0.0.1", 
        port=8000, 
        reload=use_reload, 
        reload_dirs=["app", "frontend"] if use_reload else None,
        reload_excludes=["sandbox_data", "venv", "*.pyc", "__pycache__"] if use_reload else None
    )
