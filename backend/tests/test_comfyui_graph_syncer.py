import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from app.services.comfyui_graph_syncer import ComfyUIGraphSyncer
from app.api.routers.comfyui import router

def test_inspect_workflow_graph():
    syncer = ComfyUIGraphSyncer()
    mock_workflow = {
        "6": {
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "Positive Prompt"},
            "inputs": {"text": "masterpiece prompt", "clip": ["4", 0]}
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "Negative Prompt"},
            "inputs": {"text": "bad quality, blurry", "clip": ["4", 0]}
        },
        "3": {
            "class_type": "KSampler",
            "_meta": {"title": "KSampler"},
            "inputs": {"seed": 42, "steps": 20, "cfg": 7.0}
        }
    }
    inspected = syncer.inspect_graph(mock_workflow)
    assert len(inspected["nodes"]) == 3
    assert inspected["prompt_nodes"][0]["node_id"] == "6"
    assert inspected["prompt_nodes"][1]["node_id"] == "7"
    assert inspected["sampler_nodes"][0]["node_id"] == "3"

def test_inspect_workflow_endpoint():
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/comfyui")
    client = TestClient(app)

    mock_workflow = {
        "6": {
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "Positive Prompt"},
            "inputs": {"text": "masterpiece prompt", "clip": ["4", 0]}
        },
        "3": {
            "class_type": "KSampler",
            "_meta": {"title": "KSampler"},
            "inputs": {"seed": 42, "steps": 20, "cfg": 7.0}
        }
    }

    response = client.post("/api/v1/comfyui/workflow/inspect", json={"workflow": mock_workflow})
    assert response.status_code == 200
    data = response.json()
    assert len(data["nodes"]) == 2
    assert data["prompt_nodes"][0]["node_id"] == "6"
    assert data["sampler_nodes"][0]["node_id"] == "3"
