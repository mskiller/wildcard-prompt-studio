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

def test_krea2_endpoint_with_rag():
    res = client.post("/api/v1/ai/krea2-improve", json={
        "prompt": "neon cyberpunk car driving through rain",
        "variant": "turbo",
        "use_rag": True
    })
    assert res.status_code == 200
    assert "improved_prompt" in res.json()

def test_anima_endpoint_with_rag():
    res = client.post("/api/v1/ai/anima-improve", json={
        "prompt": "1girl, silver hair, cat ears",
        "variant": "hybrid",
        "use_rag": True
    })
    assert res.status_code == 200
    assert "improved_prompt" in res.json()
