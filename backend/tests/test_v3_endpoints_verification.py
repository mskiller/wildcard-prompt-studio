import os
import sys
import io
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
BASE_URL = "/api/v1"

def test_v3_vision_describe_endpoint():
    dummy_image = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01Haf\x00\x00\x00\x00IEND\xaeB`\x82"
    with patch("app.services.ai.vision_service.vision_service.describe_image", new=AsyncMock(return_value={"description": "A radiant cyberpunk city street", "tags": ["cyberpunk", "city"]})):
        response = client.post(
            f"{BASE_URL}/ai/vision/describe",
            files={"file": ("test.png", io.BytesIO(dummy_image), "image/png")},
            data={"variant": "turbo", "provider": "auto"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "description" in data
        assert data["description"] == "A radiant cyberpunk city street"

def test_v3_wildcards_lint_endpoint():
    response = client.post(
        f"{BASE_URL}/wildcards/lint",
        json={"template": "A {vibrant|glowing} dragon with {red|blue|gold} wings"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "is_valid" in data
    assert data["is_valid"] is True
    assert "extracted_wildcards" in data

def test_v3_comfyui_execute_sweep_endpoint():
    mock_workflow = {
        "3": {
            "inputs": {
                "text": ""
            },
            "class_type": "CLIPTextEncode"
        }
    }
    with patch("app.services.comfyui_connector.ComfyUIConnector.queue_prompt", new=AsyncMock(return_value={"prompt_id": "sweep-123", "number": 1})):
        response = client.post(
            f"{BASE_URL}/comfyui/execute-sweep",
            json={
                "workflow": mock_workflow,
                "target_node_id": "3",
                "prompts": ["a cat in space", "a dog in space"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["queued_count"] == 2
        assert len(data["job_results"]) == 2

def test_v3_tags_endpoints():
    # GET tags
    get_resp = client.get(f"{BASE_URL}/tags/")
    assert get_resp.status_code == 200
    assert isinstance(get_resp.json(), list)

    # POST tag
    create_resp = client.post(f"{BASE_URL}/tags/", json={"name": "v3_test_tag", "category": "style"})
    assert create_resp.status_code == 200
    tag_data = create_resp.json()
    assert tag_data["name"] == "v3_test_tag"
    assert "id" in tag_data

    # Cleanup tag
    delete_resp = client.delete(f"{BASE_URL}/tags/{tag_data['id']}")
    assert delete_resp.status_code == 200

def test_v3_wildcards_import_endpoint():
    txt_content = b"cyberpunk\nsteampunk\nsci-fi\n"
    response = client.post(
        f"{BASE_URL}/wildcards/import",
        files=[
            ("files", ("scifi_styles.txt", io.BytesIO(txt_content), "text/plain"))
        ]
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["imported_wildcards"] >= 1
