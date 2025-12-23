from typing import Annotated, List, Dict
from fastapi import APIRouter, Depends, HTTPException
from app.core.deps import get_current_user
from app.users.models import User
from app.agent.service import AgentService
from app.github_integration.service import GitHubService
from app.github_integration.router import get_github_service
from pydantic import BaseModel

router = APIRouter()

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]

def get_agent_service(github_service: GitHubService = Depends(get_github_service)) -> AgentService:
    return AgentService(github_service)

@router.post("/chat")
async def chat(
    request: ChatRequest,
    user: User = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service)
):
    try:
        response = await service.chat(user.id, request.messages)
        return {"response": response}
    except Exception as e:
        # In a real app, log the error
        print(f"Agent Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

