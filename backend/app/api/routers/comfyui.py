import copy
import json
import asyncio
import logging
import random
import os
import aiofiles
import configparser
import httpx
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Response, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.services.comfyui_connector import ComfyUIConnector, listen_comfyui_websocket
from app.services.comfyui_ws import comfyui_ws_manager
from app.services.comfyui_graph_syncer import ComfyUIGraphSyncer
from app.dependencies import get_db
from app.database import SessionLocal
from app.models.image import Image
from app.models.prompt import Prompt
from app.api.routers.images import STATIC_IMAGES_DIR
from app.services.image_metadata import extract_metadata_from_png

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Discord webhook helpers — auto-discovers from workspace, env, or ComfyUI config
# ---------------------------------------------------------------------------

_DISCORD_CONFIG_CANDIDATE_PATHS = [
    os.getenv("DISCORD_CONFIG_PATH", ""),
    "/workspace/discord_config.ini",
    "/workspace/config.ini",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "workspace", "discord_config.ini")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "workspace", "discord_config.ini")),
    r"E:\Comfy\ComfyUI\custom_nodes\ComfyUI-SendToDiscord\config.ini",
    r"C:\Comfy\ComfyUI\custom_nodes\ComfyUI-SendToDiscord\config.ini",
    "/mnt/e/Comfy/ComfyUI/custom_nodes/ComfyUI-SendToDiscord/config.ini",
    "/mnt/c/Comfy/ComfyUI/custom_nodes/ComfyUI-SendToDiscord/config.ini",
    "/config/discord_config.ini",
    "/config/discord.ini",
]


def _get_discord_webhook_url() -> Optional[str]:
    """Read the Discord webhook URL from environment variable, workspace config, or ComfyUI config.ini."""
    env_url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    if env_url and "your-webhook-url-here" not in env_url:
        return env_url

    for path in _DISCORD_CONFIG_CANDIDATE_PATHS:
        if not path:
            continue
        try:
            if os.path.exists(path):
                cfg = configparser.ConfigParser()
                cfg.read(path, encoding="utf-8")
                url = cfg.get("Discord", "webhook_url", fallback="").strip()
                if url and "your-webhook-url-here" not in url:
                    return url
        except Exception as e:
            logger.debug(f"Could not read Discord config from {path}: {e}")

    # Check for .env files
    for env_file in ("/workspace/.env", ".env", "../.env", "../../.env"):
        try:
            if os.path.exists(env_file):
                with open(env_file, "r", encoding="utf-8") as ef:
                    for line in ef:
                        line = line.strip()
                        if line.startswith("DISCORD_WEBHOOK_URL="):
                            url = line.split("=", 1)[1].strip().strip('"').strip("'")
                            if url and "your-webhook-url-here" not in url:
                                return url
        except Exception:
            pass

    return None


