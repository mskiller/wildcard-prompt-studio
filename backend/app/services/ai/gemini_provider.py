from typing import Optional
import httpx
from app.services.ai.provider import AIProvider, AIProviderError

class GeminiProvider(AIProvider):
    def __init__(
        self,
        api_key: str = "",
        model: str = "gemini-1.5-flash",
        base_url: str = "https://generativelanguage.googleapis.com",
        timeout: float = 60.0
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

    async def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        if not self.api_key:
            raise AIProviderError("[Gemini Error] API key is missing or unconfigured.")

        gen_config = {
            "temperature": temperature
        }
        if max_tokens is not None:
            gen_config["maxOutputTokens"] = max_tokens

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": gen_config
        }


        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }

        url = f"{self.base_url}/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except Exception as e:
                raise AIProviderError(f"[Gemini Error] {str(e)}") from e
