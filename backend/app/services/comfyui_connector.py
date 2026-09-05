import os
import json
import base64
import logging
import asyncio
import time
from typing import Callable, Dict, Any, Optional
import httpx
try:
    import websockets
except ImportError:
    websockets = None

from app.services.ai.utils import get_url_candidates

logger = logging.getLogger(__name__)


async def listen_comfyui_websocket(
    base_url: Optional[str],
    client_id: str,
    on_message_callback: Callable[[Dict[str, Any]], Any],
    retry_delay: float = 1.0,
    max_retries: Optional[int] = None,
) -> None:
    """
    Connects to ComfyUI's native WebSocket feed (ws://<comfy_host>/ws?clientId=<client_id>)
    and listens for real-time execution events & binary preview frames.
    Calls on_message_callback(parsed_message) for each incoming event.
    """
    if websockets is None:
        logger.error("websockets package is not installed. Cannot listen to ComfyUI websocket.")
        return

    target_url = base_url or os.getenv("COMFYUI_URL", "http://host.docker.internal:8188")
    candidates = get_url_candidates(target_url, default_port=8188)

    retries = 0
    while True:
        last_exc = None
        for candidate in candidates:
            cand_clean = candidate.rstrip('/')
            if cand_clean.startswith("http://"):
                ws_base = "ws://" + cand_clean[7:]
            elif cand_clean.startswith("https://"):
                ws_base = "wss://" + cand_clean[8:]
            elif not cand_clean.startswith("ws://") and not cand_clean.startswith("wss://"):
                ws_base = "ws://" + cand_clean
            else:
                ws_base = cand_clean

            ws_url = f"{ws_base}/ws?clientId={client_id}"
            try:
                async with websockets.connect(ws_url) as ws:
                    async for message in ws:
                        if isinstance(message, str):
                            try:
                                payload = json.loads(message)
                            except Exception:
                                payload = {"type": "raw", "data": message}
                        elif isinstance(message, (bytes, bytearray)):
                            img_data = message
                            mime_type = "image/png"
                            if len(message) > 8:
                                header_stripped = message[8:]
                                if header_stripped.startswith(b"\xff\xd8"):
                                    img_data = header_stripped
                                    mime_type = "image/jpeg"
                                elif header_stripped.startswith(b"\x89PNG"):
                                    img_data = header_stripped
                                    mime_type = "image/png"
                                elif message.startswith(b"\xff\xd8"):
                                    img_data = message
                                    mime_type = "image/jpeg"
                                elif message.startswith(b"\x89PNG"):
                                    img_data = message
                                    mime_type = "image/png"
                            elif message.startswith(b"\xff\xd8"):
                                img_data = message
                                mime_type = "image/jpeg"
                            elif message.startswith(b"\x89PNG"):
                                img_data = message
                                mime_type = "image/png"

                            b64_str = base64.b64encode(img_data).decode("utf-8")
                            data_url = f"data:{mime_type};base64,{b64_str}"
                            payload = {
                                "type": "preview_image",
                                "data": {
                                    "image_b64": data_url,
                                    "b64": data_url
                                }
                            }
                        else:
                            continue

                        try:
                            if asyncio.iscoroutinefunction(on_message_callback):
                                await on_message_callback(payload)
                            else:
                                on_message_callback(payload)
                        except Exception as cb_err:
                            logger.error(f"Error in on_message_callback: {cb_err}", exc_info=True)
                    return
            except asyncio.CancelledError:
                raise
            except Exception as e:
                last_exc = e
                logger.warning(f"Failed to connect to ComfyUI WebSocket at {ws_url}: {e}")
                continue

        if last_exc:
            logger.error(f"ComfyUI WebSocket connection failed for all candidates of {target_url}: {last_exc}")

        retries += 1
        if max_retries is not None and retries >= max_retries:
            break

        try:
            await asyncio.sleep(retry_delay)
        except asyncio.CancelledError:
            raise


