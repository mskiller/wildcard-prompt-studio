from fastapi import APIRouter, Depends, HTTPException, Query
import httpx
from app.services.comfyui_connector import ComfyUIConnector
from app.services.wildcard_engine import WildcardEngine
from app.services.matrix_engine import MatrixEngine
from app.dependencies import get_wildcard_engine, get_comfyui_connector, get_matrix_engine
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

router = APIRouter()

class ExpandRequest(BaseModel):
    prompt: str

class ExpandResponse(BaseModel):
    expanded_prompt: str

class MatrixRequest(BaseModel):
    prompt: str
    max_depth: Optional[int] = 10
    expand_wildcards: Optional[bool] = True
    max_limit: Optional[int] = None

class SubmitRequest(BaseModel):
    workflow: Dict[str, Any]
    comfyui_url: Optional[str] = None

class MatrixPermutationItem(BaseModel):
    index: int
    prompt: str

class MatrixSliceRequest(BaseModel):
    prompt: str
    offset: Optional[int] = 0
    limit: Optional[int] = 250
    expand_wildcards: Optional[bool] = True
    sample_size: Optional[int] = None
    seed: Optional[int] = None
    indices: Optional[List[int]] = None

class MatrixSliceResponse(BaseModel):
    total_count: int
    offset: int = 0
    limit: int = 0
    is_sample: bool = False
    items: List[MatrixPermutationItem]

class MatrixExecuteRequest(BaseModel):
    prompt: Optional[str] = ""
    max_depth: Optional[int] = 10
    limit: Optional[int] = None
    expand_wildcards: Optional[bool] = True
    mode: Optional[str] = "view"
    offset: Optional[int] = 0
    sample_size: Optional[int] = None
    seed: Optional[int] = None
    indices: Optional[List[int]] = None
    prompts: Optional[List[str]] = None

class MatrixExecuteResponse(BaseModel):
    total_generated: int
    prompts: List[str]
    status: str

@router.post("/expand", response_model=ExpandResponse)
async def expand_prompt(
    request: ExpandRequest,
    engine: WildcardEngine = Depends(get_wildcard_engine)
):
    expanded = engine.expand_prompt(request.prompt)
    return ExpandResponse(expanded_prompt=expanded)

@router.post("/matrix", response_model=List[str])
async def generate_matrix(
    request: MatrixRequest,
    matrix_engine: MatrixEngine = Depends(get_matrix_engine)
):
    try:
        expand_wc = request.expand_wildcards if request.expand_wildcards is not None else True
        return matrix_engine.generate_matrix(
            request.prompt,
            max_depth=request.max_depth or 10,
            expand_wildcards=expand_wc,
            max_limit=request.max_limit
        )
    except Exception as e:
        # Return empty list or fallback to the prompt string on syntax error
        return [request.prompt] if request.prompt else []

@router.post("/matrix/slice", response_model=MatrixSliceResponse)
async def get_matrix_slice(
    request: MatrixSliceRequest,
    matrix_engine: MatrixEngine = Depends(get_matrix_engine)
):
    try:
        expand_wc = request.expand_wildcards if request.expand_wildcards is not None else True
        if request.indices is not None:
            data = matrix_engine.get_matrix_indices(
                request.prompt,
                indices=request.indices,
                expand_wildcards=expand_wc
            )
        elif request.sample_size is not None:
            data = matrix_engine.get_matrix_sample(
                request.prompt,
                sample_size=request.sample_size,
                seed=request.seed,
                expand_wildcards=expand_wc
            )
        else:
            offset = request.offset if request.offset is not None else 0
            limit = request.limit if request.limit is not None else 250
            data = matrix_engine.get_matrix_slice(
                request.prompt,
                offset=offset,
                limit=limit,
                expand_wildcards=expand_wc
            )
        return MatrixSliceResponse(**data)
    except Exception as e:
        return MatrixSliceResponse(
            total_count=0,
            offset=0,
            limit=0,
            is_sample=False,
            items=[]
        )