async def _send_image_to_discord(
    image_path: str,
    filename: str,
    prompt_text: str = "",
    webhook_url_override: Optional[str] = None,
    max_retries: int = 5,
) -> bool:
    """Send a downloaded sweep image (+ prompt formatted in message and txt) to Discord via webhook with rate-limit and retry handling."""
    webhook_url = webhook_url_override or _get_discord_webhook_url()
    if not webhook_url:
        logger.warning("Discord webhook URL not configured — skipping Discord send.")
        return False

    try:
        with open(image_path, "rb") as f:
            img_data = f.read()
    except Exception as e:
        logger.error(f"Could not read image {image_path} for Discord dispatch: {e}")
        return False

    clean_prompt = prompt_text.strip() if prompt_text else ""
    display_prompt = clean_prompt[:1800] + ("..." if len(clean_prompt) > 1800 else "")

    for attempt in range(1, max_retries + 1):
        try:
            files: dict = {
                "file": (filename, img_data, "image/png"),
            }
            if clean_prompt:
                files["file1"] = ("prompt.txt", clean_prompt.encode("utf-8"), "text/plain")

            data: dict = {}
            if clean_prompt:
                data["payload_json"] = json.dumps({
                    "content": f"**Prompt:**\n```\n{display_prompt}\n```"
                })

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(webhook_url, files=files, data=data if data else None)

            if response.status_code in (200, 204):
                logger.info(f"Discord: sent {filename} successfully (attempt {attempt}).")
                return True

            if response.status_code == 429:
                retry_after = 2.0
                try:
                    if "Retry-After" in response.headers:
                        retry_after = float(response.headers["Retry-After"])
                    else:
                        resp_json = response.json()
                        if isinstance(resp_json, dict) and "retry_after" in resp_json:
                            retry_after = float(resp_json["retry_after"])
                except Exception:
                    pass
                wait_time = max(1.0, min(retry_after + 0.5, 30.0))
                logger.warning(
                    f"Discord rate limit (429) on {filename} (attempt {attempt}/{max_retries}). "
                    f"Waiting {wait_time:.2f}s before retry..."
                )
                await asyncio.sleep(wait_time)
                continue

            if response.status_code == 500 or response.status_code in (502, 503, 504):
                wait_time = min(15.0, 1.5 ** attempt)
                logger.warning(
                    f"Discord server error {response.status_code} for {filename} (attempt {attempt}/{max_retries}). "
                    f"Retrying in {wait_time:.1f}s..."
                )
                await asyncio.sleep(wait_time)
                continue

            # Handle Discord AutoMod explicit content filter (code 20009)
            if response.status_code == 400 and "20009" in response.text:
                logger.warning(
                    f"Discord AutoMod flagged {filename} (code 20009). Retrying as spoiler attachment..."
                )
                spoiler_files = {
                    "file": (f"SPOILER_{filename}", img_data, "image/png"),
                }
                if clean_prompt:
                    spoiler_files["file1"] = ("prompt.txt", clean_prompt.encode("utf-8"), "text/plain")
                try:
                    async with httpx.AsyncClient(timeout=30) as client:
                        resp_sp = await client.post(webhook_url, files=spoiler_files, data=data if data else None)
                    if resp_sp.status_code in (200, 204):
                        logger.info(f"Discord: sent SPOILER_{filename} successfully after AutoMod retry.")
                        return True
                except Exception as sp_err:
                    logger.warning(f"Discord spoiler retry error: {sp_err}")

                # If Discord still rejects the image due to channel age restriction, post the prompt text
                try:
                    notice_data = {
                        "payload_json": json.dumps({
                            "content": (
                                f"⚠️ **Discord Notice:** Image `{filename}` was filtered by Discord AutoMod (Code 20009).\n"
                                f"*(Please set this Discord channel to **Age-Restricted (NSFW)** in channel settings to receive sensitive images.)*\n\n"
                                f"**Prompt:**\n```\n{clean_prompt[:1600]}\n```"
                            )
                        })
                    }
                    async with httpx.AsyncClient(timeout=30) as client:
                        await client.post(webhook_url, data=notice_data)
                except Exception:
                    pass
                return False

            logger.warning(f"Discord webhook returned {response.status_code}: {response.text[:200]}")
            return False

        except (httpx.TimeoutException, httpx.NetworkError, httpx.TransportError) as net_err:
            wait_time = min(15.0, 1.5 ** attempt)
            logger.warning(
                f"Discord network error for {filename} (attempt {attempt}/{max_retries}): {net_err}. "
                f"Retrying in {wait_time:.1f}s..."
            )
            await asyncio.sleep(wait_time)
        except Exception as e:
            logger.error(f"Discord send error for {filename}: {e}")
            return False

    logger.error(f"Failed to send {filename} to Discord after {max_retries} attempts.")
    return False

router = APIRouter()
connector = ComfyUIConnector()
graph_syncer = ComfyUIGraphSyncer()

class PromptRequest(BaseModel):
    prompt: Dict[str, Any]
    base_url: Optional[str] = None
    client_id: Optional[str] = None

@router.post("/queue")
async def queue_prompt(req: PromptRequest):
    try:
        res = await connector.queue_prompt(req.prompt, base_url=req.base_url, client_id=req.client_id)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{prompt_id}")
