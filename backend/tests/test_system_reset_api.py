import pytest
from fastapi.testclient import TestClient
from main import app
from app.database import SessionLocal
from app.models.wildcard import Wildcard
from app.models.tag import Tag

client = TestClient(app)

def test_system_stats_endpoint():
    resp = client.get("/api/v1/system/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "tags_count" in data
    assert "wildcards_count" in data
    assert "prompts_count" in data
    assert "danbooru" in data

def test_batch_delete_wildcards():
    db = SessionLocal()
    try:
        # Create 2 temp wildcards
        w1 = Wildcard(filename="test_temp_w1.txt", content="tag1\ntag2")
        w2 = Wildcard(filename="test_temp_w2.txt", content="tag3\ntag4")
        db.add_all([w1, w2])
        db.commit()
        db.refresh(w1)
        db.refresh(w2)
        w1_id, w2_id = w1.id, w2.id

        # Batch delete
        resp = client.post("/api/v1/wildcards/batch-delete", json={"ids": [w1_id, w2_id]})
        assert resp.status_code == 200
        assert resp.json()["deleted_count"] == 2

        # Verify gone
        assert db.query(Wildcard).filter(Wildcard.id.in_([w1_id, w2_id])).count() == 0
    finally:
        db.close()

def test_factory_reset_guard():
    # Factory reset without 'RESET' confirm should be rejected
    resp = client.post("/api/v1/system/reset", json={"target": "all", "confirm": "no"})
    assert resp.status_code == 400


def test_clear_prompts_with_linked_images_and_tags():
    from app.models.prompt import Prompt
    from app.models.image import Image
    from app.models.version import PromptVersion

    import uuid
    db = SessionLocal()
    try:
        # Create prompt with version and image
        p = Prompt(name="Test Prompt With Image", content="masterpiece, 1girl")
        db.add(p)
        db.commit()
        db.refresh(p)

        pv = PromptVersion(prompt_id=p.id, content="v1 content")
        img = Image(filename=f"test_linked_{uuid.uuid4().hex}.png", prompt_id=p.id)
        db.add_all([pv, img])
        db.commit()
        db.refresh(img)

        # Clear prompts via API
        resp = client.post("/api/v1/system/reset", json={"target": "prompts"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["target"] == "prompts"

        # Image should still exist in gallery, with prompt_id set to None
        db.refresh(img)
        assert img.prompt_id is None

        # Clean up test image
        db.delete(img)
        db.commit()
    finally:
        db.close()