@router.post("/matrix/execute", response_model=MatrixExecuteResponse)
async def execute_matrix_sweep(
    request: MatrixExecuteRequest,
    matrix_engine: MatrixEngine = Depends(get_matrix_engine)
):
    try:
        expand_wc = request.expand_wildcards if request.expand_wildcards is not None else True
        prompts: List[str] = []

        if request.prompts is not None and len(request.prompts) > 0:
            prompts = list(request.prompts)
            if request.limit and request.limit > 0 and len(prompts) > request.limit:
                prompts = prompts[:request.limit]
        elif (request.indices is not None and len(request.indices) > 0) or request.mode == "indices":
            if request.indices:
                data = matrix_engine.get_matrix_indices(
                    request.prompt,
                    indices=request.indices,
                    expand_wildcards=expand_wc
                )
                prompts = [item["prompt"] for item in data.get("items", [])]
            else:
                prompts = []
        elif request.mode == "sample":
            sample_size = request.sample_size if request.sample_size is not None else (request.limit or 25)
            data = matrix_engine.get_matrix_sample(
                request.prompt,
                sample_size=sample_size,
                seed=request.seed,
                expand_wildcards=expand_wc
            )
            prompts = [item["prompt"] for item in data.get("items", [])]
        elif request.mode in ("range", "view"):
            offset = request.offset if request.offset is not None else 0
            limit = request.limit if request.limit is not None else 250
            data = matrix_engine.get_matrix_slice(
                request.prompt,
                offset=offset,
                limit=limit,
                expand_wildcards=expand_wc
            )
            prompts = [item["prompt"] for item in data.get("items", [])]
        else:
            limit = request.limit
            prompts = matrix_engine.generate_matrix(
                request.prompt,
                max_depth=request.max_depth or 10,
                expand_wildcards=expand_wc,
                max_limit=limit
            )
            if limit and limit > 0 and len(prompts) > limit:
                prompts = prompts[:limit]

        return MatrixExecuteResponse(
            total_generated=len(prompts),
            prompts=prompts,
            status="queued"
        )
    except Exception as e:
        return MatrixExecuteResponse(
            total_generated=1 if request.prompt else 0,
            prompts=[request.prompt] if request.prompt else [],
            status="error"
        )

@router.post("/matrix/analyze")
async def analyze_matrix_heatmap(
    request: MatrixRequest,
    matrix_engine: MatrixEngine = Depends(get_matrix_engine)
):
    try:
        expand_wc = request.expand_wildcards if request.expand_wildcards is not None else True
        return matrix_engine.analyze_heatmap_scores(
            request.prompt,
            expand_wildcards=expand_wc,
            max_limit=request.max_limit
        )
    except Exception:
        return {
            "combinations_count": 0,
            "avg_token_count": 0.0,
            "min_token_count": 0,
            "max_token_count": 0,
            "category_distribution": {"artist": 0, "character": 0, "copyright": 0, "general": 0, "meta": 0}
        }




class OptionsResponse(BaseModel):
    models: list[str]
    clips: list[str] = []
    vaes: list[str] = []
    samplers: list[str]
    schedulers: list[str]
    connected: bool = True

def _extract_strings_from_param(param_def) -> List[str]:
    results = []
    if isinstance(param_def, list):
        for item in param_def:
            if isinstance(item, str):
                results.append(item)
            elif isinstance(item, list):
                for sub in item:
                    if isinstance(sub, str):
                        results.append(sub)
    return results

