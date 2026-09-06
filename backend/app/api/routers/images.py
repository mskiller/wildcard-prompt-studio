import logging
import os
from typing import List, Optional
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, contains_eager, joinedload
from app.models.image import Image
from app.models.prompt import Prompt
from app.schemas.image import (
    ImageCreate, 
    ImageUpdate, 
    ImageResponse,
    RatingUpdateRequest,
    BatchDeleteRequest,
    BatchRAGIndexRequest
)
from app.dependencies import get_db, get_comfyui_connector
from app.services.comfyui_connector import ComfyUIConnector
from app.services.aesthetic_scorer import score_aesthetic_prompt
from app.services.unified_rag import unified_rag_service
from app.services.image_metadata import extract_metadata_from_png

logger = logging.getLogger(__name__)
router = APIRouter()

class GalleryItemResponse(ImageResponse):
    prompt_content: str

class ImageCreateWithDownload(ImageCreate):
    comfyui_url: Optional[str] = None
    prompt_content: Optional[str] = None

# Consistently locate /app/app/static/images (matching main.py)
STATIC_IMAGES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "static", "images"))
os.makedirs(STATIC_IMAGES_DIR, exist_ok=True)

def ensure_image_prompt_linked(img: Image, db: Session) -> Optional[str]:
    """Ensures image has its associated Prompt record linked, falling back to PNG metadata."""
    if img.prompt and img.prompt.content:
        return img.prompt.content

    if img.prompt_id:
        p = db.query(Prompt).filter(Prompt.id == img.prompt_id).first()
        if p and p.content:
            img.prompt = p
            return p.content

    # Extract metadata from disk if available
    local_path = os.path.join(STATIC_IMAGES_DIR, img.filename)
    if os.path.exists(local_path):
        meta = extract_metadata_from_png(local_path)
        prompt_text = meta.get("prompt_text")
        if prompt_text:
            p_record = db.query(Prompt).filter(Prompt.content == prompt_text).first()
            if not p_record:
                p_record = Prompt(name=prompt_text[:32].strip(), content=prompt_text)
                db.add(p_record)
                try:
                    db.commit()
                    db.refresh(p_record)
                except Exception:
                    db.rollback()
                    p_record = db.query(Prompt).filter(Prompt.content == prompt_text).first()

            if p_record:
                img.prompt_id = p_record.id
                img.prompt = p_record
                if img.seed is None and meta.get("seed") is not None:
                    img.seed = meta.get("seed")
                if img.steps is None and meta.get("steps") is not None:
                    img.steps = meta.get("steps")
                if img.cfg_scale is None and meta.get("cfg") is not None:
                    img.cfg_scale = meta.get("cfg")
                if not img.sampler_name and meta.get("sampler_name"):
                    img.sampler_name = meta.get("sampler_name")
                if (not img.width or img.width == 1024) and meta.get("width"):
                    img.width = meta.get("width")
                if (not img.height or img.height == 1024) and meta.get("height"):
                    img.height = meta.get("height")
                try:
                    db.commit()
                    db.refresh(img)
                except Exception:
                    db.rollback()
                return prompt_text
    return None

def _to_gallery_response(img: Image, db: Optional[Session] = None) -> GalleryItemResponse:
    prompt_content = ""
    if img.prompt and img.prompt.content:
        prompt_content = img.prompt.content
    elif db:
        prompt_content = ensure_image_prompt_linked(img, db) or ""

    return GalleryItemResponse(
        id=img.id,
        filename=img.filename,
        prompt_id=img.prompt_id,
        seed=img.seed,
        cfg_scale=img.cfg_scale,
        steps=img.steps,
        sampler_name=img.sampler_name,
        width=img.width,
        height=img.height,
        comfy_workflow_id=img.comfy_workflow_id,
        is_favorite=img.is_favorite if img.is_favorite is not None else False,
        rating=img.rating if img.rating is not None else 0,
        aesthetic_score=img.aesthetic_score,
        created_at=img.created_at,
        prompt_content=prompt_content,
    )

