import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.api.routers import router as api_router
from app.services.watchdog_service import watchdog_service
from app.database import SessionLocal
from app.services.unified_rag import unified_rag_service

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_IMAGES_DIR = os.path.join(BASE_DIR, "app", "static", "images")
os.makedirs(STATIC_IMAGES_DIR, exist_ok=True)

import logging

logger = logging.getLogger(__name__)

def backfill_unlinked_image_metadata():
    """Background startup task to link Prompts and extract metadata for any images lacking prompts."""
    try:
        from app.models.image import Image
        from app.api.routers.images import ensure_image_prompt_linked
        db = SessionLocal()
        try:
            unlinked = db.query(Image).filter(Image.prompt_id.is_(None)).all()
            for img in unlinked:
                ensure_image_prompt_linked(img, db)
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Metadata auto-healing completed with note: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(STATIC_IMAGES_DIR, exist_ok=True)
    watchdog_service.start()
    db = SessionLocal()
    try:
        await unified_rag_service.seed_default_knowledge_if_empty(db)
    except Exception as e:
        logger.warning(f"RAG pre-seeding deferred during startup: {e}")
    finally:
        db.close()
    try:
        backfill_unlinked_image_metadata()
    except Exception:
        pass
    yield
    watchdog_service.stop()
    unified_rag_service.close()

app = FastAPI(title="Wildcard Management Studio API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static/images", StaticFiles(directory=STATIC_IMAGES_DIR), name="images")

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {"status": "ok"}
