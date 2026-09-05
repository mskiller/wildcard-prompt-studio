import os
import sys
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from main import app
from app.api.routers.images import STATIC_IMAGES_DIR

client = TestClient(app)

import uuid

def test_create_and_get_gallery():
    unique_fn = f"test_unit_render_{uuid.uuid4().hex[:8]}.png"
    # 1. Create an image with prompt_content
    payload = {
        "filename": unique_fn,
        "prompt_content": "a futuristic cybernetic cat in Tokyo",
        "seed": 99999,
        "cfg_scale": 1.0,
        "steps": 10,
        "sampler_name": "er_sde"
    }
    create_resp = client.post("/api/v1/images/", json=payload)
    assert create_resp.status_code == 200
    created_data = create_resp.json()
    assert created_data["filename"] == unique_fn
    assert created_data["seed"] == 99999

    # 2. Get gallery and ensure prompt_content matches
    gallery_resp = client.get("/api/v1/images/gallery")
    assert gallery_resp.status_code == 200
    gallery_items = gallery_resp.json()
    matched = [item for item in gallery_items if item["filename"] == unique_fn]
    assert len(matched) == 1
    assert matched[0]["prompt_content"] == "a futuristic cybernetic cat in Tokyo"

    # Cleanup
    client.delete(f"/api/v1/images/{created_data['id']}")

def test_serve_image_file_local_and_fallback():
    test_filename = "test_stream_file.png"
    local_path = os.path.join(STATIC_IMAGES_DIR, test_filename)
    
    # Test local serving
    with open(local_path, "wb") as f:
        f.write(b"PNG_FAKE_DATA_FOR_TEST")
    
    try:
        resp = client.get(f"/api/v1/images/file/{test_filename}")
        assert resp.status_code == 200
        assert resp.content == b"PNG_FAKE_DATA_FOR_TEST"
    finally:
        if os.path.exists(local_path):
            os.remove(local_path)
    
    # Test fallback to ComfyUI
    with patch("app.api.routers.images.ComfyUIConnector.get_image", new_callable=AsyncMock) as mock_get_image:
        mock_get_image.return_value = b"COMFY_FALLBACK_BYTES"
        resp_fallback = client.get(f"/api/v1/images/file/comfy_fallback_test.png")
        assert resp_fallback.status_code == 200
        assert resp_fallback.content == b"COMFY_FALLBACK_BYTES"
        # Verify it cached locally
        cached_path = os.path.join(STATIC_IMAGES_DIR, "comfy_fallback_test.png")
        assert os.path.exists(cached_path)
        os.remove(cached_path)
