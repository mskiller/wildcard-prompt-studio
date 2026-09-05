import base64
import json
import httpx
import os
from typing import Dict, Any, Optional

from app.services.ai.utils import get_url_candidates
from app.services.ai.thinking_parser import extract_final_prompt

class VisionService:
    def __init__(self):
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
        self.koboldcpp_host = os.getenv("KOBOLDCPP_HOST", "http://host.docker.internal:5001")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")

    async def describe_image(
        self,
        image_bytes: bytes,
        variant: str = "turbo",
        provider: str = "auto",
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """
        Reverse-engineer a raw image into a structured Krea 2 prompt.
        """
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        
        system_prompt = (
            f"You are an expert AI prompt engineer specializing in Krea 2 ({variant.upper()} variant). "
            "Analyze the image and describe it in a natural, highly descriptive prompt following Krea 2 rules:\n"
            "- Use fluid natural language without legacy quality buzzwords (no 8k, masterpiece, etc.).\n"
            "- Wrap any exact rendered text in double quotes (\"text\").\n"
            "- Describe key subject, composition, lighting, and mood directly.\n"
            "Return ONLY the optimized prompt text."
        )

        selected_provider = provider.lower()
        if selected_provider == "auto":
            selected_provider = "ollama"

        if selected_provider == "koboldcpp":
            prompt_text = await self._call_koboldcpp_vision(b64_image, system_prompt, max_tokens=max_tokens)
        elif selected_provider == "gemini":
            prompt_text = await self._call_gemini_vision(b64_image, system_prompt, max_tokens=max_tokens)
        else:
            prompt_text = await self._call_ollama_vision(b64_image, system_prompt, max_tokens=max_tokens)

        return {
            "prompt": extract_final_prompt(prompt_text),
            "variant": variant,
            "provider_used": selected_provider
        }

    async def extract_style_descriptors(
        self,
        image_bytes: bytes,
        provider: str = "auto"
    ) -> Dict[str, Any]:
        """
        Extract lighting, camera optics, color palette, and medium descriptors from an image.
        """
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        system_prompt = (
            "Analyze the image and extract key visual descriptors in JSON format with keys:\n"
            "\"lighting\": string,\n"
            "\"camera_optics\": string,\n"
            "\"color_palette\": string,\n"
            "\"medium\": string,\n"
            "\"subject\": string"
        )

        selected_provider = provider.lower()
        if selected_provider == "auto":
            selected_provider = "ollama"

        if selected_provider == "koboldcpp":
            res_raw = await self._call_koboldcpp_vision(b64_image, system_prompt)
        elif selected_provider == "gemini":
            res_raw = await self._call_gemini_vision(b64_image, system_prompt)
        else:
            res_raw = await self._call_ollama_vision(b64_image, system_prompt)

        try:
            # Parse JSON if output is JSON formatted
            start = res_raw.find("{")
            end = res_raw.rfind("}") + 1
            if start != -1 and end != 0:
                descriptors = json.loads(res_raw[start:end])
            else:
                descriptors = {"raw": res_raw.strip()}
        except Exception:
            descriptors = {"raw": res_raw.strip()}

        return {
            "descriptors": descriptors,
            "provider_used": selected_provider
        }

    async def _call_ollama_vision(self, b64_image: str, prompt: str, max_tokens: int = 4096) -> str:
        payload = {
            "model": os.getenv("OLLAMA_VISION_MODEL", "llava"),
            "prompt": prompt,
            "images": [b64_image],
            "stream": False,
            "options": {
                "num_predict": max_tokens
            }
        }
        candidates = get_url_candidates(self.ollama_host, default_port=11434)
        last_err = None

        for candidate in candidates:
            url = f"{candidate}/api/generate"
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        return resp.json().get("response", "")
                    else:
                        last_err = f"Ollama Vision status {resp.status_code}"
                except (httpx.ConnectError, httpx.ConnectTimeout) as e:
                    last_err = str(e)
                    continue
                except Exception as e:
                    return f"Ollama Vision error: {str(e)}"

        return f"Ollama Vision connection failed: {last_err}"

    async def _call_koboldcpp_vision(self, b64_image: str, prompt: str, max_tokens: int = 4096) -> str:
        payload = {
            "model": "koboldcpp-vision",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{b64_image}"}
                        }
                    ]
                }
            ],
            "max_tokens": max_tokens
        }
        candidates = get_url_candidates(self.koboldcpp_host, default_port=5001)
        last_err = None

        for candidate in candidates:
            url = f"{candidate}/v1/chat/completions"
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        return data["choices"][0]["message"]["content"]
                    else:
                        last_err = f"KoboldCpp Vision status {resp.status_code}"
                except (httpx.ConnectError, httpx.ConnectTimeout) as e:
                    last_err = str(e)
                    continue
                except Exception as e:
                    return f"KoboldCpp Vision error: {str(e)}"

        return f"KoboldCpp Vision connection failed: {last_err}"


    async def _call_gemini_vision(self, b64_image: str, prompt: str, max_tokens: int = 4096) -> str:
        if not self.gemini_api_key:
            return "Gemini Vision API key unconfigured."
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": b64_image
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": max_tokens
            }
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
            return f"Gemini Vision response status {resp.status_code}"

vision_service = VisionService()
