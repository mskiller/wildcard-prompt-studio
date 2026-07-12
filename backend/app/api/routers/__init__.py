from fastapi import APIRouter
from .prompts import router as prompts_router
from .wildcards import router as wildcards_router
from .tags import router as tags_router
from .images import router as images_router
from .generate import router as generate_router

router = APIRouter()

router.include_router(prompts_router, prefix="/prompts", tags=["prompts"])
router.include_router(wildcards_router, prefix="/wildcards", tags=["wildcards"])
router.include_router(tags_router, prefix="/tags", tags=["tags"])
router.include_router(images_router, prefix="/images", tags=["images"])
router.include_router(generate_router, prefix="/generate", tags=["generate"])
