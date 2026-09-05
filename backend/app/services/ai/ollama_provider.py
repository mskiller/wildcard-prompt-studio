import os
from typing import Optional
import httpx
from app.services.ai.provider import AIProvider, AIProviderError
from app.services.ai.utils import get_url_candidates

class OllamaProvider(AIProvider):
    def __init__(self, base_url: str = None, model: str = "llama3", timeout: float = 60.0):
        default_url = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
        self.base_url = base_url if base_url else default_url
        self.model = model
        self.timeout = timeout

    async def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        options = {
            "temperature": temperature
        }
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        payload = {
            "model": self.model,
            "messages": messages,
            "options": options,
            "stream": False
        }


        candidates = get_url_candidates(self.base_url, default_port=11434)
        last_exception = None

        for candidate in candidates:
            url = f"{candidate}/api/chat"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                try:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    return data["message"]["content"]
                except (httpx.ConnectError, httpx.ConnectTimeout) as e:
                    last_exception = e
                    continue
                except Exception as e:
                    raise AIProviderError(f"[Ollama Error] {str(e)}") from e

        raise AIProviderError(f"[Ollama Error] All connection attempts failed: {str(last_exception)}")

