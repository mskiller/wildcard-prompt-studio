import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from main import app
from app.dependencies import get_wildcard_engine
from app.services.wildcard_engine import WildcardEngine
import httpx

client = TestClient(app)

def test_expand_prompt():
    engine = WildcardEngine({"character": ["elf", "knight"]})
    app.dependency_overrides[get_wildcard_engine] = lambda: engine
    
    response = client.post(
        "/api/v1/generate/expand",
        json={"prompt": "A brave __character__"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "expanded_prompt" in data
    assert data["expanded_prompt"] in ["A brave elf", "A brave knight"]
    
    app.dependency_overrides.clear()

@patch("app.api.routers.generate.ComfyUIConnector.queue_prompt", new_callable=AsyncMock)
def test_submit_workflow(mock_queue_prompt):
    mock_queue_prompt.return_value = {"prompt_id": "12345"}
    
    workflow_data = {"test_node": {"class_type": "KSampler"}}
    response = client.post(
        "/api/v1/generate/submit",
        json={"workflow": workflow_data}
    )
    
    assert response.status_code == 200
    assert response.json() == {"prompt_id": "12345"}
    mock_queue_prompt.assert_called_once_with(workflow_data, base_url=None)

@patch("app.api.routers.generate.ComfyUIConnector.queue_prompt", new_callable=AsyncMock)
def test_submit_workflow_error(mock_queue_prompt):
    mock_queue_prompt.side_effect = httpx.HTTPError("Error")
    
    workflow_data = {"test_node": {"class_type": "KSampler"}}
    response = client.post(
        "/api/v1/generate/submit",
        json={"workflow": workflow_data}
    )
    
    assert response.status_code == 502
    assert response.json() == {"detail": "ComfyUI server error: Error"}
