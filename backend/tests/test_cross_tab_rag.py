import pytest
from app.database import SessionLocal
from app.services.krea2_optimizer import Krea2Optimizer
from app.services.anima_optimizer import AnimaOptimizer
from app.services.unified_rag import unified_rag_service
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_krea2_enrichment_with_rag():
    db = SessionLocal()
    try:
        await unified_rag_service.seed_default_knowledge_if_empty(db)
        optimizer = Krea2Optimizer()
        prompt = "a majestic dragon flying over snowy mountains"
        prompt_with_rag = await optimizer.enrich_prompt_with_rag(db, prompt)
        assert len(prompt_with_rag) > len(prompt)
        assert "RAG Formatting & Style Guidelines:" in prompt_with_rag
    finally:
        db.close()

@pytest.mark.asyncio
async def test_anima_enrichment_with_rag():
    db = SessionLocal()
    try:
        await unified_rag_service.seed_default_knowledge_if_empty(db)
        optimizer = AnimaOptimizer()
        prompt = "1girl, solo, school uniform"
        prompt_with_rag = await optimizer.enrich_prompt_with_rag(db, prompt)
        assert len(prompt_with_rag) > len(prompt)
        assert "ANIMA Model Guidelines" in prompt_with_rag or "Tag Hierarchy" in prompt_with_rag or "RAG" in prompt_with_rag
    finally:
        db.close()

from unittest.mock import AsyncMock
from app.dependencies import get_provider_manager
from app.services.ai.provider_manager import AIProviderManager

@pytest.fixture
def mock_provider_manager():
    mock = AsyncMock(spec=AIProviderManager)
    mock.list_providers.return_value = ["mock_ai"]
    mock.generate.return_value = "improved output prompt"
    app.dependency_overrides[get_provider_manager] = lambda: mock
    yield mock
    app.dependency_overrides.pop(get_provider_manager, None)

def test_krea2_endpoint_with_rag(mock_provider_manager):
    res = client.post("/api/v1/ai/krea2-improve", json={
        "prompt": "neon cyberpunk car driving through rain",
        "variant": "turbo",
        "use_rag": True
    })
    assert res.status_code == 200
    assert res.json()["improved_prompt"] == "improved output prompt"
    # Verify RAG guidelines were passed in system_prompt
    called_kwargs = mock_provider_manager.generate.call_args.kwargs
    assert "RAG Formatting & Style Guidelines:" in called_kwargs["system_prompt"]

def test_anima_endpoint_with_rag(mock_provider_manager):
    res = client.post("/api/v1/ai/anima-improve", json={
        "prompt": "1girl, silver hair, cat ears",
        "variant": "hybrid",
        "use_rag": True
    })
    assert res.status_code == 200
    assert res.json()["improved_prompt"] == "improved output prompt"
    called_kwargs = mock_provider_manager.generate.call_args.kwargs
    assert "RAG Formatting & Style Guidelines:" in called_kwargs["system_prompt"]

@pytest.mark.asyncio
async def test_rag_exception_resilience():
    # Test that optimizer recovers cleanly if RAG search encounters an error
    optimizer = Krea2Optimizer()
    guidelines = await optimizer.get_rag_guidelines(None, "sample prompt")
    assert guidelines == ""
