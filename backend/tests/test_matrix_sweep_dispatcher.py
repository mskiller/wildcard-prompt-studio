import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from main import app
from app.api.routers.comfyui import build_default_krea_sweep_workflow

client = TestClient(app)

def test_execute_sweep_with_seed_strategies():
    mock_workflow = {
        "3": {"inputs": {"seed": 0, "steps": 20, "cfg": 8.0, "sampler_name": "euler"}, "class_type": "KSampler"},
        "6": {"inputs": {"text": ""}, "class_type": "CLIPTextEncode"}
    }
    
    with patch("app.api.routers.comfyui.connector.queue_prompt", new_callable=AsyncMock) as mock_queue:
        mock_queue.return_value = {"prompt_id": "test-sweep", "number": 1}

        # 1. Test Sequential Strategy
        resp_seq = client.post(
            "/api/v1/comfyui/execute-sweep",
            json={
                "workflow": mock_workflow,
                "target_node_id": "6",
                "seed_node_id": "3",
                "prompts": ["prompt 1", "prompt 2", "prompt 3"],
                "seed_strategy": "sequential",
                "base_seed": 5000,
                "steps": 25,
                "cfg": 7.0,
                "sampler_name": "dpmpp_2m"
            }
        )
        assert resp_seq.status_code == 200
        data_seq = resp_seq.json()
        assert data_seq["queued_count"] == 3
        assert mock_queue.call_count == 3
        
        # Check first queued payload has base_seed 5000 and steps 25
        first_call_wf = mock_queue.call_args_list[0][0][0]
        assert first_call_wf["3"]["inputs"]["seed"] == 5000
        assert first_call_wf["3"]["inputs"]["steps"] == 25
        assert first_call_wf["3"]["inputs"]["cfg"] == 7.0
        assert first_call_wf["3"]["inputs"]["sampler_name"] == "dpmpp_2m"
        assert first_call_wf["6"]["inputs"]["text"] == "prompt 1"

        second_call_wf = mock_queue.call_args_list[1][0][0]
        assert second_call_wf["3"]["inputs"]["seed"] == 5001

        # 2. Test Fixed Strategy
        mock_queue.reset_mock()
        resp_fixed = client.post(
            "/api/v1/comfyui/execute-sweep",
            json={
                "workflow": mock_workflow,
                "target_node_id": "6",
                "seed_node_id": "3",
                "prompts": ["prompt A", "prompt B"],
                "seed_strategy": "fixed",
                "base_seed": 9999
            }
        )
        assert resp_fixed.status_code == 200
        assert mock_queue.call_count == 2
        call_0_wf = mock_queue.call_args_list[0][0][0]
        call_1_wf = mock_queue.call_args_list[1][0][0]
        assert call_0_wf["3"]["inputs"]["seed"] == 9999
        assert call_1_wf["3"]["inputs"]["seed"] == 9999

        # 3. Test Random Strategy
        mock_queue.reset_mock()
        with patch("random.randint", return_value=12345678) as mock_rand:
            resp_random = client.post(
                "/api/v1/comfyui/execute-sweep",
                json={
                    "workflow": mock_workflow,
                    "target_node_id": "6",
                    "seed_node_id": "3",
                    "prompts": ["prompt R1", "prompt R2"],
                    "seed_strategy": "random"
                }
            )
            assert resp_random.status_code == 200
            assert mock_queue.call_count == 2
            assert mock_rand.call_count == 2
            rand_call_wf = mock_queue.call_args_list[0][0][0]
            assert rand_call_wf["3"]["inputs"]["seed"] == 12345678

