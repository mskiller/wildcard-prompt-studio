from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from app.models.wildcard import Wildcard
from app.schemas.wildcard import WildcardCreate, WildcardUpdate, WildcardResponse
from app.dependencies import get_db

router = APIRouter()

@router.get("/", response_model=List[WildcardResponse])
def get_wildcards(skip: int = 0, limit: int = Query(default=100, le=100), db: Session = Depends(get_db)):
    return db.query(Wildcard).offset(skip).limit(limit).all()

@router.post("/", response_model=WildcardResponse)
def create_wildcard(wildcard: WildcardCreate, db: Session = Depends(get_db)):
    db_wildcard = Wildcard(**wildcard.model_dump())
    db.add(db_wildcard)
    try:
        db.commit()
        db.refresh(db_wildcard)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Related entity does not exist or integrity error")
    return db_wildcard

@router.get("/{wildcard_id}", response_model=WildcardResponse)
def get_wildcard(wildcard_id: int, db: Session = Depends(get_db)):
    wildcard = db.query(Wildcard).filter(Wildcard.id == wildcard_id).first()
    if wildcard is None:
        raise HTTPException(status_code=404, detail="Wildcard not found")
    return wildcard

@router.patch("/{wildcard_id}", response_model=WildcardResponse)
def update_wildcard(wildcard_id: int, wildcard_update: WildcardUpdate, db: Session = Depends(get_db)):
    db_wildcard = db.query(Wildcard).filter(Wildcard.id == wildcard_id).first()
    if db_wildcard is None:
        raise HTTPException(status_code=404, detail="Wildcard not found")
    
    update_data = wildcard_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_wildcard, key, value)
        
    try:
        db.commit()
        db.refresh(db_wildcard)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Related entity does not exist or integrity error")
    return db_wildcard

@router.delete("/{wildcard_id}")
def delete_wildcard(wildcard_id: int, db: Session = Depends(get_db)):
    db_wildcard = db.query(Wildcard).filter(Wildcard.id == wildcard_id).first()
    if db_wildcard is None:
        raise HTTPException(status_code=404, detail="Wildcard not found")
        
    db.delete(db_wildcard)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Cannot delete because of related entities")
    return {"ok": True}
