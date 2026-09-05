import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi.testclient import TestClient
from main import app
from app.dependencies import get_db

client = TestClient(app)

def test_create_prompt():
    response = client.post(
        "/api/v1/prompts/",
        json={"name": "Test Prompt", "content": "A test prompt"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Prompt"
    assert data["content"] == "A test prompt"
    assert "id" in data

def test_get_prompts():
    response = client.get("/api/v1/prompts/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_prompt_version():
    # First create a prompt
    create_response = client.post(
        "/api/v1/prompts/",
        json={"name": "Versioned Prompt", "content": "v1"}
    )
    prompt_id = create_response.json()["id"]

    # Then create a version
    version_response = client.post(
        f"/api/v1/prompts/{prompt_id}/versions",
        json={"content": "v2", "commit_message": "updated content"}
    )
    assert version_response.status_code == 200
    data = version_response.json()
    assert data["content"] == "v2"
    assert data["commit_message"] == "updated content"
