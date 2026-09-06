from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from app.models.tag import Tag
from app.schemas.tag import TagCreate, TagUpdate, TagResponse
from app.dependencies import get_db

router = APIRouter()

@router.get("/", response_model=List[TagResponse])
def get_tags(
    q: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = Query(default=100, le=2000),
    db: Session = Depends(get_db)
):
    query = db.query(Tag)
    if q and q.strip():
        search_pattern = f"%{q.strip()}%"
        query = query.filter(Tag.name.ilike(search_pattern))
    if category and category.strip() and category.lower() != "all":
        query = query.filter(Tag.category == category.strip())
    return query.order_by(Tag.name.asc()).offset(skip).limit(limit).all()

@router.get("/categories")
def get_tag_categories(db: Session = Depends(get_db)):
    """Returns all unique tag categories and the count of tags in each category."""
    from sqlalchemy import func
    results = db.query(Tag.category, func.count(Tag.id)).group_by(Tag.category).all()
    categories = []
    total = 0
    for cat, count in results:
        total += count
        categories.append({"name": cat or "General", "count": count})
    categories.sort(key=lambda x: x["count"], reverse=True)
    return {"total": total, "categories": categories}

@router.post("/sanitize")
def sanitize_tags_database(db: Session = Depends(get_db)):
    """
    Cleans all existing tags in the database by stripping syntax leftovers
    (e.g. {4::, :1.3), full sentence fragments), reclassifying categories,
    and deleting duplicates.
    """
    from app.services.wildcard_ast import sanitize_single_tag, classify_tag_category
    
    raw_tags = db.query(Tag.id, Tag.name).all()
    name_to_id = {}
    to_delete_ids = set()
    to_update = {} # id -> (clean_name, category)

    for tid, name in raw_tags:
        clean = sanitize_single_tag(name)
        if not clean:
            to_delete_ids.add(tid)
            continue

        cl = clean.lower()
        if cl in name_to_id:
            to_delete_ids.add(tid)
        else:
            name_to_id[cl] = tid
            to_update[tid] = (clean, classify_tag_category(clean))

    try:
        # Step 1: Delete all invalid/duplicate tags in chunks
        del_list = list(to_delete_ids)
        chunk_size = 1000
        for i in range(0, len(del_list), chunk_size):
            chunk = del_list[i:i+chunk_size]
            db.query(Tag).filter(Tag.id.in_(chunk)).delete(synchronize_session=False)
        db.commit()

        # Step 2: Update remaining valid tags
        updated_count = 0
        tag_objects = db.query(Tag).filter(Tag.id.in_(list(to_update.keys()))).all()
        for tag in tag_objects:
            if tag.id in to_update:
                clean_name, cat = to_update[tag.id]
                if tag.name != clean_name or tag.category != cat:
                    tag.name = clean_name
                    tag.category = cat
                    updated_count += 1
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database sanitization error: {e}")

    return {
        "ok": True,
        "tags_cleaned": updated_count,
        "tags_deleted": len(to_delete_ids),
        "total_remaining": db.query(Tag).count()
    }


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
