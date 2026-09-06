from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from app.models.wildcard import Wildcard
from app.schemas.wildcard import WildcardCreate, WildcardUpdate, WildcardResponse
from app.dependencies import get_db

router = APIRouter()

@router.get("/", response_model=List[WildcardResponse])
def get_wildcards(skip: int = 0, limit: int = Query(default=10000, le=10000), db: Session = Depends(get_db)):
    return db.query(Wildcard).offset(skip).limit(limit).all()

def _sync_tags_from_text(text: str, db: Session):
    """Safely extracts atomic tags from text and stores them in the tags database."""
    if not text:
        return
    try:
        from app.services.wildcard_ast import extract_atomic_tags_from_text
        from app.models.tag import Tag
        tags_with_cats = extract_atomic_tags_from_text(text)
        if not tags_with_cats:
            return
        
        existing_names = set(
            row[0].lower()
            for row in db.query(Tag.name).filter(Tag.name.in_([t[0] for t in tags_with_cats])).all()
        )
        
        added = False
        for name, cat in tags_with_cats:
            if name.lower() not in existing_names:
                db.add(Tag(name=name, category=cat))
                existing_names.add(name.lower())
                added = True
        if added:
            db.commit()
    except Exception as e:
        print(f"Warning syncing tags: {e}")
        db.rollback()


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

    # Automatically extract and store tags from new wildcard
    _sync_tags_from_text(db_wildcard.content or "\n".join(db_wildcard.entries or []), db)

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

    # Automatically extract and store tags from updated wildcard content
    _sync_tags_from_text(db_wildcard.content or "\n".join(db_wildcard.entries or []), db)

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

class BatchDeleteWildcardsRequest(BaseModel):
    ids: List[int]

@router.post("/batch-delete")
def batch_delete_wildcards(payload: BatchDeleteWildcardsRequest, db: Session = Depends(get_db)):
    if not payload.ids:
        return {"ok": True, "deleted_count": 0}
    deleted = db.query(Wildcard).filter(Wildcard.id.in_(payload.ids)).delete(synchronize_session=False)
    db.commit()
    return {"ok": True, "deleted_count": deleted}

from fastapi import UploadFile, File
from app.services.importer import ImporterService
from app.services.sync_service import export_wildcard_to_file
from app.models.tag import Tag

import traceback

