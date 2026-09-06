from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.dependencies import get_db
from app.models.prompt import Prompt
from app.models.version import PromptVersion
from app.models.image import Image
from app.schemas.prompt import PromptCreate, PromptUpdate, PromptResponse
from app.schemas.version import PromptVersionBase, PromptVersionCreate, PromptVersionResponse
from app.services.sync_service import export_prompt_to_file
from app.services.async_rag import async_rag_service
from app.worker_tasks import generate_prompt_embedding

class VaultSimilarityRequest(BaseModel):
    prompt_text: Optional[str] = None
    text: Optional[str] = None
    threshold: float = 0.7


_search_embedder = None
def get_search_embedder():
    global _search_embedder
    if _search_embedder is None:
        try:
            from sentence_transformers import SentenceTransformer
            _search_embedder = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception:
            _search_embedder = "MOCK"
    return _search_embedder

router = APIRouter()

@router.post("/", response_model=PromptResponse)
def create_prompt(prompt: PromptCreate, db: Session = Depends(get_db)):
    db_prompt = Prompt(**prompt.model_dump())
    db.add(db_prompt)
    db.commit()
    db.refresh(db_prompt)
    export_prompt_to_file(db_prompt)
    generate_prompt_embedding.delay(db_prompt.id)
    async_rag_service.add_prompt_to_vault(db_prompt.id, db_prompt.content)
    return db_prompt


@router.get("/", response_model=List[PromptResponse])
def read_prompts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    prompts = db.query(Prompt).offset(skip).limit(limit).all()
    if not async_rag_service._vault_store and prompts:
        for p in prompts:
            async_rag_service.add_prompt_to_vault(p.id, p.content)
    return prompts

@router.get("/search", response_model=List[PromptResponse])
def search_prompts(q: str, limit: int = 10, db: Session = Depends(get_db)):
    if not q.strip():
        return []
    
    model = get_search_embedder()
    if model == "MOCK":
        prompts = db.query(Prompt).filter(Prompt.name.ilike(f"%{q}%") | Prompt.content.ilike(f"%{q}%")).limit(limit).all()
    else:
        try:
            query_embedding = model.encode(q).tolist()
            prompts = db.query(Prompt).order_by(Prompt.embedding.cosine_distance(query_embedding)).limit(limit).all()
        except Exception:
            prompts = db.query(Prompt).filter(Prompt.name.ilike(f"%{q}%") | Prompt.content.ilike(f"%{q}%")).limit(limit).all()
    return prompts

@router.get("/{prompt_id}", response_model=PromptResponse)
def read_prompt(prompt_id: int, db: Session = Depends(get_db)):
    db_prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if db_prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return db_prompt

@router.post("/{prompt_id}/versions", response_model=PromptVersionResponse)
def create_prompt_version(prompt_id: int, version: PromptVersionBase, db: Session = Depends(get_db)):
    db_prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not db_prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    db_version = PromptVersion(prompt_id=prompt_id, **version.model_dump())
    db.add(db_version)
    db.commit()
    db.refresh(db_version)
    return db_version

@router.patch("/{prompt_id}", response_model=PromptResponse)
def update_prompt(prompt_id: int, prompt_update: PromptUpdate, db: Session = Depends(get_db)):
    db_prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not db_prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    update_data = prompt_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_prompt, key, value)
    
    db.commit()
    db.refresh(db_prompt)
    export_prompt_to_file(db_prompt)
    generate_prompt_embedding.delay(db_prompt.id)
    return db_prompt

@router.delete("/{prompt_id}")
def delete_prompt(prompt_id: int, db: Session = Depends(get_db)):
    db_prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not db_prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    # Detach any images pointing to this prompt so gallery images survive without broken foreign keys
    db.query(Image).filter(Image.prompt_id == prompt_id).update({Image.prompt_id: None}, synchronize_session=False)
    db.delete(db_prompt)
    db.commit()
    return {"message": "Prompt deleted"}

@router.post("/vault/similarity")
def check_prompt_vault_similarity(req: VaultSimilarityRequest, db: Session = Depends(get_db)):
    prompt_text = req.prompt_text or req.text or ""
    if not prompt_text:
        return []
    
    if not async_rag_service._vault_store:
        prompts = db.query(Prompt).all()
        for p in prompts:
            async_rag_service.add_prompt_to_vault(p.id, p.content)
            
    matches = async_rag_service.check_duplicate_similarity(prompt_text, threshold=req.threshold)
    return matches