@router.get("/gallery", response_model=List[GalleryItemResponse])
def get_gallery(
    skip: int = 0,
    limit: int = Query(default=50, le=100),
    search: Optional[str] = None,
    sampler: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    min_rating: Optional[int] = None,
    sort_by: str = "newest",
    db: Session = Depends(get_db)
):
    """Retrieve gallery images with search, filtering by sampler/favorites/ratings, and custom sorting."""
    query = db.query(Image).outerjoin(Prompt, Image.prompt_id == Prompt.id).options(contains_eager(Image.prompt))

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(or_(Image.filename.ilike(search_pattern), Prompt.content.ilike(search_pattern)))

    if sampler:
        query = query.filter(Image.sampler_name == sampler)

    if is_favorite is not None:
        query = query.filter(Image.is_favorite == is_favorite)

    if min_rating is not None:
        query = query.filter(Image.rating >= min_rating)

    sort_order = (sort_by or "newest").lower()
    if sort_order == "oldest":
        query = query.order_by(Image.created_at.asc(), Image.id.asc())
    elif sort_order == "rating":
        query = query.order_by(Image.rating.desc().nullslast(), Image.created_at.desc())
    elif sort_order == "aesthetic_score":
        query = query.order_by(Image.aesthetic_score.desc().nullslast(), Image.created_at.desc())
    else:  # "newest"
        query = query.order_by(Image.created_at.desc(), Image.id.desc())

    images = query.offset(skip).limit(limit).all()
    return [_to_gallery_response(img, db) for img in images]

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
    elif not prompt_id and os.path.exists(local_path):
        meta = extract_metadata_from_png(local_path)
        extracted_p = meta.get("prompt_text")
        if extracted_p:
            existing_prompt = db.query(Prompt).filter(Prompt.content == extracted_p).first()
            if not existing_prompt:
                existing_prompt = Prompt(name=extracted_p[:32].strip(), content=extracted_p)
                db.add(existing_prompt)
                try:
                    db.commit()
                    db.refresh(existing_prompt)
                except Exception:
                    db.rollback()
                    existing_prompt = db.query(Prompt).filter(Prompt.content == extracted_p).first()
            if existing_prompt:
                prompt_id = existing_prompt.id
        if image.seed is None and meta.get("seed") is not None:
            image.seed = meta.get("seed")
        if image.steps is None and meta.get("steps") is not None:
            image.steps = meta.get("steps")
        if image.cfg_scale is None and meta.get("cfg") is not None:
            image.cfg_scale = meta.get("cfg")
        if not image.sampler_name and meta.get("sampler_name"):
            image.sampler_name = meta.get("sampler_name")
        if (not image.width or image.width == 1024) and meta.get("width"):
            image.width = meta.get("width")
        if (not image.height or image.height == 1024) and meta.get("height"):
            image.height = meta.get("height")

    # Upsert: if image already exists, update missing prompt_id and parameters
    existing_img = db.query(Image).filter(Image.filename == image.filename).first()
    if existing_img:
        if prompt_id and not existing_img.prompt_id:
            existing_img.prompt_id = prompt_id
        if image.seed is not None and existing_img.seed is None:
            existing_img.seed = image.seed
        if image.steps is not None and existing_img.steps is None:
            existing_img.steps = image.steps
        if image.cfg_scale is not None and existing_img.cfg_scale is None:
            existing_img.cfg_scale = image.cfg_scale
        if image.sampler_name and not existing_img.sampler_name:
            existing_img.sampler_name = image.sampler_name
        if image.width and (not existing_img.width or existing_img.width == 1024):
            existing_img.width = image.width
        if image.height and (not existing_img.height or existing_img.height == 1024):
            existing_img.height = image.height
        db.commit()
        db.refresh(existing_img)
        return existing_img

    db_payload = image.model_dump(exclude={"comfyui_url", "prompt_content"})
    db_payload["prompt_id"] = prompt_id
    db_image = Image(**db_payload)
    db.add(db_image)
    try:
        db.commit()
        db.refresh(db_image)
    except IntegrityError:
        db.rollback()
        existing_img = db.query(Image).filter(Image.filename == image.filename).first()
        if existing_img:
            return existing_img
        raise HTTPException(status_code=400, detail="Related entity does not exist or integrity error")
    return db_image

@router.post("/batch/delete")
def batch_delete_images(payload: BatchDeleteRequest, db: Session = Depends(get_db)):
    """Delete multiple images and their local cached files safely."""
    if not payload.image_ids:
        return {"status": "deleted", "deleted_count": 0}

    images = db.query(Image).filter(Image.id.in_(payload.image_ids)).all()
    deleted_count = 0
    files_to_delete = []

    for img in images:
        if img.filename:
            safe_filename = os.path.basename(img.filename)
            files_to_delete.append(os.path.join(STATIC_IMAGES_DIR, safe_filename))
        db.delete(img)
        deleted_count += 1

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Cannot delete because of related entities")

    # Unlink local cached files after database commit succeeds
    for file_path in files_to_delete:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"Failed to remove static file {file_path}: {e}")

    return {"status": "deleted", "deleted_count": deleted_count}