class ComfyUIConnector:
    def __init__(self, default_url: Optional[str] = None) -> None:
        self.default_url: str = default_url or os.getenv("COMFYUI_URL", "http://host.docker.internal:8188")

    async def queue_prompt(self, prompt_workflow: Dict[str, Any], base_url: Optional[str] = None, client_id: Optional[str] = None) -> Dict[str, Any]:
        target_url = base_url or self.default_url
        candidates = get_url_candidates(target_url, default_port=8188)
        
        # Ensure payload is correctly nested for ComfyUI's /prompt endpoint
        if isinstance(prompt_workflow, dict) and "prompt" in prompt_workflow and isinstance(prompt_workflow["prompt"], dict):
            payload = dict(prompt_workflow)
        else:
            payload = {"prompt": prompt_workflow}

        if client_id:
            payload["client_id"] = client_id

        last_exc = None
        for candidate in candidates:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.post(f"{candidate}/prompt", json=payload)
                    response.raise_for_status()
                    return response.json()
            except Exception as e:
                last_exc = e
                continue

        raise httpx.ConnectError(f"Failed to connect to ComfyUI at {target_url}: {str(last_exc)}")

    async def get_history(self, prompt_id: str, base_url: Optional[str] = None) -> Dict[str, Any]:
        target_url = base_url or self.default_url
        candidates = get_url_candidates(target_url, default_port=8188)
        last_exc = None
        for candidate in candidates:
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    response = await client.get(f"{candidate}/history/{prompt_id}")
                    response.raise_for_status()
                    return response.json()
            except Exception as e:
                last_exc = e
                continue
        raise httpx.ConnectError(f"Failed to connect to ComfyUI history at {target_url}: {str(last_exc)}")

    async def get_all_history(self, max_items: int = 50, base_url: Optional[str] = None) -> Dict[str, Any]:
        target_url = base_url or self.default_url
        candidates = get_url_candidates(target_url, default_port=8188)
        last_exc = None
        for candidate in candidates:
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    response = await client.get(f"{candidate}/history", params={"max_items": max_items})
                    response.raise_for_status()
                    return response.json()
            except Exception as e:
                last_exc = e
                continue
        raise httpx.ConnectError(f"Failed to connect to ComfyUI history at {target_url}: {str(last_exc)}")

    async def get_image(self, filename: str, folder_type: str = "output", subfolder: str = "", base_url: Optional[str] = None) -> bytes:
        target_url = base_url or self.default_url
        candidates = get_url_candidates(target_url, default_port=8188)
        last_exc = None
        for candidate in candidates:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{candidate}/view", params={"filename": filename, "subfolder": subfolder, "type": folder_type})
                    if response.status_code == 404:
                        raise FileNotFoundError(f"Image '{filename}' not found in ComfyUI ({candidate})")
                    response.raise_for_status()
                    return response.content
            except FileNotFoundError:
                raise
            except Exception as e:
                last_exc = e
                continue
        raise httpx.ConnectError(f"Failed to fetch image from ComfyUI at {target_url}: {str(last_exc)}")

    async def get_object_info(self, base_url: Optional[str] = None) -> Dict[str, Any]:
        target_url = base_url or self.default_url
        now = time.time()
        if hasattr(self, "_object_info_cache") and self._object_info_cache:
            cached_url, cached_time, cached_data = self._object_info_cache
            if cached_url == target_url and (now - cached_time) < 60:
                return cached_data

        candidates = get_url_candidates(target_url, default_port=8188)
        last_exc = None
        for candidate in candidates:
            for path in ["/object_info", "/object_info/"]:
                try:
                    async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
                        response = await client.get(f"{candidate}{path}")
                        if response.status_code == 200:
                            data = response.json()
                            if isinstance(data, dict) and len(data) > 0:
                                self._object_info_cache = (target_url, now, data)
                                return data
                except Exception as e:
                    last_exc = e
                    continue
        raise httpx.ConnectError(f"Failed to fetch object_info from ComfyUI at {target_url}: {str(last_exc)}")

