from fastapi import APIRouter
from app.services.comfyui_connector import ComfyUIConnector
from app.services.wildcard_engine import WildcardEngine
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
async def expand_prompt(request: ExpandRequest):
    engine = WildcardEngine(wildcards={"character": ["elf", "knight"]})
    expanded = engine.expand_prompt(request.prompt)
    return ExpandResponse(expanded_prompt=expanded)

@router.post("/submit")
async def submit_workflow(request: SubmitRequest):
    connector = ComfyUIConnector()
    response = await connector.queue_prompt(request.workflow)
    return response
