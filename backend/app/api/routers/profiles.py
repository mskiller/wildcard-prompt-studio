from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from app.models.model_profile import ModelProfile
from app.schemas.model_profile import ModelProfileCreate, ModelProfileUpdate, ModelProfileResponse
from app.dependencies import get_db

router = APIRouter()

@router.get("/", response_model=List[ModelProfileResponse])
def get_model_profiles(skip: int = 0, limit: int = Query(default=100, le=100), db: Session = Depends(get_db)):
    return db.query(ModelProfile).offset(skip).limit(limit).all()

@router.post("/", response_model=ModelProfileResponse)
def create_model_profile(profile: ModelProfileCreate, db: Session = Depends(get_db)):
    db_profile = ModelProfile(**profile.model_dump())
    db.add(db_profile)
    try:
        db.commit()
        db.refresh(db_profile)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Profile with this name already exists")
    return db_profile

@router.get("/{profile_id}", response_model=ModelProfileResponse)
def get_model_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.query(ModelProfile).filter(ModelProfile.id == profile_id).first()
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.patch("/{profile_id}", response_model=ModelProfileResponse)
def update_model_profile(profile_id: int, profile_update: ModelProfileUpdate, db: Session = Depends(get_db)):
    db_profile = db.query(ModelProfile).filter(ModelProfile.id == profile_id).first()
    if db_profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    update_data = profile_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_profile, key, value)
        
    try:
        db.commit()
        db.refresh(db_profile)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Profile with this name already exists")
    return db_profile

@router.delete("/{profile_id}")
def delete_model_profile(profile_id: int, db: Session = Depends(get_db)):
    db_profile = db.query(ModelProfile).filter(ModelProfile.id == profile_id).first()
    if db_profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    db.delete(db_profile)
    db.commit()
    return {"ok": True}
