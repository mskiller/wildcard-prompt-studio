import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from app.services.async_rag import AsyncRAGEngine, async_rag_engine

client = TestClient(app)


@pytest.mark.asyncio
async def test_rag_engine_initialization():
    engine = AsyncRAGEngine()
    assert hasattr(engine, "_knowledge_store")
    assert isinstance(engine._knowledge_store, list)
    assert len(engine._knowledge_store) >= 3


@pytest.mark.asyncio
async def test_rag_engine_search():
    engine = AsyncRAGEngine()
    results = await engine.search_knowledge_async("cyberpunk lighting", top_k=2)
    assert isinstance(results, list)
    assert len(results) <= 2
    if results:
        assert "similarity_score" in results[0]
        assert "title" in results[0]


@pytest.mark.asyncio
async def test_rag_engine_index():
    engine = AsyncRAGEngine()
    initial_count = len(engine._knowledge_store)
    doc = await engine.index_document_async(
        title="Test Doc",
        content="Test content for indexing",
        tags=["test", "unit"]
    )
    assert doc["title"] == "Test Doc"
    assert doc["id"] > 0
    assert len(engine._knowledge_store) == initial_count + 1


@pytest.mark.asyncio
async def test_rag_engine_stats():
    engine = AsyncRAGEngine()
    stats = await engine.get_stats_async()
    assert isinstance(stats, dict)
    assert "total_documents" in stats
    assert "total_tags" in stats
    assert "model_name" in stats
    assert stats["total_documents"] == len(engine._knowledge_store)


@pytest.mark.asyncio
async def test_rag_engine_get_documents():
    engine = AsyncRAGEngine()
    # List all documents
    docs = await engine.get_documents_async(query=None, tag=None)
    assert isinstance(docs, list)
    assert len(docs) == len(engine._knowledge_store)

    # Filter by tag
    cyberpunk_docs = await engine.get_documents_async(query=None, tag="cyberpunk")
    assert len(cyberpunk_docs) >= 1
    assert any("cyberpunk" in [t.lower() for t in d.get("tags", [])] for d in cyberpunk_docs)

    # Filter by query
    portrait_docs = await engine.get_documents_async(query="Portrait", tag=None)
    assert len(portrait_docs) >= 1


@pytest.mark.asyncio
async def test_rag_engine_delete_document():
    engine = AsyncRAGEngine()
    doc = await engine.index_document_async(
        title="Doc To Delete",
        content="This will be deleted",
        tags=["temp"]
    )
    doc_id = doc["id"]
    deleted = await engine.delete_document_async(doc_id)
    assert deleted is True

    # Deleting non-existent doc ID should return False
    deleted_again = await engine.delete_document_async(doc_id)
    assert deleted_again is False


@pytest.mark.asyncio
async def test_rag_engine_delete_non_existent_document():
    engine = AsyncRAGEngine()
    deleted = await engine.delete_document_async(999999)
    assert deleted is False


def test_api_rag_stats():
    response = client.get("/api/v1/ai/rag/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_documents" in data
    assert "total_tags" in data
    assert "model_name" in data


def test_api_rag_documents():
    response = client.get("/api/v1/ai/rag/documents")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert isinstance(data["documents"], list)

    # Test query param filtering
    res_filtered = client.get("/api/v1/ai/rag/documents?tag=lighting")
    assert res_filtered.status_code == 200
    data_filtered = res_filtered.json()
    assert "documents" in data_filtered


def test_api_rag_search():
    response = client.post(
        "/api/v1/ai/rag/search",
        json={"query": "cyberpunk lighting", "top_k": 2}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "cyberpunk lighting"
    assert "results" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) <= 2
    if data["results"]:
        first_result = data["results"][0]
        assert "id" in first_result
        assert "title" in first_result
        assert "content" in first_result
        assert "similarity_score" in first_result


def test_api_rag_search_invalid_parameters():
    # Test top_k <= 0 validation failure (gt=0 requirement)
    res_invalid_top_k = client.post(
        "/api/v1/ai/rag/search",
        json={"query": "test query", "top_k": 0}
    )
    assert res_invalid_top_k.status_code == 422

    res_negative_top_k = client.post(
        "/api/v1/ai/rag/search",
        json={"query": "test query", "top_k": -5}
    )
    assert res_negative_top_k.status_code == 422

    # Test missing required query field
    res_missing_query = client.post(
        "/api/v1/ai/rag/search",
        json={"top_k": 3}
    )
    assert res_missing_query.status_code == 422


def test_api_rag_index():
    # Test indexing document with explicit tags
    response = client.post(
        "/api/v1/ai/rag/index",
        json={"title": "API Index Test", "content": "Content for testing API index", "tags": ["api", "test"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "indexed"
    assert "document" in data
    assert data["document"]["title"] == "API Index Test"
    assert data["document"]["tags"] == ["api", "test"]

    # Test indexing document with default tags (empty list)
    res_default_tags = client.post(
        "/api/v1/ai/rag/index",
        json={"title": "API Index No Tags", "content": "Content without tags"}
    )
    assert res_default_tags.status_code == 200
    data_default = res_default_tags.json()
    assert data_default["status"] == "indexed"
    assert data_default["document"]["tags"] == []


def test_api_rag_delete_document():
    # Index doc first
    doc = client.post(
        "/api/v1/ai/rag/index",
        json={"title": "API Doc Delete Test", "content": "Delete me", "tags": ["api_test"]}
    ).json()["document"]
    doc_id = doc["id"]

    # Delete existing
    res_delete = client.delete(f"/api/v1/ai/rag/documents/{doc_id}")
    assert res_delete.status_code == 200
    assert res_delete.json()["status"] == "deleted"

    # Delete non-existent doc ID returns 404
    res_delete_404 = client.delete(f"/api/v1/ai/rag/documents/{doc_id}")
    assert res_delete_404.status_code == 404


def test_api_rag_delete_non_existent_document():
    res = client.delete("/api/v1/ai/rag/documents/999999")
    assert res.status_code == 404
