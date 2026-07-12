from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from app.models.prompt import Prompt
from app.schemas.prompt import PromptCreate, PromptUpdate, PromptResponse
from app.dependencies import get_db

router = APIRouter()

@router.get("/", response_model=List[PromptResponse])
def get_prompts(skip: int = 0, limit: int = Query(default=100, le=100), db: Session = Depends(get_db)):
    return db.query(Prompt).offset(skip).limit(limit).all()

@router.post("/", response_model=PromptResponse)
def create_prompt(prompt: PromptCreate, db: Session = Depends(get_db)):
    db_prompt = Prompt(**prompt.model_dump())
    db.add(db_prompt)
    try:
        db.commit()
        db.refresh(db_prompt)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Related entity does not exist or integrity error")
    return db_prompt

@router.get("/{prompt_id}", response_model=PromptResponse)
def get_prompt(prompt_id: int, db: Session = Depends(get_db)):
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt

@router.patch("/{prompt_id}", response_model=PromptResponse)
def update_prompt(prompt_id: int, prompt_update: PromptUpdate, db: Session = Depends(get_db)):
    db_prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if db_prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    update_data = prompt_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_prompt, key, value)
        
    try:
        db.commit()
        db.refresh(db_prompt)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Related entity does not exist or integrity error")
    return db_prompt

@router.delete("/{prompt_id}")
def delete_prompt(prompt_id: int, db: Session = Depends(get_db)):
    db_prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if db_prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")
        
    db.delete(db_prompt)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Cannot delete because of related entities")
    return {"ok": True}
