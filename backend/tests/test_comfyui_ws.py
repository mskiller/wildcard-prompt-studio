import json
import base64
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.services.comfyui_ws import ComfyUIWSManager
from app.services.comfyui_connector import listen_comfyui_websocket
from app.api.routers.comfyui import router as comfyui_router


@pytest.mark.asyncio
async def test_ws_manager_connection_registration():
    manager = ComfyUIWSManager()
    mock_ws = AsyncMock()

    await manager.connect(mock_ws, "client-001")
    assert "client-001" in manager.active_connections
    assert manager.active_connections["client-001"] == mock_ws

    manager.disconnect("client-001")
    assert "client-001" not in manager.active_connections


@pytest.mark.asyncio
async def test_ws_manager_active_execution_mapping():
    manager = ComfyUIWSManager()
    
    execution_info = {
        "prompt_id": "prompt-abc",
        "node_id": "3",
        "status": "executing"
    }
    
    manager.set_active_execution("client-001", execution_info)
    assert manager.get_active_execution("client-001") == execution_info
    
    # Update mapping
    updated_info = {**execution_info, "progress": 50}
    manager.set_active_execution("client-001", updated_info)
    assert manager.get_active_execution("client-001")["progress"] == 50

    manager.clear_active_execution("client-001")
    assert manager.get_active_execution("client-001") is None


@pytest.mark.asyncio
async def test_ws_manager_message_proxying_and_broadcasting():
    manager = ComfyUIWSManager()
    mock_ws1 = AsyncMock()
    mock_ws2 = AsyncMock()

    await manager.connect(mock_ws1, "client-001")
    await manager.connect(mock_ws2, "client-002")

    # Personal proxy message
    msg = {"type": "executing", "data": {"node": "5"}}
    await manager.proxy_message("client-001", msg)
    mock_ws1.send_json.assert_called_once_with(msg)
    mock_ws2.send_json.assert_not_called()

    # Broadcast message
    bcast_msg = {"type": "status", "data": {"queue_remaining": 0}}
    await manager.broadcast(bcast_msg)
    mock_ws1.send_json.assert_called_with(bcast_msg)
    mock_ws2.send_json.assert_called_with(bcast_msg)


@pytest.mark.asyncio
async def test_listen_comfyui_websocket_json_events():
    received_messages = []

    async def mock_callback(msg):
        received_messages.append(msg)

    # Mock websockets.connect
    mock_ws_connection = AsyncMock()
    
    # Return two JSON messages then close
    event_status = json.dumps({"type": "status", "data": {"status": "ok"}})
    event_executing = json.dumps({"type": "executing", "data": {"node": "3", "prompt_id": "p-123"}})
    
    mock_ws_connection.__aiter__.return_value = [event_status, event_executing]

    class MockWebSocketContext:
        def __init__(self, ws):
            self.ws = ws
        async def __aenter__(self):
            return self.ws
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return None

    with patch("websockets.connect", side_effect=lambda *args, **kwargs: MockWebSocketContext(mock_ws_connection)) as mock_connect:
        await listen_comfyui_websocket("http://localhost:8188", "client-001", mock_callback, max_retries=1)

        assert len(received_messages) == 2
        assert received_messages[0] == {"type": "status", "data": {"status": "ok"}}
        assert received_messages[1] == {"type": "executing", "data": {"node": "3", "prompt_id": "p-123"}}
        mock_connect.assert_called_once()
        call_url = mock_connect.call_args[0][0]
        assert "clientId=client-001" in call_url and ":8188/ws" in call_url


