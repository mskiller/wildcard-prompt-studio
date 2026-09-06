import os
import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.api.routers.comfyui import _send_image_to_discord, background_poll_sweep_prompts

@pytest.mark.asyncio
async def test_send_image_to_discord_retry_on_429(tmp_path):
    """Verify _send_image_to_discord retries and succeeds when hitting 429 rate limit."""
    dummy_img = tmp_path / "test_001.png"
    dummy_img.write_bytes(b"\x89PNG\r\n\x1a\nfake_image_content")

    resp_429 = MagicMock()
    resp_429.status_code = 429
    resp_429.headers = {"Retry-After": "0.01"}
    resp_429.json.return_value = {"message": "You are being rate limited.", "retry_after": 0.01}

    resp_200 = MagicMock()
    resp_200.status_code = 200

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=[resp_429, resp_200])

    with patch("httpx.AsyncClient") as mock_client_cls, \
         patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        success = await _send_image_to_discord(
            image_path=str(dummy_img),
            filename="test_001.png",
            prompt_text="a lovely test prompt",
            webhook_url_override="https://discord.com/api/webhooks/dummy",
        )

        assert success is True
        assert mock_client.post.call_count == 2
        mock_sleep.assert_called()

@pytest.mark.asyncio
async def test_send_image_to_discord_retry_on_5xx(tmp_path):
    """Verify _send_image_to_discord retries and succeeds on 502/503 server errors."""
    dummy_img = tmp_path / "test_502.png"
    dummy_img.write_bytes(b"\x89PNG\r\n\x1a\nfake_image_content")

    resp_502 = MagicMock()
    resp_502.status_code = 502
    resp_502.text = "Bad Gateway"

    resp_200 = MagicMock()
    resp_200.status_code = 200

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=[resp_502, resp_200])

    with patch("httpx.AsyncClient") as mock_client_cls, \
         patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        success = await _send_image_to_discord(
            image_path=str(dummy_img),
            filename="test_502.png",
            prompt_text="server retry prompt",
            webhook_url_override="https://discord.com/api/webhooks/dummy",
        )

        assert success is True
        assert mock_client.post.call_count == 2
        mock_sleep.assert_called()

@pytest.mark.asyncio
async def test_background_poll_sweep_handles_large_batch():
    """Verify background_poll_sweep_prompts can process 30 items without stopping at 20 or timing out."""
    pids = [f"sweep-job-{i}" for i in range(30)]

    mock_history = {}
    for i, pid in enumerate(pids):
        mock_history[pid] = {
            "prompt": [0, "cid", {"4": {"class_type": "CLIPTextEncode", "inputs": {"text": f"prompt {i}"}}}],
            "outputs": {
                "9": {
                    "images": [{"filename": f"Sweep_img_{i:03d}.png", "subfolder": "", "type": "output"}]
                }
            }
        }

    with patch("app.api.routers.comfyui.connector.get_all_history", new_callable=AsyncMock) as mock_all_hist, \
         patch("app.api.routers.comfyui.process_and_save_comfy_output", new_callable=AsyncMock) as mock_save, \
         patch("app.api.routers.comfyui._send_image_to_discord", new_callable=AsyncMock) as mock_discord, \
         patch("app.api.routers.comfyui.os.path.exists", return_value=True), \
         patch("asyncio.sleep", new_callable=AsyncMock):

        mock_all_hist.return_value = mock_history
        mock_save.side_effect = lambda pid, job_info, db, base_url: [{
            "filename": job_info["outputs"]["9"]["images"][0]["filename"],
            "prompt_content": f"prompt for {pid}"
        }]
        mock_discord.return_value = True

        await background_poll_sweep_prompts(
            prompt_ids=pids,
            base_url="http://localhost:8188",
            send_to_discord=True,
            discord_webhook_url="https://discord.com/api/webhooks/dummy",
            allow_in_test=True,
        )

        assert mock_save.call_count == 30
        assert mock_discord.call_count == 30

def test_get_discord_webhook_url_from_config(tmp_path):
    """Verify _get_discord_webhook_url reads from config file when environment variable is not set."""
    from app.api.routers.comfyui import _get_discord_webhook_url, _DISCORD_CONFIG_CANDIDATE_PATHS

    dummy_cfg = tmp_path / "discord_config.ini"
    dummy_cfg.write_text("[Discord]\nwebhook_url = https://discord.com/api/webhooks/test-123/token\n", encoding="utf-8")

    orig_env = os.environ.pop("DISCORD_WEBHOOK_URL", None)
    _DISCORD_CONFIG_CANDIDATE_PATHS.insert(0, str(dummy_cfg))
    try:
        url = _get_discord_webhook_url()
        assert url == "https://discord.com/api/webhooks/test-123/token"
    finally:
        _DISCORD_CONFIG_CANDIDATE_PATHS.remove(str(dummy_cfg))
        if orig_env:
            os.environ["DISCORD_WEBHOOK_URL"] = orig_env

@pytest.mark.asyncio
async def test_integration_test_discord_endpoint():
    """Verify test_integration_connection handles discord provider correctly."""
    from app.api.routers.ai import test_integration_connection, ConnectionTestRequest

    resp_200 = MagicMock()
    resp_200.status_code = 200
    resp_200.json.return_value = {"name": "TestHook", "channel_id": "999888777"}

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=resp_200)

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        res = await test_integration_connection(
            ConnectionTestRequest(provider="discord", url="https://discord.com/api/webhooks/123/abc")
        )
        assert res["status"] == "ok"
        assert res["provider"] == "discord"
        assert res["name"] == "TestHook"


