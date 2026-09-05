import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
BASE_URL = "/api/v1"

def test_prompt_crud():
    # Create
    create_resp = client.post(f"{BASE_URL}/prompts/", json={"content": "Test prompt content"})
    assert create_resp.status_code == 200
    prompt_data = create_resp.json()
    assert "id" in prompt_data
    assert prompt_data["content"] == "Test prompt content"
    prompt_id = prompt_data["id"]

    # Read All
    list_resp = client.get(f"{BASE_URL}/prompts/")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) > 0

    # Read One
    get_resp = client.get(f"{BASE_URL}/prompts/{prompt_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == prompt_id

    # Update
    update_resp = client.patch(f"{BASE_URL}/prompts/{prompt_id}", json={"content": "Updated prompt content"})
    assert update_resp.status_code == 200
    assert update_resp.json()["content"] == "Updated prompt content"

    # Delete
    delete_resp = client.delete(f"{BASE_URL}/prompts/{prompt_id}")
    assert delete_resp.status_code == 200

    # Verify Delete
    get_deleted = client.get(f"{BASE_URL}/prompts/{prompt_id}")
    assert get_deleted.status_code == 404

def test_wildcard_crud():
    # Create
    create_resp = client.post(f"{BASE_URL}/wildcards/", json={"filename": "test.txt", "content": "test,wildcard"})
    assert create_resp.status_code == 200
    wildcard_data = create_resp.json()
    assert wildcard_data["filename"] == "test.txt"
    wildcard_id = wildcard_data["id"]

    # Update
    update_resp = client.patch(f"{BASE_URL}/wildcards/{wildcard_id}", json={"filename": "test2.txt", "content": "updated"})
    assert update_resp.status_code == 200
    assert update_resp.json()["filename"] == "test2.txt"

    # Delete
    delete_resp = client.delete(f"{BASE_URL}/wildcards/{wildcard_id}")
    assert delete_resp.status_code == 200

def test_tag_crud():
    create_resp = client.post(f"{BASE_URL}/tags/", json={"name": "test_tag", "category": "test"})
    assert create_resp.status_code == 200
    tag_data = create_resp.json()
    tag_id = tag_data["id"]

    update_resp = client.patch(f"{BASE_URL}/tags/{tag_id}", json={"name": "test_tag_updated"})
    assert update_resp.status_code == 200

    delete_resp = client.delete(f"{BASE_URL}/tags/{tag_id}")
    assert delete_resp.status_code == 200

def test_image_crud():
    # Create a prompt first for the foreign key
    prompt_resp = client.post(f"{BASE_URL}/prompts/", json={"content": "Prompt for image"})
    prompt_id = prompt_resp.json()["id"]

    create_resp = client.post(f"{BASE_URL}/images/", json={"filename": "test_image.png", "prompt_id": prompt_id})
    assert create_resp.status_code == 200
    image_data = create_resp.json()
    image_id = image_data["id"]

    update_resp = client.patch(f"{BASE_URL}/images/{image_id}", json={"filename": "updated.png"})
    assert update_resp.status_code == 200

    delete_resp = client.delete(f"{BASE_URL}/images/{image_id}")
    assert delete_resp.status_code == 200
    delete_prompt_resp = client.delete(f"{BASE_URL}/prompts/{prompt_id}")
    assert delete_prompt_resp.status_code == 200

from unittest.mock import AsyncMock
from app.dependencies import get_provider_manager, get_matrix_engine
from app.services.ai.provider_manager import AIProviderManager
from app.services.ai.provider import AIProvider
from app.services.matrix_engine import MatrixEngine

def test_krea2_improve_endpoint_basic():
    response = client.post(
        f"{BASE_URL}/ai/krea2-improve",
        json={"prompt": "masterpiece, 8k, a glowing sword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "improved_prompt" in data
    assert "masterpiece" not in data["improved_prompt"].lower()
    assert "8k" not in data["improved_prompt"].lower()
    assert "a glowing sword" in data["improved_prompt"]

def test_krea2_improve_endpoint_with_options():
    response = client.post(
        f"{BASE_URL}/ai/krea2-improve",
        json={
            "prompt": "a neon sign that says Open 24/7",
            "variant": "medium",
            "quote_targets": ["Open 24/7"],
            "clean_buzzwords": True,
            "provider": "kobold"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "improved_prompt" in data
    assert '"Open 24/7"' in data["improved_prompt"]

def test_krea2_improve_endpoint_with_mocked_provider():
    mock_provider = AsyncMock(spec=AIProvider)
    mock_provider.generate.return_value = "An elegant painting of a dragon resting atop a mountain."

    manager = AIProviderManager()
    manager.register_provider("mock_provider", mock_provider)

    app.dependency_overrides[get_provider_manager] = lambda: manager

    response = client.post(
        f"{BASE_URL}/ai/krea2-improve",
        json={
            "prompt": "a dragon resting atop a mountain",
            "variant": "large",
            "provider": "mock_provider"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["improved_prompt"] == "An elegant painting of a dragon resting atop a mountain."

    app.dependency_overrides.clear()

def test_anima_improve_endpoint_basic():
    response = client.post(
        f"{BASE_URL}/ai/anima-improve",
        json={"prompt": "(glowing sword:1.2), artist:shinkai_makoto, cat ears"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "improved_prompt" in data
    assert "score_9" in data["improved_prompt"]
    assert "@shinkai_makoto" in data["improved_prompt"]
    assert "(glowing sword:1.2)" not in data["improved_prompt"]
    assert "glowing sword" in data["improved_prompt"]

def test_anima_improve_endpoint_with_mocked_provider():
    mock_provider = AsyncMock(spec=AIProvider)
    mock_provider.model = "default-model"
    mock_provider.generate.return_value = "score_9, score_8, score_7, 1girl, vibrant scenery"

    manager = AIProviderManager()
    manager.register_provider("mock_anima_provider", mock_provider)

    app.dependency_overrides[get_provider_manager] = lambda: manager

    response = client.post(
        f"{BASE_URL}/ai/anima-improve",
        json={
            "prompt": "1girl, vibrant scenery",
            "provider": "mock_anima_provider",
            "model": "custom-anima-model",
            "max_tokens": 2048
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["improved_prompt"] == "score_9, score_8, score_7, 1girl, vibrant scenery"
    assert mock_provider.model == "custom-anima-model"
    mock_provider.generate.assert_called_once()
    _, kwargs = mock_provider.generate.call_args
    assert kwargs.get("max_tokens") == 2048

    app.dependency_overrides.clear()

def test_kobold_integration_test_unreachable():
    response = client.post(
        f"{BASE_URL}/ai/integrations/test",
        json={"provider": "kobold", "url": "http://127.0.0.1:59999"}
    )
    assert response.status_code == 502
    assert response.json()["detail"] == "KoboldCpp server unreachable"


def test_matrix_generate_endpoint():
    response = client.post(
        f"{BASE_URL}/generate/matrix",
        json={"prompt": "{red|blue} {car|bike}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 4
    assert "red car" in data
    assert "red bike" in data
    assert "blue car" in data
    assert "blue bike" in data

def test_matrix_generate_endpoint_with_wildcards():
    mock_engine = MatrixEngine(wildcards={"color": ["crimson", "azure"]})
    app.dependency_overrides[get_matrix_engine] = lambda: mock_engine

    response = client.post(
        f"{BASE_URL}/generate/matrix",
        json={"prompt": "__color__ dragon"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data == ["crimson dragon", "azure dragon"]

    app.dependency_overrides.clear()

