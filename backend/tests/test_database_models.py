import pytest
from app.models.knowledge import KnowledgeDocument
from app.models.image import Image

def test_knowledge_document_model_attributes():
    doc = KnowledgeDocument(
        title="Test Doc",
        content="Test Content",
        category="optics",
        tags='["lighting", "cyberpunk"]',
        embedding=[0.1] * 384
    )
    assert doc.title == "Test Doc"
    assert doc.category == "optics"
    assert len(doc.embedding) == 384

def test_image_model_attributes():
    img = Image(
        filename="test_render.png",
        is_favorite=True,
        rating=5,
        aesthetic_score=8.7
    )
    assert img.is_favorite is True
    assert img.rating == 5
    assert img.aesthetic_score == 8.7
