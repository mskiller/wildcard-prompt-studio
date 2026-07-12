from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from app.models.image import Image
from app.schemas.image import ImageCreate, ImageUpdate, ImageResponse
from app.dependencies import get_db

router = APIRouter()

@router.get("/", response_model=List[ImageResponse])
def get_images(skip: int = 0, limit: int = Query(default=100, le=100), db: Session = Depends(get_db)):
    return db.query(Image).offset(skip).limit(limit).all()

@router.post("/", response_model=ImageResponse)
def create_image(image: ImageCreate, db: Session = Depends(get_db)):
    db_image = Image(**image.model_dump())
    db.add(db_image)
    try:
        db.commit()
        db.refresh(db_image)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Related entity does not exist or integrity error")
    return db_image

@router.get("/{image_id}", response_model=ImageResponse)
def get_image(image_id: int, db: Session = Depends(get_db)):
    image = db.query(Image).filter(Image.id == image_id).first()
    if image is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return image

@router.patch("/{image_id}", response_model=ImageResponse)
def update_image(image_id: int, image_update: ImageUpdate, db: Session = Depends(get_db)):
    db_image = db.query(Image).filter(Image.id == image_id).first()
    if db_image is None:
        raise HTTPException(status_code=404, detail="Image not found")
    
    update_data = image_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_image, key, value)
        
    try:
        db.commit()
        db.refresh(db_image)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Related entity does not exist or integrity error")
    return db_image

@router.delete("/{image_id}")
def delete_image(image_id: int, db: Session = Depends(get_db)):
    db_image = db.query(Image).filter(Image.id == image_id).first()
    if db_image is None:
        raise HTTPException(status_code=404, detail="Image not found")
        
    db.delete(db_image)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Cannot delete because of related entities")
    return {"ok": True}