async def get_history(prompt_id: str, base_url: Optional[str] = None):
    try:
        return await connector.get_history(prompt_id, base_url=base_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/image/{filename}")
async def get_image(filename: str, folder_type: str = "output", subfolder: str = "", base_url: Optional[str] = None):
    try:
        content = await connector.get_image(filename, folder_type=folder_type, subfolder=subfolder, base_url=base_url)
        return Response(content=content, media_type="image/png")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/view")
async def view_image(filename: str, type: str = "output", subfolder: str = "", base_url: Optional[str] = None):
    try:
        content = await connector.get_image(filename, folder_type=type, subfolder=subfolder, base_url=base_url)
        return Response(content=content, media_type="image/png")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/object_info")
async def get_object_info(base_url: Optional[str] = None):
    try:
        return await connector.get_object_info(base_url=base_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/options")
async def get_comfyui_options(
    comfyui_url: Optional[str] = None
):
    from app.api.routers.generate import get_generation_options
    return await get_generation_options(comfyui_url=comfyui_url, connector=connector)

@router.websocket("/ws/{client_id}")
async def comfyui_websocket_endpoint(websocket: WebSocket, client_id: str, base_url: Optional[str] = None):
    await comfyui_ws_manager.connect(websocket, client_id)

    async def on_comfyui_message(msg: dict):
        await comfyui_ws_manager.proxy_message(client_id, msg)

    comfy_url = base_url or connector.default_url
    listener_task = asyncio.create_task(
        listen_comfyui_websocket(comfy_url, client_id, on_comfyui_message)
    )

    try:
        while True:
            data = await websocket.receive_text()
            try:
                parsed = json.loads(data)
                await comfyui_ws_manager.send_personal_message({"type": "ack", "data": parsed}, client_id)
            except Exception:
                await comfyui_ws_manager.send_personal_message({"type": "ack", "data": data}, client_id)
    except WebSocketDisconnect:
        logger.info(f"WebSocket client {client_id} disconnected.")
    except Exception as e:
        logger.error(f"Error in WebSocket endpoint for client {client_id}: {e}")
    finally:
        listener_task.cancel()
        try:
            await listener_task
        except (asyncio.CancelledError, Exception):
            pass
        comfyui_ws_manager.disconnect(client_id)

def resolve_comfy_asset(name: Optional[str], candidates: List[str], fallback: str) -> str:
    if not name:
        return fallback
    if name in candidates:
        return name
    # Exact basename match
    clean_target = name.lower().replace("\\", "/").split("/")[-1]
    for c in candidates:
        c_clean = c.lower().replace("\\", "/").split("/")[-1]
        if clean_target == c_clean:
            return c
    # Stem / substring match
    for c in candidates:
        c_clean = c.lower().replace("\\", "/").split("/")[-1]
        if clean_target in c_clean or c_clean in clean_target:
            return c
    # Special alias rule for Krea2 / Kea2 model names
    if "krea2" in clean_target or "kea2" in clean_target:
        for c in candidates:
            cl = c.lower()
            if "kea2" in cl or "krea2" in cl:
                return c
    return candidates[0] if candidates else name

def build_default_krea_sweep_workflow(
    model_name: str,
    clip_name: str,
    vae_name: str,
    sampler_name: str,
    scheduler: str,
    steps: int,
    cfg: float,
    seed: int,
    prompt_str: str,
    is_unet: bool = True,
    width: int = 896,
    height: int = 1152
) -> Dict[str, Any]:
    wf: Dict[str, Any] = {}
    if is_unet:
        wf["1"] = {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": model_name,
                "weight_dtype": "default"
            }
        }
    else:
        wf["1"] = {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": model_name
            }
        }

    wf["2"] = {
        "class_type": "CLIPLoader",
        "inputs": {
            "clip_name": clip_name,
            "type": "krea2",
            "device": "default"
        }
    }
    wf["3"] = {
        "class_type": "VAELoader",
        "inputs": {
            "vae_name": vae_name
        }
    }
    wf["4"] = {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "text": prompt_str,
            "clip": ["2", 0]
        }
    }
    wf["5"] = {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "text": "",
            "clip": ["2", 0]
        }
    }
    wf["6"] = {
        "class_type": "EmptyLatentImage",
        "inputs": {
            "width": width,
            "height": height,
            "batch_size": 1
        }
    }
    wf["7"] = {
        "class_type": "KSampler",
        "inputs": {
            "model": ["1", 0],
            "positive": ["4", 0],
            "negative": ["5", 0],
            "latent_image": ["6", 0],
            "seed": seed,
            "steps": steps,
            "cfg": cfg,
            "sampler_name": sampler_name,
            "scheduler": scheduler,
            "denoise": 1.0
        }
    }
    wf["8"] = {
        "class_type": "VAEDecode",
        "inputs": {
            "samples": ["7", 0],
            "vae": ["3", 0]
        }
    }
    wf["9"] = {
        "class_type": "SaveImage",
        "inputs": {
            "filename_prefix": "MatrixSweep_Krea2",
            "images": ["8", 0]
        }
    }
    return wf

