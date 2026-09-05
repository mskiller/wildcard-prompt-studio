from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
import os
import aiofiles
from pydantic import BaseModel
from app.models.image import Image
from app.models.prompt import Prompt
from app.schemas.image import ImageCreate, ImageUpdate, ImageResponse
from app.dependencies import get_db, get_comfyui_connector
from app.services.comfyui_connector import ComfyUIConnector

router = APIRouter()

class GalleryItemResponse(ImageResponse):
    prompt_content: str

class ImageCreateWithDownload(ImageCreate):
    comfyui_url: Optional[str] = None
    prompt_content: Optional[str] = None

# Consistently locate /app/app/static/images (matching main.py)
STATIC_IMAGES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "static", "images"))
os.makedirs(STATIC_IMAGES_DIR, exist_ok=True)

@router.get("/gallery", response_model=List[GalleryItemResponse])
def get_gallery(skip: int = 0, limit: int = Query(default=50, le=100), db: Session = Depends(get_db)):
    images = db.query(Image).order_by(Image.created_at.desc()).offset(skip).limit(limit).all()
    result = []
    for img in images:
        prompt = db.query(Prompt).filter(Prompt.id == img.prompt_id).first() if img.prompt_id else None
        prompt_content = prompt.content if prompt else ""
        item_dict = img.__dict__.copy()
        item_dict['prompt_content'] = prompt_content
        result.append(item_dict)
    return result

@router.get("/file/{filename}")
async def get_image_file(
    filename: str,
    base_url: Optional[str] = None,
    connector: ComfyUIConnector = Depends(get_comfyui_connector)
):
    """Serve image directly, caching locally from ComfyUI if not yet cached."""
    local_path = os.path.join(STATIC_IMAGES_DIR, filename)
    if os.path.exists(local_path):
        async with aiofiles.open(local_path, "rb") as f:
            content = await f.read()
            return Response(content=content, media_type="image/png")

    try:
        content = await connector.get_image(filename, base_url=base_url)
        os.makedirs(STATIC_IMAGES_DIR, exist_ok=True)
        async with aiofiles.open(local_path, "wb") as f:
            await f.write(content)
        return Response(content=content, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Image {filename} not found: {str(e)}")

@router.get("/", response_model=List[ImageResponse])
def get_images(skip: int = 0, limit: int = Query(default=100, le=100), db: Session = Depends(get_db)):
    return db.query(Image).offset(skip).limit(limit).all()

@router.post("/", response_model=ImageResponse)
async def create_image(
    image: ImageCreateWithDownload, 
    db: Session = Depends(get_db),
    connector: ComfyUIConnector = Depends(get_comfyui_connector)
):
    # Download from ComfyUI if a URL is provided or if file not yet present
    local_path = os.path.join(STATIC_IMAGES_DIR, image.filename)
    if not os.path.exists(local_path):
        try:
            image_data = await connector.get_image(image.filename, base_url=image.comfyui_url)
            os.makedirs(STATIC_IMAGES_DIR, exist_ok=True)
            async with aiofiles.open(local_path, "wb") as f:
                await f.write(image_data)
        except Exception as e:
            print(f"Failed to download image from ComfyUI: {e}")

    # If prompt_id is missing but prompt_content is provided, link or create Prompt
    prompt_id = image.prompt_id
    if not prompt_id and image.prompt_content:
        existing_prompt = db.query(Prompt).filter(Prompt.content == image.prompt_content).first()
        if not existing_prompt:
            existing_prompt = Prompt(name=image.prompt_content[:32].strip(), content=image.prompt_content)
            db.add(existing_prompt)
            db.commit()
            db.refresh(existing_prompt)
        prompt_id = existing_prompt.id

    db_payload = image.model_dump(exclude={"comfyui_url", "prompt_content"})
    db_payload["prompt_id"] = prompt_id
    db_image = Image(**db_payload)
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
