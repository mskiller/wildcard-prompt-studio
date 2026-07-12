from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from app.models.tag import Tag
from app.schemas.tag import TagCreate, TagUpdate, TagResponse
from app.dependencies import get_db

router = APIRouter()

@router.get("/", response_model=List[TagResponse])
def get_tags(skip: int = 0, limit: int = Query(default=100, le=100), db: Session = Depends(get_db)):
    return db.query(Tag).offset(skip).limit(limit).all()

@router.post("/", response_model=TagResponse)
def create_tag(tag: TagCreate, db: Session = Depends(get_db)):
    db_tag = Tag(**tag.model_dump())
    db.add(db_tag)
    try:
        db.commit()
        db.refresh(db_tag)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Related entity does not exist or integrity error")
    return db_tag

@router.get("/{tag_id}", response_model=TagResponse)
def get_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag

@router.patch("/{tag_id}", response_model=TagResponse)
def update_tag(tag_id: int, tag_update: TagUpdate, db: Session = Depends(get_db)):
    db_tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if db_tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    update_data = tag_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_tag, key, value)
        
    try:
        db.commit()
        db.refresh(db_tag)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Related entity does not exist or integrity error")
    return db_tag

@router.delete("/{tag_id}")
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    db_tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if db_tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")
        
    db.delete(db_tag)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Cannot delete because of related entities")
    return {"ok": True}