@router.post("/import")
async def import_wildcards(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    # Clean any leftover aborted transaction state
    db.rollback()
    
    try:
        imported_count = 0
        extracted_tags = set()
        
        # Track wildcards by normalized filename within this session batch
        batch_wildcards = {}
        
        for file in files:
            content = await file.read()
            content_str = ""
            for encoding in ['utf-8', 'utf-16', 'windows-1252', 'iso-8859-1']:
                try:
                    content_str = content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
                    
            if not content_str:
                continue # skip unreadable files
                
            # Strip null bytes to prevent PostgreSQL DataError
            content_str = content_str.replace('\x00', '')
            if not content_str.strip():
                continue

            parsed_data = {}
            raw_filename = file.filename or "wildcard.txt"
            clean_filename = raw_filename.replace('\\', '/').replace('\x00', '')
            filename_lower = clean_filename.lower()
            
            is_yaml = filename_lower.endswith(('.yaml', '.yml'))
            if filename_lower.endswith('.txt'):
                parsed_data = ImporterService.parse_txt(clean_filename, content_str)
            elif is_yaml:
                parsed_data = ImporterService.parse_yaml(clean_filename, content_str)
            else:
                parsed_data = ImporterService.parse_txt(clean_filename, content_str)
                
            for name, raw_choices in parsed_data.items():
                norm_name = str(name).replace('\\', '/').replace('\x00', '').strip()
                choices = [str(c).replace('\x00', '').strip() for c in raw_choices if c is not None and str(c).replace('\x00', '').strip()] if raw_choices else []
                if not norm_name or not choices:
                    continue

                w_type = 'yaml' if is_yaml else 'txt'

                if norm_name in batch_wildcards:
                    db_wildcard = batch_wildcards[norm_name]
                    existing = db_wildcard.content.split('\n') if db_wildcard.content else []
                    merged = list(dict.fromkeys(existing + choices))
                    db_wildcard.content = '\n'.join(merged)
                    db_wildcard.entries = merged
                else:
                    db_wildcard = db.query(Wildcard).filter(
                        (Wildcard.filename == norm_name) | 
                        (Wildcard.filename == f"{norm_name}.txt") | 
                        (Wildcard.filename == f"{norm_name}.yaml")
                    ).first()

                    if db_wildcard:
                        existing = db_wildcard.content.split('\n') if db_wildcard.content else []
                        merged = list(dict.fromkeys(existing + choices))
                        db_wildcard.content = '\n'.join(merged)
                        db_wildcard.entries = merged
                    else:
                        db_wildcard = Wildcard(
                            filename=norm_name, 
                            content='\n'.join(choices),
                            type=w_type,
                            entries=choices
                        )
                        db.add(db_wildcard)
                    
                    batch_wildcards[norm_name] = db_wildcard
                    imported_count += 1

                from app.services.wildcard_ast import extract_atomic_tags_from_text
                extracted_tags.update(extract_atomic_tags_from_text('\n'.join(choices)))
                
        try:
            db.commit()
        except Exception as err:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Error saving imported wildcards: {err}")
            
        # Also save extracted tags safely with categories
        try:
            all_tags = db.query(Tag).all()
            existing_tags = set(t.name.lower() for t in all_tags if t and t.name)
            for tag_item in extracted_tags:
                tag_name, tag_cat = tag_item if isinstance(tag_item, tuple) else (tag_item, "General")
                clean_tag = str(tag_name).replace('\x00', '').strip()
                if clean_tag and clean_tag.lower() not in existing_tags:
                    db.add(Tag(name=clean_tag, category=tag_cat))
                    existing_tags.add(clean_tag.lower())
            db.commit()
        except Exception as tag_err:
            print(f"Warning saving tags: {tag_err}")
            db.rollback()
            
        # Trigger sync to export these new wildcards to the workspace
        try:
            for db_w in db.query(Wildcard).all():
                export_wildcard_to_file(db_w)
        except Exception as e:
            print(f"Warning exporting wildcards: {e}")
        
        return {"ok": True, "imported_wildcards": imported_count, "extracted_tags": len(extracted_tags)}

    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Import error: {str(exc)}")


@router.post("/resync-tags")
def resync_all_wildcard_tags(db: Session = Depends(get_db)):
    """
    Parses all wildcards from the database and workspace files using WildcardASTEngine,
    extracts clean atomic tags with categories, and stores them in the tags database.
    """
    from app.services.wildcard_ast import extract_atomic_tags_from_text, WildcardASTEngine
    
    wildcards = db.query(Wildcard).all()
    all_extracted = []
    seen = set()
    
    for w in wildcards:
        content = w.content or "\n".join(w.entries or [])
        if content:
            tags = extract_atomic_tags_from_text(content)
            for name, cat in tags:
                nl = name.lower()
                if nl not in seen:
                    seen.add(nl)
                    all_extracted.append((name, cat))

    existing_tags = {t.name.lower(): t for t in db.query(Tag).all()}
    new_count = 0
    updated_count = 0
    
    for name, cat in all_extracted:
        nl = name.lower()
        if nl in existing_tags:
            t = existing_tags[nl]
            if (not t.category or t.category == "General") and cat and cat != "General":
                t.category = cat
                updated_count += 1
        else:
            db.add(Tag(name=name, category=cat))
            existing_tags[nl] = None
            new_count += 1
            
    db.commit()
    return {
        "ok": True,
        "total_tags_found": len(all_extracted),
        "new_tags_added": new_count,
        "tags_categorized": updated_count,
        "total_tags_in_db": db.query(Tag).count()
    }


from pydantic import BaseModel
from app.services.wildcard_ast import WildcardASTEngine

class LintRequest(BaseModel):
    template: str

@router.post("/lint")
def lint_wildcard_template(req: LintRequest):
    engine = WildcardASTEngine()
    engine.load_from_directory("wildcards")
    result = engine.lint_prompt(req.template)
    return result


