import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@patch("app.api.routers.ai.improve_prompt", new_callable=AsyncMock)
def test_improve_prompt(mock_improve):
    mock_improve.return_value = "A cute cat, cinematic lighting, 8k resolution, photorealistic"
    response = client.post(
        "/api/v1/ai/improve",
        json={"prompt": "A cute cat", "target_model": "stable-diffusion-xl"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "improved_prompt" in data
    assert data["improved_prompt"] == "A cute cat, cinematic lighting, 8k resolution, photorealistic"
    mock_improve.assert_called_once()
