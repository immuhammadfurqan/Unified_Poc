import httpx
from typing import Dict, Any

class FigmaClient:
    BASE_URL = "https://api.figma.com/v1"

    async def get_file(self, token: str, file_key: str) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {token}"
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}/files/{file_key}", headers=headers)
            response.raise_for_status()
            return response.json()