class SweepExecutionRequest(BaseModel):
    workflow: Optional[Dict[str, Any]] = None
    target_node_id: Optional[str] = None
    seed_node_id: Optional[str] = None
    prompts: List[Any]
    base_url: Optional[str] = None
    client_id: Optional[str] = None
    seed_strategy: Optional[str] = "sequential"
    base_seed: Optional[int] = 42
    steps: Optional[int] = 10
    cfg: Optional[float] = 1.0
    sampler_name: Optional[str] = "er_sde"
    scheduler: Optional[str] = "beta"
    model: Optional[str] = "Mklan_Kea2_V1.safetensors"
    clip: Optional[str] = "qwen3-vl-4b-heretic.safetensors"
    vae: Optional[str] = "qwen_image_vae.safetensors"
    width: Optional[int] = 896
    height: Optional[int] = 1152
    send_to_discord: Optional[bool] = False
    discord_webhook_url: Optional[str] = None

@router.post("/execute-sweep")
async def execute_sweep(req: SweepExecutionRequest, background_tasks: BackgroundTasks):
    try:
        results = []
        has_custom_workflow = bool(
            req.workflow and
            req.target_node_id and
            req.target_node_id in req.workflow
        )

        resolved_model = req.model or "Mklan_Kea2_V1.safetensors"
        resolved_clip = req.clip or "qwen3-vl-4b-heretic.safetensors"
        resolved_vae = req.vae or "qwen_image_vae.safetensors"
        is_unet = True

        if not has_custom_workflow:
            obj_info = {}
            try:
                obj_info = await connector.get_object_info(base_url=req.base_url)
            except Exception:
                pass

            unets = obj_info.get("UNETLoader", {}).get("input", {}).get("required", {}).get("unet_name", [[]])[0] if obj_info else []
            ckpts = obj_info.get("CheckpointLoaderSimple", {}).get("input", {}).get("required", {}).get("ckpt_name", [[]])[0] if obj_info else []
            clips = obj_info.get("CLIPLoader", {}).get("input", {}).get("required", {}).get("clip_name", [[]])[0] if obj_info else []
            vaes = obj_info.get("VAELoader", {}).get("input", {}).get("required", {}).get("vae_name", [[]])[0] if obj_info else []

            all_models = unets + ckpts
            resolved_model = resolve_comfy_asset(req.model, all_models, "Mklan_Kea2_V1.safetensors")
            resolved_clip = resolve_comfy_asset(req.clip, clips, "qwen3-vl-4b-heretic.safetensors")
            resolved_vae = resolve_comfy_asset(req.vae, vaes, "qwen_image_vae.safetensors")
            is_unet = (resolved_model in unets) or ("kea" in resolved_model.lower()) or ("unet" in resolved_model.lower()) or (resolved_model not in ckpts)

        for idx, prompt_str in enumerate(req.prompts):
            base = req.base_seed if req.base_seed is not None else 42
            if req.seed_strategy == "fixed":
                seed = base
            elif req.seed_strategy == "random":
                seed = random.randint(1, 2147483647)
            else:
                seed = base + idx

            if has_custom_workflow:
                wf_copy = copy.deepcopy(req.workflow)
                if req.target_node_id and req.target_node_id in wf_copy:
                    node = wf_copy.get(req.target_node_id, {})
                    if isinstance(node, dict):
                        if "inputs" not in node or not isinstance(node["inputs"], dict):
                            node["inputs"] = {}
                        wf_copy[req.target_node_id]["inputs"]["text"] = str(prompt_str)
                if req.seed_node_id and req.seed_node_id in wf_copy:
                    seed_node = wf_copy.get(req.seed_node_id, {})
                    if isinstance(seed_node, dict):
                        if "inputs" not in seed_node or not isinstance(seed_node["inputs"], dict):
                            seed_node["inputs"] = {}
                        inputs = seed_node["inputs"]
                        inputs["seed"] = seed
                        if req.steps is not None:
                            inputs["steps"] = req.steps
                        if req.cfg is not None:
                            inputs["cfg"] = req.cfg
                        if req.sampler_name is not None:
                            inputs["sampler_name"] = req.sampler_name
                        if req.scheduler is not None:
                            inputs["scheduler"] = req.scheduler
                # Update EmptyLatentImage width/height if present in custom workflow
                if req.width is not None or req.height is not None:
                    for n_id, n_data in wf_copy.items():
                        if isinstance(n_data, dict) and n_data.get("class_type") == "EmptyLatentImage":
                            if "inputs" in n_data and isinstance(n_data["inputs"], dict):
                                if req.width is not None:
                                    n_data["inputs"]["width"] = req.width
                                if req.height is not None:
                                    n_data["inputs"]["height"] = req.height
            else:
                wf_copy = build_default_krea_sweep_workflow(
                    model_name=resolved_model,
                    clip_name=resolved_clip,
                    vae_name=resolved_vae,
                    sampler_name=req.sampler_name or "er_sde",
                    scheduler=req.scheduler or "beta",
                    steps=req.steps if req.steps is not None else 10,
                    cfg=req.cfg if req.cfg is not None else 1.0,
                    seed=seed,
                    prompt_str=str(prompt_str),
                    is_unet=is_unet,
                    width=req.width if req.width is not None else 896,
                    height=req.height if req.height is not None else 1152
                )

            res = await connector.queue_prompt(wf_copy, base_url=req.base_url, client_id=req.client_id)
            results.append(res)

        queued_pids = [r["prompt_id"] for r in results if isinstance(r, dict) and "prompt_id" in r]
        if queued_pids:
            background_tasks.add_task(
                background_poll_sweep_prompts,
                queued_pids,
                req.base_url,
                bool(req.send_to_discord),
                req.discord_webhook_url or None,
            )

        return {
            "queued_count": len(results),
            "job_results": results,
            "prompt_ids": queued_pids
        }
    except Exception as e:
        logger.error(f"Error executing sweep: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_and_save_comfy_output(
    prompt_id: str,
    job_info: Dict[str, Any],
    db: Session,
    base_url: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Extracts output images from a completed ComfyUI job, downloads them, and persists to DB."""
    outputs = job_info.get("outputs", {})
    prompt_tuple = job_info.get("prompt", [])
    prompt_dict = prompt_tuple[2] if len(prompt_tuple) > 2 and isinstance(prompt_tuple[2], dict) else {}

    # Extract positive prompt text
    pos_text = ""
    for nid in ("4", "6", "positive"):
        if nid in prompt_dict:
            t = prompt_dict[nid].get("inputs", {}).get("text", "")
            if t:
                pos_text = t
                break

    if not pos_text:
        for nid, nval in prompt_dict.items():
            if isinstance(nval, dict) and nval.get("class_type") == "CLIPTextEncode":
                t = nval.get("inputs", {}).get("text", "")
                if t:
                    pos_text = t
                    break

    # Extract sampling parameters
    seed = None
    steps = None
    cfg = None
    sampler_name = None
    for nid, nval in prompt_dict.items():
        if isinstance(nval, dict) and "KSampler" in nval.get("class_type", ""):
            inputs = nval.get("inputs", {})
            seed = inputs.get("seed")
            steps = inputs.get("steps")
            cfg = inputs.get("cfg")
            sampler_name = inputs.get("sampler_name")
            break

    saved_items = []
    for nid, out in outputs.items():
        if isinstance(out, dict) and "images" in out:
            for im in out["images"]:
                fn = im.get("filename")
                if not fn:
                    continue
                subfolder = im.get("subfolder", "")
                folder_type = im.get("type", "output")

                # Cache image locally in STATIC_IMAGES_DIR
                local_path = os.path.join(STATIC_IMAGES_DIR, fn)
                if not os.path.exists(local_path):
                    try:
                        img_bytes = await connector.get_image(
                            fn, folder_type=folder_type, subfolder=subfolder, base_url=base_url
                        )
                        os.makedirs(STATIC_IMAGES_DIR, exist_ok=True)
                        async with aiofiles.open(local_path, "wb") as f:
                            await f.write(img_bytes)
                    except Exception as e:
                        logger.warning(f"Could not download {fn} from ComfyUI: {e}")

                # If prompt text or sampling parameters are missing, attempt fallback extraction from local PNG
                img_w = 896
                img_h = 1152
                if os.path.exists(local_path):
                    meta = extract_metadata_from_png(local_path)
                    if not pos_text and meta.get("prompt_text"):
                        pos_text = meta["prompt_text"]
                    if seed is None and meta.get("seed") is not None:
                        seed = meta["seed"]
                    if steps is None and meta.get("steps") is not None:
                        steps = meta["steps"]
                    if cfg is None and meta.get("cfg") is not None:
                        cfg = meta["cfg"]
                    if not sampler_name and meta.get("sampler_name"):
                        sampler_name = meta["sampler_name"]
                    if meta.get("width"):
                        img_w = meta["width"]
                    if meta.get("height"):
                        img_h = meta["height"]

                # Find or create DB Image record
                db_img = db.query(Image).filter(Image.filename == fn).first()
                prompt_record = None
                if pos_text:
                    prompt_record = db.query(Prompt).filter(Prompt.content == pos_text).first()
                    if not prompt_record:
                        prompt_record = Prompt(name=pos_text[:32].strip(), content=pos_text)
                        db.add(prompt_record)
                        try:
                            db.commit()
                            db.refresh(prompt_record)
                        except Exception:
                            db.rollback()
                            prompt_record = db.query(Prompt).filter(Prompt.content == pos_text).first()

                if not db_img:
                    db_img = Image(
                        filename=fn,
                        prompt_id=prompt_record.id if prompt_record else None,
                        seed=seed,
                        cfg_scale=float(cfg) if cfg is not None else None,
                        steps=int(steps) if steps is not None else None,
                        sampler_name=sampler_name,
                        width=img_w,
                        height=img_h,
                        comfy_workflow_id=prompt_id
                    )
                    db.add(db_img)
                    try:
                        db.commit()
                        db.refresh(db_img)
                    except Exception:
                        db.rollback()
                        db_img = db.query(Image).filter(Image.filename == fn).first()
                else:
                    # Update existing record if missing prompt or parameters
                    updated = False
                    if prompt_record and not db_img.prompt_id:
                        db_img.prompt_id = prompt_record.id
                        updated = True
                    if seed is not None and db_img.seed is None:
                        db_img.seed = seed
                        updated = True
                    if steps is not None and db_img.steps is None:
                        db_img.steps = steps
                        updated = True
                    if cfg is not None and db_img.cfg_scale is None:
                        db_img.cfg_scale = float(cfg)
                        updated = True
                    if sampler_name and not db_img.sampler_name:
                        db_img.sampler_name = sampler_name
                        updated = True
                    if prompt_id and not db_img.comfy_workflow_id:
                        db_img.comfy_workflow_id = prompt_id
                        updated = True
                    if img_w and (not db_img.width or db_img.width == 1024):
                        db_img.width = img_w
                        updated = True
                    if img_h and (not db_img.height or db_img.height == 1024):
                        db_img.height = img_h
                        updated = True
                    if updated:
                        try:
                            db.commit()
                            db.refresh(db_img)
                        except Exception:
                            db.rollback()

                saved_items.append({
                    "id": db_img.id if db_img else None,
                    "filename": fn,
                    "prompt_content": pos_text,
                    "seed": seed,
                    "steps": steps,
                    "cfg_scale": cfg,
                    "sampler_name": sampler_name,
                    "url": f"/static/images/{fn}"
                })
    return saved_items

async def background_poll_sweep_prompts(
    prompt_ids: List[str],
    base_url: Optional[str] = None,
    send_to_discord: bool = False,
    discord_webhook_url: Optional[str] = None,
    allow_in_test: bool = False,
):
    """Monitors queued sweep prompt IDs until completion and saves images to DB/storage."""
    if os.environ.get("PYTEST_CURRENT_TEST") and not allow_in_test:
        return

    real_pids = [
        p for p in prompt_ids 
        if p and (allow_in_test or not any(str(p).startswith(prefix) for prefix in ("test-", "mock-", "krea2-", "dummy-", "p-")))
    ]
    if not real_pids:
        return

    pending = set(real_pids)
    # Dynamic timeout: scale to allow full batch completion (minimum 2 hours, or 5 minutes per prompt)
    max_total_seconds = max(7200, len(real_pids) * 300)
    # Idle timeout: 10 minutes without any completed output before giving up
    idle_timeout = 600
    start_time = asyncio.get_event_loop().time()
    last_progress_time = start_time
    consecutive_poll_errors = 0

    while pending:
        now = asyncio.get_event_loop().time()
        if (now - start_time) > max_total_seconds:
            logger.warning(
                f"Sweep background poll reached total timeout ({max_total_seconds}s) with {len(pending)} prompts still pending."
            )
            break
        if (now - last_progress_time) > idle_timeout:
            logger.warning(
                f"Sweep background poll idle for {idle_timeout}s without progress. Exiting with {len(pending)} prompts still pending."
            )
            break

        await asyncio.sleep(2.0)

        # 1. Fetch history from ComfyUI (batch check first, fallback to queue-head check)
        completed_in_batch: Dict[str, Any] = {}
        try:
            fetch_limit = max(50, min(len(real_pids) * 2, 250))
            all_hist = await connector.get_all_history(max_items=fetch_limit, base_url=base_url)
            if isinstance(all_hist, dict):
                for pid in list(pending):
                    if pid in all_hist:
                        completed_in_batch[pid] = all_hist[pid]
            consecutive_poll_errors = 0
        except Exception as e:
            logger.debug(f"get_all_history check in sweep poller: {e}")
            try:
                # Check up to 3 oldest pending PIDs individually
                check_pids = [p for p in real_pids if p in pending][:3]
                for pid in check_pids:
                    hist_single = await connector.get_history(pid, base_url=base_url)
                    if isinstance(hist_single, dict) and pid in hist_single:
                        completed_in_batch[pid] = hist_single[pid]
                consecutive_poll_errors = 0
            except Exception as e_single:
                consecutive_poll_errors += 1
                logger.debug(f"Sweep background poll error ({consecutive_poll_errors}): {e_single}")
                if consecutive_poll_errors > 30:
                    await asyncio.sleep(min(10.0, 1.0 * consecutive_poll_errors))
                continue

        if not completed_in_batch:
            continue

        # 2. Process and save any newly completed jobs into the database
        images_to_send_discord: List[Dict[str, str]] = []
        db = SessionLocal()
        try:
            for pid, job_info in completed_in_batch.items():
                try:
                    if job_info.get("outputs"):
                        saved = await process_and_save_comfy_output(pid, job_info, db, base_url=base_url)
                        pending.discard(pid)
                        last_progress_time = asyncio.get_event_loop().time()

                        if send_to_discord and saved:
                            for item in saved:
                                fn = item.get("filename", "")
                                prompt_txt = item.get("prompt_content", "")
                                if fn:
                                    images_to_send_discord.append({
                                        "filename": fn,
                                        "prompt_content": prompt_txt,
                                    })
                    else:
                        # Job is in ComfyUI history but has no outputs (e.g. error or cancelled)
                        status = job_info.get("status", {})
                        if status.get("completed") is True or status.get("status_str") in ("error", "cancelled"):
                            logger.info(f"ComfyUI prompt {pid} completed without image outputs (status={status}).")
                            pending.discard(pid)
                            last_progress_time = asyncio.get_event_loop().time()
                except Exception as proc_err:
                    logger.warning(f"Error processing completed output for prompt {pid}: {proc_err}")
        finally:
            db.close()

        # 3. Send images to Discord outside DB session to avoid holding DB connections
        if send_to_discord and images_to_send_discord:
            for img_info in images_to_send_discord:
                fn = img_info["filename"]
                prompt_txt = img_info["prompt_content"]
                local_path = os.path.join(STATIC_IMAGES_DIR, fn)
                if os.path.exists(local_path):
                    await _send_image_to_discord(
                        local_path,
                        fn,
                        prompt_txt,
                        webhook_url_override=discord_webhook_url,
                    )
                    # Courtesy delay between Discord webhook posts to prevent rate-limit bursts
                    await asyncio.sleep(0.5)

class SyncOutputsRequest(BaseModel):
    prefix: Optional[str] = "MatrixSweep"
    limit: Optional[int] = 50
    base_url: Optional[str] = None

@router.post("/sync-recent-outputs")
async def sync_recent_outputs(req: Optional[SyncOutputsRequest] = None, db: Session = Depends(get_db)):
    limit = req.limit if req and req.limit else 50
    prefix = req.prefix if req and req.prefix is not None else "MatrixSweep"
    base_url = req.base_url if req else None

    try:
        history = await connector.get_all_history(max_items=limit, base_url=base_url)
    except Exception as e:
        logger.error(f"Failed to fetch ComfyUI history for sync: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch ComfyUI history: {str(e)}")

    all_saved = []
    for pid, data in history.items():
        outputs = data.get("outputs", {})
        has_match = False
        for nid, out in outputs.items():
            if isinstance(out, dict) and "images" in out:
                for im in out["images"]:
                    fn = im.get("filename", "")
                    if not prefix or prefix in fn:
                        has_match = True
                        break
        if has_match:
            saved = await process_and_save_comfy_output(pid, data, db, base_url=base_url)
            all_saved.extend(saved)

    return {"imported_count": len(all_saved), "items": all_saved}

class WorkflowInspectRequest(BaseModel):
    workflow: Dict[str, Any]

@router.post("/workflow/inspect")
async def inspect_workflow(req: WorkflowInspectRequest):
    try:
        return graph_syncer.inspect_graph(req.workflow)
    except Exception as e:
        logger.error(f"Error inspecting workflow graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/discord-status")
async def get_discord_status():
    """Returns whether Discord webhook is configured and active."""
    url = _get_discord_webhook_url()
    masked = None
    if url:
        if len(url) > 45:
            masked = f"{url[:35]}...{url[-6:]}"
        else:
            masked = "***configured***"
    return {
        "configured": bool(url),
        "webhook_url": url or "",
        "masked_url": masked
    }


class DiscordConfigRequest(BaseModel):
    webhook_url: str


@router.post("/discord-config")
async def set_discord_config(req: DiscordConfigRequest):
    """Saves or updates Discord webhook URL in workspace configuration and runtime environment."""
    url = req.webhook_url.strip()
    if url and "discord.com/api/webhooks" not in url:
        raise HTTPException(status_code=400, detail="Invalid Discord webhook URL format.")

    os.environ["DISCORD_WEBHOOK_URL"] = url

    # Persist to workspace/discord_config.ini
    workspace_dir = "/workspace" if os.path.exists("/workspace") else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "workspace"))
    os.makedirs(workspace_dir, exist_ok=True)
    cfg_file = os.path.join(workspace_dir, "discord_config.ini")

    cfg = configparser.ConfigParser()
    if os.path.exists(cfg_file):
        cfg.read(cfg_file, encoding="utf-8")
    if not cfg.has_section("Discord"):
        cfg.add_section("Discord")
    cfg.set("Discord", "webhook_url", url)

    with open(cfg_file, "w", encoding="utf-8") as f:
        cfg.write(f)

    logger.info(f"Discord webhook URL saved to {cfg_file}")
    return {"ok": True, "configured": bool(url), "webhook_url": url}


class ResendDiscordRequest(BaseModel):
    limit: Optional[int] = 10


@router.post("/resend-recent-discord")
async def resend_recent_discord(req: Optional[ResendDiscordRequest] = None, db: Session = Depends(get_db)):
    """Resends the most recent sweep images and companion prompts to Discord."""
    limit = req.limit if req and req.limit else 10
    webhook_url = _get_discord_webhook_url()
    if not webhook_url:
        raise HTTPException(status_code=400, detail="Discord webhook URL is not configured.")

    recent_images = db.query(Image).order_by(Image.id.desc()).limit(limit).all()
    sent_count = 0
    errors = []

    for img in reversed(recent_images):
        local_path = os.path.join(STATIC_IMAGES_DIR, img.filename)
        if not os.path.exists(local_path):
            continue

        prompt_text = ""
        if img.prompt:
            prompt_text = img.prompt.content
        elif img.prompt_id:
            p_rec = db.query(Prompt).filter(Prompt.id == img.prompt_id).first()
            if p_rec:
                prompt_text = p_rec.content

        if not prompt_text:
            meta = extract_metadata_from_png(local_path)
            prompt_text = meta.get("prompt_text", "")

        ok = await _send_image_to_discord(local_path, img.filename, prompt_text, webhook_url_override=webhook_url)
        if ok:
            sent_count += 1
            await asyncio.sleep(0.5)
        else:
            errors.append(img.filename)

    return {
        "attempted": len(recent_images),
        "sent": sent_count,
        "failed": len(errors),
        "errors": errors
    }



