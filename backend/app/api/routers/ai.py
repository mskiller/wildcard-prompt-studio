import json
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import httpx

from app.dependencies import get_db, get_krea2_optimizer, get_anima_optimizer, get_provider_manager
from app.schemas.ai import PromptImproveRequest, Krea2ImproveRequest, AnimaImproveRequest
from app.services.prompt_assistant import improve_prompt
from app.services.krea2_optimizer import Krea2Optimizer
from app.services.anima_optimizer import AnimaOptimizer
from app.services.ai.provider_manager import AIProviderManager
from app.services.comfyui_connector import ComfyUIConnector
from app.services.ai.utils import get_url_candidates
from app.services.async_rag import async_rag_engine
from app.services.ai.vision_service import vision_service
from app.services.prompt_chat_service import prompt_chat_service

router = APIRouter()

class PromptImproveResponse(BaseModel):
    improved_prompt: str

class PromptChanges(BaseModel):
    added: List[str] = Field(default_factory=list)
    removed: List[str] = Field(default_factory=list)

class ChatRefineRequest(BaseModel):
    current_prompt: str
    user_message: str
    chat_history: Optional[List[Dict[str, str]]] = Field(default_factory=list)
    provider: Optional[str] = "auto"
    target_model: Optional[str] = None
    use_rag: bool = False
    max_tokens: Optional[int] = 4096

class ChatRefineResponse(BaseModel):
    updated_prompt: str
    explanation: str
    changes: PromptChanges


@router.post("/improve", response_model=PromptImproveResponse)
async def improve_prompt_endpoint(request: PromptImproveRequest, db: Session = Depends(get_db)):
    result = await improve_prompt(
        db_session=db, 
        prompt=request.prompt, 
        target_model=request.target_model,
        kobold_url=request.kobold_url,
        use_rag=request.use_rag,
        max_tokens=request.max_tokens,
    )
    return {"improved_prompt": result}

@router.post("/krea2-improve", response_model=PromptImproveResponse)
async def krea2_improve_prompt_endpoint(
    request: Krea2ImproveRequest,
    optimizer: Krea2Optimizer = Depends(get_krea2_optimizer),
    provider_manager: AIProviderManager = Depends(get_provider_manager),
):
    if request.provider and request.provider not in provider_manager.list_providers():
        if request.provider == "kobold":
            from app.services.ai.kobold_provider import KoboldCppProvider
            provider_manager.register_provider("kobold", KoboldCppProvider())
        elif request.provider == "ollama":
            from app.services.ai.ollama_provider import OllamaProvider
            provider_manager.register_provider("ollama", OllamaProvider())
        elif request.provider == "gemini":
            from app.services.ai.gemini_provider import GeminiProvider
            provider_manager.register_provider("gemini", GeminiProvider())

    if request.provider and request.provider in provider_manager.list_providers():
        provider_manager.set_active_provider(request.provider)

    improved = await optimizer.improve_prompt(
        prompt=request.prompt,
        variant=request.variant,
        quote_targets=request.quote_targets,
        clean_buzzwords_flag=request.clean_buzzwords,
        provider_manager=provider_manager,
        max_tokens=request.max_tokens,
    )
    return {"improved_prompt": improved}

@router.post("/anima-improve", response_model=PromptImproveResponse)
async def anima_improve_prompt_endpoint(
    request: AnimaImproveRequest,
    optimizer: AnimaOptimizer = Depends(get_anima_optimizer),
    provider_manager: AIProviderManager = Depends(get_provider_manager),
):
    if request.provider and request.provider not in provider_manager.list_providers():
        if request.provider in ["kobold", "koboldcpp"]:
            from app.services.ai.kobold_provider import KoboldCppProvider
            provider_manager.register_provider(request.provider, KoboldCppProvider())
        elif request.provider == "ollama":
            from app.services.ai.ollama_provider import OllamaProvider
            provider_manager.register_provider("ollama", OllamaProvider())
        elif request.provider == "gemini":
            from app.services.ai.gemini_provider import GeminiProvider
            provider_manager.register_provider("gemini", GeminiProvider())

    if request.provider and request.provider in provider_manager.list_providers():
        provider_manager.set_active_provider(request.provider)

    if request.model:
        active_p = provider_manager.get_active_provider()
        if active_p and hasattr(active_p, "model"):
            active_p.model = request.model

    improved = await optimizer.improve_prompt(
        prompt=request.prompt,
        variant=request.variant or "hybrid",
        clean_weights_flag=request.clean_weights if request.clean_weights is not None else True,
        inject_scores_flag=request.add_quality_tags if request.add_quality_tags is not None else True,
        provider_manager=provider_manager,
        max_tokens=request.max_tokens,
    )
    return {"improved_prompt": improved}


class ConnectionTestRequest(BaseModel):
    provider: str
    url: Optional[str] = None