def test_execute_sweep_default_krea2_workflow():
    with patch("app.api.routers.comfyui.connector.queue_prompt", new_callable=AsyncMock) as mock_queue, \
         patch("app.api.routers.comfyui.connector.get_object_info", new_callable=AsyncMock) as mock_obj:
        mock_queue.return_value = {"prompt_id": "krea2-sweep", "number": 100}
        mock_obj.return_value = {
            "UNETLoader": {"input": {"required": {"unet_name": [["Mklan_Kea2_V1.safetensors"]]}}},
            "CLIPLoader": {"input": {"required": {"clip_name": [["qwen3-vl-4b-heretic.safetensors"]]}}},
            "VAELoader": {"input": {"required": {"vae_name": [["qwen_image_vae.safetensors"]]}}}
        }

        resp = client.post(
            "/api/v1/comfyui/execute-sweep",
            json={
                "prompts": ["1woman, testing sweep"],
                "model": "Mklan_Krea28v1.safetensors",
                "clip": "qwen3-vl-4b-heretic.safetensors",
                "vae": "qwen_image_vae.safetensors",
                "sampler_name": "er_sde",
                "scheduler": "beta",
                "steps": 10,
                "cfg": 1.0,
                "base_seed": 42
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["queued_count"] == 1
        mock_queue.assert_called_once()
        queued_wf = mock_queue.call_args[0][0]
        # Verify Krea 2 workflow nodes
        assert queued_wf["1"]["class_type"] == "UNETLoader"
        assert queued_wf["1"]["inputs"]["unet_name"] == "Mklan_Kea2_V1.safetensors"
        assert queued_wf["2"]["class_type"] == "CLIPLoader"
        assert queued_wf["2"]["inputs"]["clip_name"] == "qwen3-vl-4b-heretic.safetensors"
        assert queued_wf["3"]["class_type"] == "VAELoader"
        assert queued_wf["3"]["inputs"]["vae_name"] == "qwen_image_vae.safetensors"
        assert queued_wf["4"]["inputs"]["text"] == "1woman, testing sweep"
        assert queued_wf["7"]["inputs"]["sampler_name"] == "er_sde"
        assert queued_wf["7"]["inputs"]["scheduler"] == "beta"
        assert queued_wf["7"]["inputs"]["steps"] == 10
        assert queued_wf["7"]["inputs"]["cfg"] == 1.0
        assert queued_wf["7"]["inputs"]["seed"] == 42

def test_sync_recent_outputs():
    mock_history = {
        "sweep-pid-99": {
            "prompt": [
                0,
                "client-id",
                {
                    "4": {
                        "class_type": "CLIPTextEncode",
                        "inputs": {"text": "a majestic lion in Savannah"}
                    },
                    "7": {
                        "class_type": "KSampler",
                        "inputs": {
                            "seed": 77777,
                            "steps": 10,
                            "cfg": 1.0,
                            "sampler_name": "er_sde"
                        }
                    }
                }
            ],
            "outputs": {
                "9": {
                    "images": [
                        {"filename": "MatrixSweep_Krea2_00099_.png", "subfolder": "", "type": "output"}
                    ]
                }
            }
        }
    }

    with patch("app.api.routers.comfyui.connector.get_all_history", new_callable=AsyncMock) as mock_hist, \
         patch("app.api.routers.comfyui.connector.get_image", new_callable=AsyncMock) as mock_get_img:
        mock_hist.return_value = mock_history
        mock_get_img.return_value = b"MOCK_PNG_DATA"

        resp = client.post(
            "/api/v1/comfyui/sync-recent-outputs",
            json={"prefix": "MatrixSweep", "limit": 10}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["imported_count"] == 1
        item = data["items"][0]
        assert item["filename"] == "MatrixSweep_Krea2_00099_.png"
        assert item["prompt_content"] == "a majestic lion in Savannah"
        assert item["seed"] == 77777
        assert item["steps"] == 10
        assert item["cfg_scale"] == 1.0


def test_execute_sweep_resolution_parameters():
    with patch("app.api.routers.comfyui.connector.queue_prompt", new_callable=AsyncMock) as mock_queue, \
         patch("app.api.routers.comfyui.connector.get_object_info", new_callable=AsyncMock) as mock_obj:
        mock_queue.return_value = {"prompt_id": "res-sweep", "number": 101}
        mock_obj.return_value = {
            "UNETLoader": {"input": {"required": {"unet_name": [["Mklan_Kea2_V1.safetensors"]]}}},
            "CLIPLoader": {"input": {"required": {"clip_name": [["qwen3-vl-4b-heretic.safetensors"]]}}},
            "VAELoader": {"input": {"required": {"vae_name": [["qwen_image_vae.safetensors"]]}}}
        }

        # 1. Verify default resolution is 896x1152
        resp_def = client.post(
            "/api/v1/comfyui/execute-sweep",
            json={"prompts": ["default resolution prompt"]}
        )
        assert resp_def.status_code == 200
        wf_def = mock_queue.call_args[0][0]
        assert wf_def["6"]["class_type"] == "EmptyLatentImage"
        assert wf_def["6"]["inputs"]["width"] == 896
        assert wf_def["6"]["inputs"]["height"] == 1152

        # 2. Verify custom resolution (e.g. 1024x1024)
        mock_queue.reset_mock()
        resp_custom = client.post(
            "/api/v1/comfyui/execute-sweep",
            json={
                "prompts": ["custom resolution prompt"],
                "width": 1024,
                "height": 1024
            }
        )
        assert resp_custom.status_code == 200
        wf_custom = mock_queue.call_args[0][0]
        assert wf_custom["6"]["inputs"]["width"] == 1024
        assert wf_custom["6"]["inputs"]["height"] == 1024

def test_build_default_krea_sweep_workflow_custom_prefix():
    wf = build_default_krea_sweep_workflow(
        model_name="test_model.safetensors",
        clip_name="test_clip.safetensors",
        vae_name="test_vae.safetensors",
        sampler_name="er_sde",
        scheduler="beta",
        steps=10,
        cfg=1.0,
        seed=42,
        prompt_str="a test prompt",
        filename_prefix="Prompting\\MatrixSweep_Krea2"
    )
    assert "9" in wf
    assert wf["9"]["class_type"] == "SaveImage"
    assert wf["9"]["inputs"]["filename_prefix"] == "Prompting\\MatrixSweep_Krea2"

def test_execute_sweep_with_custom_filename_prefix():
    mock_workflow = {
        "3": {"inputs": {"seed": 0, "steps": 20, "cfg": 8.0, "sampler_name": "euler"}, "class_type": "KSampler"},
        "6": {"inputs": {"text": ""}, "class_type": "CLIPTextEncode"},
        "9": {"inputs": {"filename_prefix": "OriginalPrefix"}, "class_type": "SaveImage"}
    }
    with patch("app.api.routers.comfyui.connector.queue_prompt", new_callable=AsyncMock) as mock_queue:
        mock_queue.return_value = {"prompt_id": "test-sweep", "number": 1}
        payload = {
            "workflow": mock_workflow,
            "target_node_id": "6",
            "seed_node_id": "3",
            "prompts": ["cyberpunk landscape"],
            "filename_prefix": "MySubfolder/MyPrefix",
            "steps": 15,
            "cfg": 2.0
        }
        response = client.post("/api/v1/comfyui/execute-sweep", json=payload)
        assert response.status_code == 200
        assert response.json()["queued_count"] == 1
        assert mock_queue.called
        wf_passed = mock_queue.call_args[0][0]
        assert wf_passed["9"]["inputs"]["filename_prefix"] == "MySubfolder/MyPrefix"


def test_sync_recent_outputs_with_subfolder_prefix():
    history_with_subfolder = {
        "prompt-sub-1": {
            "prompt": [
                0,
                "client-id-sub",
                {
                    "4": {
                        "class_type": "CLIPTextEncode",
                        "inputs": {"text": "prompt inside prompting subfolder"}
                    },
                    "7": {
                        "class_type": "KSampler",
                        "inputs": {
                            "seed": 111,
                            "steps": 10,
                            "cfg": 1.0,
                            "sampler_name": "er_sde"
                        }
                    }
                }
            ],
            "outputs": {
                "9": {
                    "images": [
                        {"filename": "MatrixSweep_Krea2_00001_.png", "subfolder": "Prompting", "type": "output"}
                    ]
                }
            }
        },
        "prompt-unrelated": {
            "prompt": [
                0,
                "client-id-unrelated",
                {
                    "4": {
                        "class_type": "CLIPTextEncode",
                        "inputs": {"text": "unrelated prompt"}
                    }
                }
            ],
            "outputs": {
                "9": {
                    "images": [
                        {"filename": "Unrelated_00001_.png", "subfolder": "OtherFolder", "type": "output"},
                        {"filename": None, "subfolder": "OtherFolder", "type": "output"}
                    ]
                }
            }
        }
    }
    with patch("app.api.routers.comfyui.connector.get_all_history", new_callable=AsyncMock) as mock_hist, \
         patch("app.api.routers.comfyui.connector.get_image", new_callable=AsyncMock) as mock_get_img:
        mock_hist.return_value = history_with_subfolder
        mock_get_img.return_value = b"FAKE_SUBFOLDER_IMAGE_BYTES"

        # Case 1: Match by full prefix with backslash
        res1 = client.post("/api/v1/comfyui/sync-recent-outputs", json={"prefix": "Prompting\\MatrixSweep_Krea2"})
        assert res1.status_code == 200
        assert res1.json()["imported_count"] == 1
        assert res1.json()["items"][0]["filename"] == "MatrixSweep_Krea2_00001_.png"

        # Case 2: Match by full prefix with forward slash
        res2 = client.post("/api/v1/comfyui/sync-recent-outputs", json={"prefix": "Prompting/MatrixSweep_Krea2"})
        assert res2.status_code == 200
        assert res2.json()["imported_count"] == 1

        # Case 3: Match by default "MatrixSweep"
        res3 = client.post("/api/v1/comfyui/sync-recent-outputs", json={"prefix": "MatrixSweep"})
        assert res3.status_code == 200
        assert res3.json()["imported_count"] == 1

        # Case 4: Match by subfolder alone
        res4 = client.post("/api/v1/comfyui/sync-recent-outputs", json={"prefix": "Prompting"})
        assert res4.status_code == 200
        assert res4.json()["imported_count"] == 1

        # Case 5: Querying with trailing slash (forward slash) imports only 1 item (no universal match bug)
        res5 = client.post("/api/v1/comfyui/sync-recent-outputs", json={"prefix": "Prompting/"})
        assert res5.status_code == 200
        assert res5.json()["imported_count"] == 1

        # Case 6: Querying with trailing slash (backslash) imports only 1 item
        res6 = client.post("/api/v1/comfyui/sync-recent-outputs", json={"prefix": "Prompting\\"})
        assert res6.status_code == 200
        assert res6.json()["imported_count"] == 1

        # Case 7: Querying with NonExistentFolder imports 0 items
        res7 = client.post("/api/v1/comfyui/sync-recent-outputs", json={"prefix": "NonExistentFolder"})
        assert res7.status_code == 200
        assert res7.json()["imported_count"] == 0


