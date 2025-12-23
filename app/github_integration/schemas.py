from pydantic import BaseModel

# --- OAuth & Status Models ---

class GitHubConnectResponse(BaseModel):
    authorization_url: str

class GitHubStatusResponse(BaseModel):
    connected: bool
    username: str | None = None
    error: str | None = None

class GitHubDisconnectResponse(BaseModel):
    message: str

class GitHubCallbackRequest(BaseModel):
    code: str
    state: str

# --- Resource Models ---

class RepoCreate(BaseModel):
    name: str
    private: bool = False