@router.post("/integrations/test")
async def test_integration_connection(req: ConnectionTestRequest):
    provider = req.provider.lower()
    try:
        if provider == "comfyui":
            connector = ComfyUIConnector()
            info = await connector.get_object_info(base_url=req.url)
            return {"status": "ok", "provider": "comfyui", "nodes_count": len(info) if isinstance(info, dict) else 0}
        elif provider in ["kobold", "koboldcpp"]:
            candidates = get_url_candidates(req.url or "http://host.docker.internal:5001", default_port=5001)
            for c in candidates:
                try:
                    async with httpx.AsyncClient(timeout=4.0) as client:
                        r = await client.get(f"{c}/v1/models")
                        if r.status_code in [200, 404, 405]:
                            return {"status": "ok", "provider": "kobold"}
                except Exception:
                    continue
            raise HTTPException(status_code=502, detail="KoboldCpp server unreachable")
        elif provider == "ollama":
            candidates = get_url_candidates(req.url or "http://host.docker.internal:11434", default_port=11434)
            for c in candidates:
                try:
                    async with httpx.AsyncClient(timeout=4.0) as client:
                        r = await client.get(f"{c}/api/tags")
                        if r.status_code == 200:
                            return {"status": "ok", "provider": "ollama", "models": r.json().get("models", [])}
                except Exception:
                    continue
            raise HTTPException(status_code=502, detail="Ollama server unreachable")
        else:
            raise HTTPException(status_code=400, detail=f"Unknown provider '{provider}'")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to connect to {provider}: {str(e)}")

class RAGSearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=3, gt=0)

class RAGIndexRequest(BaseModel):
    title: str
    content: str
    tags: List[str] = Field(default_factory=list)

class RAGDocumentItem(BaseModel):
    id: int
    title: str
    content: str
    tags: List[str] = Field(default_factory=list)

class RAGSearchResultItem(RAGDocumentItem):
    similarity_score: float

class RAGSearchResponse(BaseModel):
    query: str
    results: List[RAGSearchResultItem]

class RAGIndexResponse(BaseModel):
    status: str
    document: RAGDocumentItem

class RAGStatsResponse(BaseModel):
    total_documents: int
    total_tags: int
    model_name: str

class RAGDocumentsResponse(BaseModel):
    documents: List[RAGDocumentItem]

class RAGDeleteResponse(BaseModel):
    status: str
    doc_id: int

@router.post("/rag/search", response_model=RAGSearchResponse)
async def rag_search_endpoint(req: RAGSearchRequest):
    results = await async_rag_engine.search_knowledge_async(req.query, top_k=req.top_k)
    return {"query": req.query, "results": results}

@router.post("/rag/index", response_model=RAGIndexResponse)
async def rag_index_endpoint(req: RAGIndexRequest):
    doc = await async_rag_engine.index_document_async(req.title, req.content, tags=req.tags)
    return {"status": "indexed", "document": doc}

@router.get("/rag/stats", response_model=RAGStatsResponse)
async def rag_stats_endpoint():
    stats = await async_rag_engine.get_stats_async()
    return stats

@router.get("/rag/documents", response_model=RAGDocumentsResponse)
async def rag_get_documents_endpoint(query: Optional[str] = None, tag: Optional[str] = None):
    documents = await async_rag_engine.get_documents_async(query=query, tag=tag)
    return {"documents": documents}

@router.delete("/rag/documents/{doc_id}", response_model=RAGDeleteResponse)
async def rag_delete_document_endpoint(doc_id: int):
    deleted = await async_rag_engine.delete_document_async(doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Document with ID {doc_id} not found")
    return {"status": "deleted", "doc_id": doc_id}

@router.post("/vision/describe")
async def vision_describe_endpoint(
    file: UploadFile = File(...),
    variant: str = Form("turbo"),
    provider: str = Form("auto"),
    max_tokens: int = Form(4096),
):
    image_bytes = await file.read()
    result = await vision_service.describe_image(
        image_bytes, variant=variant, provider=provider, max_tokens=max_tokens
    )
    return result

@router.post("/vision/extract-style")
async def vision_extract_style_endpoint(
    file: UploadFile = File(...),
    provider: str = Form("auto"),
    index_rag: bool = Form(False)
):
    image_bytes = await file.read()
    result = await vision_service.extract_style_descriptors(image_bytes, provider=provider)
    if index_rag and "descriptors" in result:
        desc = result["descriptors"]
        content_str = json.dumps(desc)
        await async_rag_engine.index_document_async("Extracted Vision Style", content_str, tags=["vision", "extracted_style"])
    return result

@router.post("/chat-refine", response_model=ChatRefineResponse)
async def chat_refine_endpoint(
    request: ChatRefineRequest,
    provider_manager: AIProviderManager = Depends(get_provider_manager),
):
    if request.provider and request.provider != "auto" and request.provider not in provider_manager.list_providers():
        if request.provider in ["kobold", "koboldcpp"]:
            from app.services.ai.kobold_provider import KoboldCppProvider
            provider_manager.register_provider(request.provider, KoboldCppProvider())
        elif request.provider == "ollama":
            from app.services.ai.ollama_provider import OllamaProvider
            provider_manager.register_provider(request.provider, OllamaProvider())
        elif request.provider == "gemini":
            from app.services.ai.gemini_provider import GeminiProvider
            provider_manager.register_provider(request.provider, GeminiProvider())

    if request.provider and request.provider in provider_manager.list_providers():
        provider_manager.set_active_provider(request.provider)

    result = await prompt_chat_service.refine_prompt_chat(
        current_prompt=request.current_prompt,
        user_message=request.user_message,
        chat_history=request.chat_history,
        provider=request.provider,
        target_model=request.target_model,
        use_rag=request.use_rag,
        provider_manager=provider_manager,
        max_tokens=request.max_tokens or 4096,
    )
    return result

