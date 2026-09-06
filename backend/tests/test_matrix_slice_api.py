import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_matrix_slice_endpoint():
    res = client.post("/generate/matrix/slice", json={
        "prompt": "photo of {cat|dog} with {hat|sunglasses}",
        "offset": 0,
        "limit": 2,
        "expand_wildcards": True
    })
    assert res.status_code == 200
    data = res.json()
    assert data["total_count"] == 4
    assert len(data["items"]) == 2
    assert data["items"][0]["index"] == 1
    assert data["items"][0]["prompt"] == "photo of cat with hat"
    assert data["items"][1]["index"] == 2
    assert data["items"][1]["prompt"] == "photo of cat with sunglasses"

def test_matrix_slice_sample_mode():
    res = client.post("/generate/matrix/slice", json={
        "prompt": "photo of {cat|dog} with {hat|sunglasses}",
        "sample_size": 2,
        "seed": 123,
        "expand_wildcards": True
    })
    assert res.status_code == 200
    data = res.json()
    assert data["total_count"] == 4
    assert data["is_sample"] is True
    assert len(data["items"]) == 2

def test_matrix_slice_explicit_indices():
    res = client.post("/generate/matrix/slice", json={
        "prompt": "photo of {cat|dog} with {hat|sunglasses}",
        "indices": [0, 3],
        "expand_wildcards": True
    })
    assert res.status_code == 200
    data = res.json()
    assert data["total_count"] == 4
    assert len(data["items"]) == 2
    assert data["items"][0]["index"] == 1
    assert data["items"][0]["prompt"] == "photo of cat with hat"
    assert data["items"][1]["index"] == 4
    assert data["items"][1]["prompt"] == "photo of dog with sunglasses"

def test_matrix_execute_range_and_sample():
    # Test range mode execution
    res = client.post("/generate/matrix/execute", json={
        "prompt": "{a|b|c} {1|2|3}",
        "mode": "range",
        "offset": 2,
        "limit": 3
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "queued"
    assert data["total_generated"] == 3
    assert len(data["prompts"]) == 3

    # Test sample mode execution
    res_sample = client.post("/generate/matrix/execute", json={
        "prompt": "{a|b|c} {1|2|3}",
        "mode": "sample",
        "sample_size": 4,
        "seed": 42
    })
    assert res_sample.status_code == 200
    data_sample = res_sample.json()
    assert data_sample["status"] == "queued"
    assert data_sample["total_generated"] == 4

def test_matrix_execute_indices_and_prompts():
    res_indices = client.post("/generate/matrix/execute", json={
        "prompt": "{a|b|c} {1|2|3}",
        "mode": "indices",
        "indices": [0, 8]
    })
    assert res_indices.status_code == 200
    data_indices = res_indices.json()
    assert data_indices["status"] == "queued"
    assert data_indices["total_generated"] == 2
    assert data_indices["prompts"] == ["a 1", "c 3"]

    res_prompts = client.post("/generate/matrix/execute", json={
        "prompts": ["custom 1", "custom 2", "custom 3"],
        "limit": 2
    })
    assert res_prompts.status_code == 200
    data_prompts = res_prompts.json()
    assert data_prompts["status"] == "queued"
    assert data_prompts["total_generated"] == 2
    assert data_prompts["prompts"] == ["custom 1", "custom 2"]

