from typing import Any, Dict
from app.clients.figma_client import FigmaClient
from app.services.oauth_service import OAuthService

class FigmaService:
    def __init__(self, oauth_service: OAuthService, client: FigmaClient):
        self.oauth_service = oauth_service
        self.client = client

    async def analyze_design(self, user_id: int, file_key: str) -> Dict[str, Any]:
        token = await self.oauth_service.get_token(user_id, "figma")
        file_data = await self.client.get_file(token, file_key)
        
        # Simple parsing logic: Extract document name and top-level frames
        document = file_data.get("document", {})
        name = file_data.get("name", "Unknown")
        children = document.get("children", [])
        
        frames = []
        for canvas in children:
            if "children" in canvas:
                for node in canvas["children"]:
                    if node.get("type") == "FRAME":
                        frames.append({
                            "id": node.get("id"),
                            "name": node.get("name"),
                            "type": "FRAME"
                        })
        
        return {
            "file_name": name,
            "frames": frames,
            "raw_data_summary": "Extracted top level frames for POC"
        }