@router.post("/batch/index-rag")
async def batch_index_rag(payload: BatchRAGIndexRequest, db: Session = Depends(get_db)):
    """Index prompts and metadata from selected images into the RAG knowledge vault."""
    if not payload.image_ids:
        return {"status": "indexed", "indexed_count": 0}

    images = (
        db.query(Image)
        .options(joinedload(Image.prompt))
        .filter(Image.id.in_(payload.image_ids))
        .all()
    )
    indexed_count = 0
    category = payload.category or "gallery_generations"
    tags = list(payload.tags or [])

    for img in images:
        prompt_content = img.prompt.content if (img.prompt and img.prompt.content) else ""
        content = prompt_content or f"Generated image {img.filename}"
        title = (img.prompt.name if (img.prompt and img.prompt.name) else None) or f"Image {img.filename}"

        await unified_rag_service.index_document_async(
            db=db,
            title=title,
            content=content,
            category=category,
            tags=tags,
        )
        indexed_count += 1

    return {"status": "indexed", "indexed_count": indexed_count}

@router.get("/{image_id}", response_model=GalleryItemResponse)
def get_image(image_id: int, db: Session = Depends(get_db)):
    image = db.query(Image).filter(Image.id == image_id).first()
    if image is None:
        raise HTTPException(status_code=404, detail="Image not found")
    ensure_image_prompt_linked(image, db)
    return _to_gallery_response(image, db)

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

@router.patch("/{image_id}/favorite", response_model=GalleryItemResponse)
def toggle_image_favorite(image_id: int, db: Session = Depends(get_db)):
    """Toggle the favorite status of an image."""
    img = db.query(Image).options(joinedload(Image.prompt)).filter(Image.id == image_id).first()
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")
    img.is_favorite = not bool(img.is_favorite)
    db.commit()
    db.refresh(img)
    return _to_gallery_response(img, db)

@router.patch("/{image_id}/rating", response_model=GalleryItemResponse)
def update_image_rating(
    image_id: int,
    rating_update: RatingUpdateRequest,
    db: Session = Depends(get_db),
):
    """Update star rating (0-5) for an image."""
    img = db.query(Image).options(joinedload(Image.prompt)).filter(Image.id == image_id).first()
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")
    img.rating = rating_update.rating
    db.commit()
    db.refresh(img)
    return _to_gallery_response(img, db)

@router.post("/{image_id}/score-aesthetic", response_model=GalleryItemResponse)
def score_image_aesthetic(image_id: int, db: Session = Depends(get_db)):
    """Calculate and store an aesthetic quality score for an image based on prompt and parameters."""
    img = db.query(Image).options(joinedload(Image.prompt)).filter(Image.id == image_id).first()
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")

    prompt_text = (img.prompt.content if (img.prompt and img.prompt.content) else "") or ensure_image_prompt_linked(img, db) or img.filename
    width = img.width or 512
    height = img.height or 512
    score = score_aesthetic_prompt(prompt_text, width=width, height=height)
    img.aesthetic_score = round(float(score), 2)
    db.commit()
    db.refresh(img)
    return _to_gallery_response(img, db)

@router.get("/{image_id}/similar", response_model=List[GalleryItemResponse])
async def get_similar_images(
    image_id: int,
    limit: int = Query(default=10, le=200),
    db: Session = Depends(get_db),
):
    """Find images with semantically similar prompts using pgvector cosine distance."""
    img = db.query(Image).options(joinedload(Image.prompt)).filter(Image.id == image_id).first()
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")

    ensure_image_prompt_linked(img, db)

    if not img.prompt or not img.prompt.content:
        return []

    if img.prompt.embedding is None:
        img.prompt.embedding = await unified_rag_service.compute_embedding_async(img.prompt.content)
        db.commit()
        db.refresh(img.prompt)

    target_vec = img.prompt.embedding
    if hasattr(target_vec, "tolist"):
        target_vec = target_vec.tolist()
    elif hasattr(target_vec, "__iter__") and not isinstance(target_vec, list):
        target_vec = list(target_vec)

    # Lazily compute missing embeddings for candidate images' prompts up to a bounded batch
    unembedded_prompts = (
        db.query(Prompt)
        .join(Image, Image.prompt_id == Prompt.id)
        .filter(Image.id != image_id, Prompt.embedding.is_(None))
        .distinct()
        .limit(500)
        .all()
    )
    if unembedded_prompts:
        for p in unembedded_prompts:
            if p.content:
                p.embedding = await unified_rag_service.compute_embedding_async(p.content)
        db.commit()

    similar_images = (
        db.query(Image)
        .join(Prompt, Image.prompt_id == Prompt.id)
        .options(contains_eager(Image.prompt))
        .filter(Image.id != image_id)
        .filter(Prompt.embedding.isnot(None))
        .order_by(Prompt.embedding.cosine_distance(target_vec))
        .limit(limit)
        .all()
    )

    return [_to_gallery_response(s_img, db) for s_img in similar_images]
