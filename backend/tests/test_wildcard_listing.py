import pytest
from fastapi.testclient import TestClient
from main import app
from app.database import SessionLocal
from app.models.wildcard import Wildcard

client = TestClient(app)

def test_get_wildcards_default_metadata_only():
    db = SessionLocal()
    try:
        w = Wildcard(
            filename="test_fast_listing.txt",
            file_path="/wildcards/test_fast_listing.txt",
            type="txt",
            content="big content" * 100,
            entries=["entry1", "entry2"]
        )
        db.add(w)
        db.commit()
        db.refresh(w)

        # 1. Default listing: should not include heavy content
        res = client.get("/api/v1/wildcards/")
        assert res.status_code == 200
        items = res.json()
        assert len(items) > 0
        matching = [item for item in items if item["id"] == w.id]
        assert len(matching) == 1
        assert matching[0]["filename"] == "test_fast_listing.txt"
        assert matching[0]["content"] == ""
        assert matching[0]["entries"] == []

        # 2. Listing with include_content=True
        res_full = client.get("/api/v1/wildcards/?include_content=true")
        assert res_full.status_code == 200
        matching_full = [item for item in res_full.json() if item["id"] == w.id]
        assert len(matching_full) == 1
        assert "big content" in matching_full[0]["content"]

        # 3. Direct GET /{id} returns content
        res_single = client.get(f"/api/v1/wildcards/{w.id}")
        assert res_single.status_code == 200
        assert "big content" in res_single.json()["content"]
    finally:
        db.query(Wildcard).filter(Wildcard.filename == "test_fast_listing.txt").delete()
        db.commit()
        db.close()
