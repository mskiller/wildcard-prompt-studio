import pytest
from fastapi.testclient import TestClient
from main import app
from app.dependencies import get_db

# Create a test client using the FastAPI app
client = TestClient(app)

def test_improve_prompt():
    response = client.post(
        "/api/v1/ai/improve",
        json={"prompt": "A cute cat", "target_model": "stable-diffusion-xl"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "improved_prompt" in data
    assert data["improved_prompt"] == "[MOCK AI] Processed: A cute cat"
