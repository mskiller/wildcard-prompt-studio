"""
System Administration & Maintenance Router
Provides database statistics, selective cleanup, and factory reset endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.tag import Tag
from app.models.wildcard import Wildcard
from app.models.prompt import Prompt, prompt_tag_association
from app.models.version import PromptVersion
from app.models.image import Image
from app.models.model_profile import ModelProfile
from app.services.danbooru_service import danbooru_service

router = APIRouter()


class ResetRequest(BaseModel):
    target: str  # "tags", "wildcards", "prompts", "gallery", "all"
    confirm: Optional[str] = None  # e.g. "RESET" for full reset


@router.get("/stats")
def get_system_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Returns entity counts across all tables and Danbooru service stats."""
    tags_count = db.query(Tag).count()
    wildcards_count = db.query(Wildcard).count()
    prompts_count = db.query(Prompt).count()
    versions_count = db.query(PromptVersion).count()
    images_count = db.query(Image).count()
    profiles_count = db.query(ModelProfile).count()

    danbooru_stats = danbooru_service.get_stats()

    return {
        "tags_count": tags_count,
        "wildcards_count": wildcards_count,
        "prompts_count": prompts_count,
        "versions_count": versions_count,
        "images_count": images_count,
        "profiles_count": profiles_count,
        "danbooru": danbooru_stats
    }


@router.post("/reset")
def reset_database_section(payload: ResetRequest, db: Session = Depends(get_db)):
    """
    Safely cleans or resets target sections of the database.
    Supported targets: 'tags', 'wildcards', 'prompts', 'gallery', 'all'.
    """
    target = payload.target.lower().strip()

    if target == "tags":
        count = db.query(Tag).count()
        # Delete association links first
        db.execute(prompt_tag_association.delete())
        db.query(Tag).delete(synchronize_session=False)
        db.commit()
        return {"ok": True, "target": "tags", "deleted": count, "message": f"Successfully deleted {count} tags."}

    elif target == "wildcards":
        count = db.query(Wildcard).count()
        db.query(Wildcard).delete(synchronize_session=False)
        db.commit()
        return {"ok": True, "target": "wildcards", "deleted": count, "message": f"Successfully deleted {count} wildcards."}

    elif target == "prompts":
        v_count = db.query(PromptVersion).count()
        p_count = db.query(Prompt).count()
        # 1. Detach images so generated gallery images are preserved without foreign key violations
        db.query(Image).filter(Image.prompt_id.isnot(None)).update({Image.prompt_id: None}, synchronize_session=False)
        # 2. Delete association links in prompt_tags
        db.execute(prompt_tag_association.delete())
        # 3. Delete prompt version records
        db.query(PromptVersion).delete(synchronize_session=False)
        # 4. Delete prompts
        db.query(Prompt).delete(synchronize_session=False)
        db.commit()
        return {
            "ok": True, 
            "target": "prompts", 
            "deleted_prompts": p_count, 
            "deleted_versions": v_count,
            "message": f"Deleted {p_count} prompts and {v_count} versions."
        }

    elif target == "gallery":
        count = db.query(Image).count()
        db.query(Image).delete(synchronize_session=False)
        db.commit()
        return {"ok": True, "target": "gallery", "deleted": count, "message": f"Deleted {count} generated images."}

    elif target == "all":
        # Factory reset requires confirm keyword
        if payload.confirm != "RESET":
            raise HTTPException(status_code=400, detail="Factory reset requires confirm='RESET'")

        # Delete dependent tables in strict topological order
        db.execute(prompt_tag_association.delete())
        db.query(PromptVersion).delete(synchronize_session=False)
        db.query(Image).delete(synchronize_session=False)
        db.query(Prompt).delete(synchronize_session=False)
        db.query(Wildcard).delete(synchronize_session=False)
        db.query(Tag).delete(synchronize_session=False)

        # Seed basic profiles if empty
        if db.query(ModelProfile).count() == 0:
            from scripts.seed import seed_data
            try:
                seed_data()
            except Exception:
                pass

        db.commit()
        return {"ok": True, "target": "all", "message": "Entire database has been factory reset."}

    else:
        raise HTTPException(status_code=400, detail=f"Unknown reset target: '{target}'. Must be one of: tags, wildcards, prompts, gallery, all.")