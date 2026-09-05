from fastapi import APIRouter
from .prompts import router as prompts_router
from .wildcards import router as wildcards_router
from .tags import router as tags_router
from .images import router as images_router
from .generate import router as generate_router
from .ai import router as ai_router
from .simulator import router as simulator_router
from .profiles import router as profiles_router
from .comfyui import router as comfyui_router
from .aesthetic import router as aesthetic_router

router = APIRouter()

router.include_router(prompts_router, prefix="/prompts", tags=["prompts"])
router.include_router(wildcards_router, prefix="/wildcards", tags=["wildcards"])
router.include_router(tags_router, prefix="/tags", tags=["tags"])
router.include_router(images_router, prefix="/images", tags=["images"])
router.include_router(generate_router, prefix="/generate", tags=["generate"])
router.include_router(ai_router, prefix="/ai", tags=["ai"])
router.include_router(simulator_router, prefix="/simulator", tags=["simulator"])
router.include_router(profiles_router, prefix="/profiles", tags=["profiles"])
router.include_router(comfyui_router, prefix="/comfyui", tags=["comfyui"])
router.include_router(aesthetic_router, prefix="/aesthetic", tags=["aesthetic"])


