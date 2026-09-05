from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.services.aesthetic_scorer import aesthetic_scorer
from app.services.genetic_optimizer import genetic_optimizer
from app.services.civitai_sync import civitai_sync_client
from app.services.cloud_storage import cloud_storage_service

router = APIRouter()

class ScoreRequest(BaseModel):
    prompt: str
    width: Optional[int] = 1024
    height: Optional[int] = 1024

class EvolveRequest(BaseModel):
    population: List[str]
    fitness_scores: List[float]
    population_size: Optional[int] = 4

@router.post("/score")
def score_prompt(req: ScoreRequest):
    score = aesthetic_scorer.score_prompt_and_metadata(req.prompt, width=req.width, height=req.height)
    return {"prompt": req.prompt, "aesthetic_score": score}

@router.post("/evolve")
def evolve_prompts(req: EvolveRequest):
    next_gen = genetic_optimizer.evolve(req.population, req.fitness_scores, population_size=req.population_size or 4)
    return {"generation": next_gen}

@router.get("/civitai/search")
async def search_civitai_hub(q: Optional[str] = ""):
    return await civitai_sync_client.search_wildcard_packs(q or "")

@router.post("/cloud/upload")
def upload_asset(filename: str, local_path: str):
    url = cloud_storage_service.upload_file(local_path, filename)
    if not url:
        raise HTTPException(status_code=500, detail="Failed to upload asset to cloud storage.")
    return {"url": url}