@pytest.mark.asyncio
async def test_listen_comfyui_websocket_binary_preview_images():
    received_messages = []

    async def mock_callback(msg):
        received_messages.append(msg)

    mock_ws_connection = AsyncMock()
    
    # Binary frame header (8 bytes) + raw jpeg content
    fake_header = b"\x00\x00\x00\x01\x00\x00\x00\x01"
    fake_image_bytes = b"\xff\xd8\xff\xe0fake_jpeg_stream"
    binary_frame = fake_header + fake_image_bytes

    mock_ws_connection.__aiter__.return_value = [binary_frame]

    class MockWebSocketContext:
        def __init__(self, ws):
            self.ws = ws
        async def __aenter__(self):
            return self.ws
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return None

    with patch("websockets.connect", side_effect=lambda *args, **kwargs: MockWebSocketContext(mock_ws_connection)) as mock_connect:
        await listen_comfyui_websocket("http://localhost:8188", "client-001", mock_callback, max_retries=1)

        assert len(received_messages) == 1
        msg = received_messages[0]
        assert msg["type"] == "preview_image" or msg["type"] == "preview"
        assert "data" in msg
        assert "image_b64" in msg["data"] or "b64" in msg["data"]
        expected_b64 = base64.b64encode(binary_frame).decode("utf-8")
        # Check base64 data encoding exists
        b64_val = msg["data"].get("image_b64") or msg["data"].get("b64")
        assert len(b64_val) > 0


@pytest.mark.asyncio
async def test_listen_comfyui_websocket_callback_error_resilience():
    processed_count = 0

    async def faulty_callback(msg):
        nonlocal processed_count
        processed_count += 1
        if processed_count == 1:
            raise RuntimeError("Simulated callback exception")

    mock_ws_connection = AsyncMock()
    msg1 = json.dumps({"type": "event1"})
    msg2 = json.dumps({"type": "event2"})
    mock_ws_connection.__aiter__.return_value = [msg1, msg2]

    class MockWebSocketContext:
        def __init__(self, ws):
            self.ws = ws
        async def __aenter__(self):
            return self.ws
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return None

    with patch("websockets.connect", side_effect=lambda *args, **kwargs: MockWebSocketContext(mock_ws_connection)) as mock_connect:
        await listen_comfyui_websocket("http://localhost:8188", "client-001", faulty_callback, max_retries=1)

    assert processed_count == 2


def test_router_queue_endpoint():
    app = FastAPI()
    app.include_router(comfyui_router)
    client = TestClient(app)

    with patch("app.api.routers.comfyui.connector.queue_prompt", new_callable=AsyncMock) as mock_queue:
        mock_queue.return_value = {"prompt_id": "p-100"}

        response = client.post("/queue", json={
            "prompt": {"6": {"class_type": "CLIPTextEncode", "inputs": {"text": "test"}}},
            "base_url": "http://localhost:8188"
        })
        assert response.status_code == 200
        assert response.json() == {"prompt_id": "p-100"}
        mock_queue.assert_called_once()


def test_router_execute_sweep_endpoint():
    app = FastAPI()
    app.include_router(comfyui_router)
    client = TestClient(app)

    with patch("app.api.routers.comfyui.connector.queue_prompt", new_callable=AsyncMock) as mock_queue:
        mock_queue.return_value = {"prompt_id": "p-sweep"}

        workflow = {
            "6": {"class_type": "CLIPTextEncode", "inputs": {"text": "default"}},
            "3": {"class_type": "KSampler", "inputs": {"seed": 42}}
        }
        payload = {
            "workflow": workflow,
            "target_node_id": "6",
            "prompts": ["prompt 1", "prompt 2"],
            "seed_node_id": "3",
            "base_url": "http://localhost:8188"
        }

        response = client.post("/execute-sweep", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["queued_count"] == 2
        assert len(data["job_results"]) == 2
        assert mock_queue.call_count == 2

        call1_args = mock_queue.call_args_list[0][0][0]
        assert call1_args["6"]["inputs"]["text"] == "prompt 1"
        assert call1_args["3"]["inputs"]["seed"] == 42

        call2_args = mock_queue.call_args_list[1][0][0]
        assert call2_args["6"]["inputs"]["text"] == "prompt 2"
        assert call2_args["3"]["inputs"]["seed"] == 43


def test_router_websocket_endpoint():
    app = FastAPI()
    app.include_router(comfyui_router)
    client = TestClient(app)

    with patch("app.api.routers.comfyui.listen_comfyui_websocket", new_callable=AsyncMock) as mock_listen:
        with client.websocket_connect("/ws/client-test-123") as websocket:
            websocket.send_text(json.dumps({"type": "test"}))
            response = websocket.receive_json()
            assert response == {"type": "ack", "data": {"type": "test"}}

