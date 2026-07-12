from fastapi import APIRouter, Depends, HTTPException
import httpx
from app.services.comfyui_connector import ComfyUIConnector
from app.services.wildcard_engine import WildcardEngine
from app.dependencies import get_wildcard_engine, get_comfyui_connector
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter()

class ExpandRequest(BaseModel):
    prompt: str

class ExpandResponse(BaseModel):
    expanded_prompt: str

class SubmitRequest(BaseModel):
    workflow: Dict[str, Any]

@router.post("/expand", response_model=ExpandResponse)
async def expand_prompt(
    request: ExpandRequest,
    engine: WildcardEngine = Depends(get_wildcard_engine)
):
    expanded = engine.expand_prompt(request.prompt)
    return ExpandResponse(expanded_prompt=expanded)

@router.post("/submit")
async def submit_workflow(
    request: SubmitRequest,
    connector: ComfyUIConnector = Depends(get_comfyui_connector)
):
    try:
        response = await connector.queue_prompt(request.workflow)
        return response
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="ComfyUI server error")
