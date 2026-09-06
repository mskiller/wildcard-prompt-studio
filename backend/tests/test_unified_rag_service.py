import pytest
from app.database import SessionLocal
from app.services.unified_rag import unified_rag_service
from app.models.knowledge import KnowledgeDocument

@pytest.mark.asyncio
async def test_compute_embedding_dimensions():
    vec = await unified_rag_service.compute_embedding_async("cyberpunk rainy street")
    assert isinstance(vec, list)
    assert len(vec) == 384

@pytest.mark.asyncio
async def test_seed_and_search_knowledge():
    db = SessionLocal()
    try:
        await unified_rag_service.seed_default_knowledge_if_empty(db)
        docs = db.query(KnowledgeDocument).all()
        assert len(docs) >= 3

        results = await unified_rag_service.search_knowledge_async(db, "optics 85mm lens portrait", top_k=2)
        assert len(results) > 0
        assert "similarity_score" in results[0]
        assert results[0]["similarity_score"] > 0
    finally:
        db.close()

@pytest.mark.asyncio
async def test_crud_knowledge_document():
    db = SessionLocal()
    try:
        doc = await unified_rag_service.index_document_async(
            db, 
            title="Custom Test Rule", 
            content="Always use volumetric mist for fantasy landscapes", 
            category="optics", 
            tags=["mist", "fantasy"]
        )
        assert doc["title"] == "Custom Test Rule"
        doc_id = doc["id"]

        fetched = await unified_rag_service.get_documents_async(db, query="volumetric mist")
        assert any(d["id"] == doc_id for d in fetched)

        deleted = await unified_rag_service.delete_document_async(db, doc_id)
        assert deleted is True
    finally:
        db.close()
