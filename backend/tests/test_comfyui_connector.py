import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.api.routers.comfyui import router
from app.services.comfyui_ws import ComfyUIWSManager

from app.services.comfyui_connector import ComfyUIConnector
from unittest.mock import MagicMock

import respx
import httpx
from main import app

def test_comfyui_router_prefix():
    routes = [route.path for route in app.routes]
    assert any(route.startswith("/api/v1/comfyui") for route in routes)

@pytest.mark.asyncio
async def test_comfyui_ws_manager_connect():
    manager = ComfyUIWSManager()
    mock_ws = AsyncMock()
    await manager.connect(mock_ws, "client-123")
    assert "client-123" in manager.active_connections
    assert manager.active_connections["client-123"] == mock_ws
    
    manager.disconnect("client-123")
    assert "client-123" not in manager.active_connections

@pytest.mark.asyncio
async def test_comfyui_connector_queue_prompt():
    connector = ComfyUIConnector()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"prompt_id": "test-prompt-123"}
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        res = await connector.queue_prompt({"3": {"class_type": "KSampler"}})
        assert res["prompt_id"] == "test-prompt-123"
        mock_post.assert_called()

@pytest.mark.asyncio
@respx.mock
async def test_get_image_404_raises_filenotfound():
    connector = ComfyUIConnector(default_url="http://host.docker.internal:8188")
    respx.get("http://host.docker.internal:8188/view").respond(status_code=404)
    respx.get("http://localhost:8188/view").respond(status_code=404)
    respx.get("http://127.0.0.1:8188/view").respond(status_code=404)

    with pytest.raises(FileNotFoundError):
        await connector.get_image("nonexistent_preview.png")

def test_router_get_image_404():
    client = TestClient(app)
    with patch("app.api.routers.comfyui.connector.get_image", new_callable=AsyncMock) as mock_get_image:
        mock_get_image.side_effect = FileNotFoundError("Image 'missing.png' not found in ComfyUI")
        response = client.get("/api/v1/comfyui/image/missing.png")
        assert response.status_code == 404
        assert "Image 'missing.png' not found in ComfyUI" in response.json()["detail"]

def test_router_view_image_404():
    client = TestClient(app)
    with patch("app.api.routers.comfyui.connector.get_image", new_callable=AsyncMock) as mock_get_image:
        mock_get_image.side_effect = FileNotFoundError("Image 'missing.png' not found in ComfyUI")
        response = client.get("/api/v1/comfyui/view?filename=missing.png")
        assert response.status_code == 404
        assert "Image 'missing.png' not found in ComfyUI" in response.json()["detail"]

