import copy
import json
import asyncio
import logging
import random
import os
import aiofiles
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

logger = logging.getLogger(__name__)

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
    is_unet: bool = True
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
            "width": 1024,
            "height": 1024,
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
                    is_unet=is_unet
                )

            res = await connector.queue_prompt(wf_copy, base_url=req.base_url, client_id=req.client_id)
            results.append(res)

        queued_pids = [r["prompt_id"] for r in results if isinstance(r, dict) and "prompt_id" in r]
        if queued_pids:
            background_tasks.add_task(background_poll_sweep_prompts, queued_pids, req.base_url)

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

                # Find or create DB Image record
                db_img = db.query(Image).filter(Image.filename == fn).first()
                if not db_img:
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

                    db_img = Image(
                        filename=fn,
                        prompt_id=prompt_record.id if prompt_record else None,
                        seed=seed,
                        cfg_scale=float(cfg) if cfg is not None else None,
                        steps=int(steps) if steps is not None else None,
                        sampler_name=sampler_name,
                        width=1024,
                        height=1024,
                        comfy_workflow_id=prompt_id
                    )
                    db.add(db_img)
                    try:
                        db.commit()
                        db.refresh(db_img)
                    except Exception:
                        db.rollback()
                        db_img = db.query(Image).filter(Image.filename == fn).first()

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

async def background_poll_sweep_prompts(prompt_ids: List[str], base_url: Optional[str] = None):
    """Monitors queued sweep prompt IDs until completion and saves images to DB/storage."""
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return

    real_pids = [
        p for p in prompt_ids 
        if p and not any(str(p).startswith(prefix) for prefix in ("test-", "mock-", "krea2-", "dummy-", "p-"))
    ]
    if not real_pids:
        return

    pending = set(real_pids)
    max_wait_seconds = 600
    start_time = asyncio.get_event_loop().time()
    consecutive_errors = 0

    while pending and (asyncio.get_event_loop().time() - start_time) < max_wait_seconds:
        await asyncio.sleep(2.0)
        db = SessionLocal()
        try:
            for pid in list(pending):
                try:
                    hist_data = await connector.get_history(pid, base_url=base_url)
                    consecutive_errors = 0
                    if isinstance(hist_data, dict) and pid in hist_data:
                        job_info = hist_data[pid]
                        if job_info.get("outputs"):
                            await process_and_save_comfy_output(pid, job_info, db, base_url=base_url)
                            pending.discard(pid)
                except Exception as e:
                    consecutive_errors += 1
                    logger.debug(f"Sweep background poll for {pid} pending: {e}")
                    if consecutive_errors > 10:
                        return
        except Exception as e:
            logger.warning(f"Error in background_poll_sweep_prompts: {e}")
        finally:
            db.close()

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


