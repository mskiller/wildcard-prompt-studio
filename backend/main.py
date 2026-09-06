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

@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(STATIC_IMAGES_DIR, exist_ok=True)
    watchdog_service.start()
    db = SessionLocal()
    try:
        await unified_rag_service.seed_default_knowledge_if_empty(db)
    finally:
        db.close()
    yield
    watchdog_service.stop()

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
