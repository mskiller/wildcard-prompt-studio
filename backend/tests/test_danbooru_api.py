import pytest
from fastapi.testclient import TestClient
from main import app
from app.services.danbooru_service import danbooru_service

client = TestClient(app)
BASE_URL = "/api/v1/danbooru"

def test_danbooru_service_stats():
    resp = client.get(f"{BASE_URL}/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "ready" in data
    if data["ready"]:
        assert data["total_tags"] >= 30000
        assert data["total_cooccurrences"] >= 3000000
        assert len(data["categories"]) > 0

def test_danbooru_tags_search():
    resp = client.get(f"{BASE_URL}/tags?q=girl&limit=10")
    assert resp.status_code == 200
    tags = resp.json()
    assert isinstance(tags, list)
    assert len(tags) > 0
    assert any("girl" in t["tag"] for t in tags)

def test_danbooru_cooccurrences():
    resp = client.get(f"{BASE_URL}/cooccurrences?tag=1girl&limit=5")
    assert resp.status_code == 200
    coocs = resp.json()
    assert isinstance(coocs, list)
    assert len(coocs) > 0
    tags = [c["tag"] for c in coocs]
    assert "solo" in tags

def test_danbooru_recommend():
    payload = {"prompt": "1girl, cyber, glowing", "limit": 6}
    resp = client.post(f"{BASE_URL}/recommend", json=payload)
    assert resp.status_code == 200
    recs = resp.json()
    assert isinstance(recs, list)
    assert len(recs) > 0
    assert "tag" in recs[0]
    assert "score" in recs[0]
    assert "category" in recs[0]