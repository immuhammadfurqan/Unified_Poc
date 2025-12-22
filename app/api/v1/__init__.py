from fastapi import APIRouter
from app.api.v1 import auth, oauth, integrations

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(oauth.router, prefix="/oauth", tags=["oauth"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
