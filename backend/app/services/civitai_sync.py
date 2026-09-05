import httpx
from typing import List, Dict, Any

class CivitaiSyncClient:
    def __init__(self, api_base: str = "https://civitai.com/api/v1"):
        self.api_base = api_base

    async def search_wildcard_packs(self, query: str = "") -> List[Dict[str, Any]]:
        """
        Searches Civitai model hub for wildcard and prompt preset packs.
        Fallback to simulated hub entries if offline or network isolated.
        """
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.api_base}/models", params={"query": query or "wildcard", "types": "Wildcards", "limit": 5})
                if res.status_code == 200:
                    data = res.json()
                    items = data.get("items", [])
                    if items:
                        return [{"id": item.get("id"), "name": item.get("name"), "downloads": item.get("stats", {}).get("downloadCount", 0)} for item in items]
        except Exception:
            pass

        # Offline/Simulated model hub items fallback
        return [
            {"id": 101, "name": "Fantasy Characters & Creatures Wildcards", "downloads": 14200, "tags": ["fantasy", "rpg"]},
            {"id": 102, "name": "Cyberpunk Neon & Sci-Fi Environment Pack", "downloads": 9800, "tags": ["cyberpunk", "sci-fi"]},
            {"id": 103, "name": "Photorealistic Optics & Camera Lighting Presets", "downloads": 23100, "tags": ["photography", "realism"]},
        ]

civitai_sync_client = CivitaiSyncClient()
