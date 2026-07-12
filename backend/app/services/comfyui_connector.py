import os
import httpx

class ComfyUIConnector:
    def __init__(self):
        self.base_url = os.getenv("COMFYUI_URL", "http://localhost:8188")

    async def queue_prompt(self, prompt_workflow: dict) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/prompt", json={"prompt": prompt_workflow})
            response.raise_for_status()
            return response.json()

    async def get_history(self, prompt_id: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/history/{prompt_id}")
            response.raise_for_status()
            return response.json()
