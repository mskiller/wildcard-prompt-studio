"""
Danbooru API Router
Exposes Danbooru tags, co-occurrences, and smart prompt synergy recommendations.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.services.danbooru_service import danbooru_service

router = APIRouter()


class RecommendRequest(BaseModel):
    prompt: Optional[str] = None
    current_tags: Optional[List[str]] = None
    limit: Optional[int] = 15


class ImportRequest(BaseModel):
    limit: Optional[int] = 5000


@router.get("/stats")
def get_danbooru_stats():
    """Returns database size, ready status, and category counts."""
    return danbooru_service.get_stats()


@router.get("/tags")
def get_danbooru_tags(
    q: Optional[str] = Query(None, description="Search term for tag name"),
    category: Optional[str] = Query(None, description="Filter by category (general, character, copyright, artist, meta)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    """Searches and lists Danbooru tags with popularity counts."""
    return danbooru_service.get_tags(q=q, category=category, limit=limit, offset=skip)


@router.get("/cooccurrences")
def get_tag_cooccurrences(
    tag: str = Query(..., description="Danbooru tag name to find co-occurring pairs for"),
    limit: int = Query(20, ge=1, le=100)
):
    """Returns the top tags that co-occur with the given tag."""
    results = danbooru_service.get_cooccurrences(tag=tag, limit=limit)
    return results


@router.post("/recommend")
def recommend_danbooru_tags(payload: RecommendRequest):
    """
    Analyzes prompt text or an array of tags and recommends top complementary
    Danbooru tags ranked by co-occurrence synergy.
    """
    return danbooru_service.recommend_tags(
        prompt=payload.prompt,
        current_tags=payload.current_tags,
        limit=payload.limit or 15
    )


@router.post("/import-to-tags")
def import_danbooru_to_tags(
    payload: ImportRequest = ImportRequest(),
    db: Session = Depends(get_db)
):
    """
    Imports top Danbooru tags into the main application tags database table.
    """
    return danbooru_service.import_to_postgres(db=db, limit=payload.limit or 5000)