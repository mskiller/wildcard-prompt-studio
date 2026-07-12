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
