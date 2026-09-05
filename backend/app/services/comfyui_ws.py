import base64
import json
import logging
from typing import Dict, Any, Optional, Tuple, Union
from fastapi import WebSocket

logger = logging.getLogger(__name__)


def parse_ws_message(message: Union[bytes, bytearray, str, Dict[str, Any]]) -> Tuple[str, Any]:
    """
    Parses an incoming WebSocket message from ComfyUI.
    - Binary frames: Skipping the first 8 bytes (header offset), base64-encodes the remaining image bytes as a data URI.
      Returns ("PREVIEW_IMAGE", "data:image/jpeg;base64,...") or png data URI.
    - JSON text frames / dicts: extracts type and data payload.
    """
    if isinstance(message, (bytes, bytearray)):
        image_bytes = message[8:] if len(message) >= 8 else message
        mime_type = "image/jpeg"
        if image_bytes.startswith(b"\x89PNG"):
            mime_type = "image/png"
        elif image_bytes.startswith(b"\xff\xd8"):
            mime_type = "image/jpeg"

        b64_str = base64.b64encode(image_bytes).decode("utf-8")
        data_uri = f"data:{mime_type};base64,{b64_str}"
        return "PREVIEW_IMAGE", data_uri

    if isinstance(message, str):
        try:
            parsed = json.loads(message)
            if isinstance(parsed, dict):
                msg_type = parsed.get("type", "UNKNOWN")
                payload = parsed.get("data", parsed)
                return msg_type, payload
            return "TEXT", parsed
        except Exception:
            return "TEXT", message

    if isinstance(message, dict):
        msg_type = message.get("type", "UNKNOWN")
        payload = message.get("data", message)
        return msg_type, payload

    return "UNKNOWN", message



class ComfyUIWSManager:
    def __init__(self) -> None:
        self.active_connections: Dict[str, WebSocket] = {}
        self.active_executions: Dict[str, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket client {client_id} connected.")

    def disconnect(self, client_id: str) -> None:
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket client {client_id} disconnected.")
        if client_id in self.active_executions:
            del self.active_executions[client_id]

    def set_active_execution(self, client_id: str, execution_info: Dict[str, Any]) -> None:
        self.active_executions[client_id] = execution_info

    def get_active_execution(self, client_id: str) -> Optional[Dict[str, Any]]:
        return self.active_executions.get(client_id)

    def clear_active_execution(self, client_id: str) -> None:
        if client_id in self.active_executions:
            del self.active_executions[client_id]

    async def send_personal_message(self, message: Dict[str, Any], client_id: str) -> None:
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send personal WS message to {client_id}: {e}")
                self.disconnect(client_id)

    async def proxy_message(self, client_id: str, message: Dict[str, Any]) -> None:
        msg_type = message.get("type")
        msg_data = message.get("data")
        if isinstance(msg_data, dict):
            if msg_type in ("executing", "progress", "execution_cached", "status"):
                current = self.active_executions.get(client_id, {})
                current.update({"type": msg_type, **msg_data})
                self.active_executions[client_id] = current
            elif msg_type == "executed":
                current = self.active_executions.get(client_id, {})
                current.update({"type": msg_type, "last_executed": msg_data})
                self.active_executions[client_id] = current

        if client_id and client_id in self.active_connections:
            await self.send_personal_message(message, client_id)
        else:
            await self.broadcast(message)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        for client_id, websocket in list(self.active_connections.items()):
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send WS message to {client_id}: {e}")
                self.disconnect(client_id)


comfyui_ws_manager = ComfyUIWSManager()