def parse_comfyui_object_info(obj_info: dict):
    models = []
    clips = []
    vaes = []
    samplers = []
    schedulers = []

    if not isinstance(obj_info, dict):
        return models, clips, vaes, samplers, schedulers

    MODEL_EXTENSIONS = ('.safetensors', '.ckpt', '.pt', '.pth', '.bin', '.gguf', '.sft')
    CKPT_KEYS = {"ckpt_name", "ckpt", "model_name", "model", "unet_name", "unet", "checkpoint", "checkpoint_name", "ckpt_names", "diffusion_model"}
    CLIP_KEYS = {"clip_name", "clip_name1", "clip_name2", "clip"}
    VAE_KEYS = {"vae_name", "vae"}
    EXCLUDED_TYPES = {"MODEL", "CLIP", "VAE", "LATENT", "IMAGE", "CONDITIONING", "INT", "FLOAT", "STRING", "BOOLEAN", "COMBO", "MASK"}

    for node_type, node_data in obj_info.items():
        if not isinstance(node_data, dict):
            continue
        inputs = node_data.get("input") or {}
        if not isinstance(inputs, dict):
            inputs = {}
        all_inputs = {}
        if isinstance(inputs.get("required"), dict):
            all_inputs.update(inputs["required"])
        if isinstance(inputs.get("optional"), dict):
            all_inputs.update(inputs["optional"])

        for param_name, param_def in all_inputs.items():
            p_lower = param_name.lower()
            extracted = _extract_strings_from_param(param_def)
            if not extracted:
                continue

            if p_lower in CLIP_KEYS or ("clip" in p_lower and "name" in p_lower):
                for val in extracted:
                    if isinstance(val, str) and val not in EXCLUDED_TYPES and not val.startswith("{") and val not in clips:
                        clips.append(val)

            elif p_lower in VAE_KEYS or ("vae" in p_lower and "name" in p_lower):
                for val in extracted:
                    if isinstance(val, str) and val not in EXCLUDED_TYPES and not val.startswith("{") and val not in vaes:
                        vaes.append(val)

            elif p_lower in CKPT_KEYS or any(k in p_lower for k in ["unet", "ckpt", "diffusion"]):
                for val in extracted:
                    if isinstance(val, str) and val not in EXCLUDED_TYPES and not val.startswith("{") and val not in models:
                        models.append(val)
            else:
                for val in extracted:
                    if isinstance(val, str) and val not in EXCLUDED_TYPES and val.lower().endswith(MODEL_EXTENSIONS):
                        if val not in models and val not in clips and val not in vaes:
                            models.append(val)

            if "sampler" in p_lower:
                for s in extracted:
                    if isinstance(s, str) and s not in samplers and s not in EXCLUDED_TYPES and not s.startswith("{"):
                        samplers.append(s)

            if "scheduler" in p_lower:
                for sch in extracted:
                    if isinstance(sch, str) and sch not in schedulers and sch not in EXCLUDED_TYPES and not sch.startswith("{"):
                        schedulers.append(sch)

    return models, clips, vaes, samplers, schedulers

@router.get("/options", response_model=OptionsResponse)
async def get_generation_options(
    comfyui_url: Optional[str] = Query(None),
    connector: ComfyUIConnector = Depends(get_comfyui_connector)
):
    models = []
    clips = []
    vaes = []
    samplers = []
    schedulers = []
    connected = False

    try:
        obj_info = await connector.get_object_info(base_url=comfyui_url)
        if isinstance(obj_info, dict) and len(obj_info) > 0:
            connected = True
            models, clips, vaes, samplers, schedulers = parse_comfyui_object_info(obj_info)
    except Exception as e:
        print(f"Error fetching ComfyUI object info: {e}")
        connected = False

    DEFAULT_MODELS = [
        "Mklan_Kea2_V1.safetensors",
        "Mklan_Krea28v1.safetensors",
        "v1-5-pruned-emaonly.safetensors",
        "sd_xl_base_1.0.safetensors"
    ]
    DEFAULT_CLIPS = [
        "qwen3-vl-4b-heretic.safetensors",
        "Qwen3-VL-4B-Instruct-Heretic.safetensors",
        "qwen3VL4BAbliteratedComfyui_v10.safetensors"
    ]
    DEFAULT_VAES = [
        "qwen_image_vae.safetensors",
        "sdxl\\sdxl-vae-fp16-fix.safetensors"
    ]
    DEFAULT_SAMPLERS = [
        "er_sde",
        "euler",
        "euler_ancestral",
        "dpmpp_2m_sde",
        "dpmpp_2m",
        "dpmpp_sde"
    ]
    DEFAULT_SCHEDULERS = [
        "beta",
        "normal",
        "karras",
        "exponential",
        "simple"
    ]

    def prioritize(item_list, priority_item):
        if priority_item in item_list:
            item_list.remove(priority_item)
            item_list.insert(0, priority_item)

    prioritize(models, "Mklan_Kea2_V1.safetensors")
    prioritize(clips, "qwen3-vl-4b-heretic.safetensors")
    prioritize(vaes, "qwen_image_vae.safetensors")
    prioritize(samplers, "er_sde")
    prioritize(schedulers, "beta")

    return OptionsResponse(
        models=models if models else DEFAULT_MODELS,
        clips=clips if clips else DEFAULT_CLIPS,
        vaes=vaes if vaes else DEFAULT_VAES,
        samplers=samplers if samplers else DEFAULT_SAMPLERS,
        schedulers=schedulers if schedulers else DEFAULT_SCHEDULERS,
        connected=connected
    )


@router.post("/submit")
async def submit_workflow(
    request: SubmitRequest,
    connector: ComfyUIConnector = Depends(get_comfyui_connector)
):
    try:
        response = await connector.queue_prompt(request.workflow, base_url=request.comfyui_url)
        return response
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"ComfyUI server error: {str(e)}")
