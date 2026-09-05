import pytest
from app.services.async_rag import AsyncRAGEngine

@pytest.mark.asyncio
async def test_async_rag_engine_compute_embedding():
    engine = AsyncRAGEngine()
    # Test compute embedding returns a list of floats asynchronously without blocking
    embedding = await engine.compute_embedding_async("cyberpunk street with neon lights")
    assert isinstance(embedding, list)
    assert len(embedding) > 0
    assert all(isinstance(x, float) for x in embedding)
