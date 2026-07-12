import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.models.knowledge import KnowledgeDocument
from app.services.ai.provider import MockAIProvider
from app.services.rag_engine import search_knowledge

import asyncio

def test_mock_ai_provider():
    provider = MockAIProvider()
    result = asyncio.run(provider.generate("hello", "you are an AI"))
    assert result == "[MOCK AI] Processed: hello"

def test_search_knowledge():
    db = SessionLocal()
    try:
        # Clear existing for clean test
        db.query(KnowledgeDocument).delete()
        db.commit()

        doc1 = KnowledgeDocument(title="Doc 1", content="Content 1", embedding=[1.0] + [0.0]*1535)
        doc2 = KnowledgeDocument(title="Doc 2", content="Content 2", embedding=[0.0, 1.0] + [0.0]*1534)
        db.add_all([doc1, doc2])
        db.commit()

        # search for [1.0, 0.0, ...]
        results = search_knowledge(db, [1.0] + [0.0]*1535, limit=1)
        assert len(results) == 1
        assert results[0].title == "Doc 1"

        # search for [0.0, 1.0, ...]
        results2 = search_knowledge(db, [0.0, 1.0] + [0.0]*1534, limit=1)
        assert len(results2) == 1
        assert results2[0].title == "Doc 2"
    finally:
        db.query(KnowledgeDocument).delete()
        db.commit()
        db.close()
