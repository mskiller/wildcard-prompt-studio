import pytest
from fastapi.testclient import TestClient
from main import app
from app.database import SessionLocal
from app.models.image import Image
from app.models.prompt import Prompt

client = TestClient(app)

def test_gallery_search_favorite_and_rating():
    db = SessionLocal()
    try:
        p = Prompt(name="Cyber City", content="neon cyberpunk street in rain")
        db.add(p)
        db.commit()
        db.refresh(p)

        img = Image(filename="test_gallery_a.png", prompt_id=p.id, seed=1234, sampler_name="Euler a", is_favorite=False, rating=0)
        db.add(img)
        db.commit()
        db.refresh(img)

        # 1. Toggle favorite
        res = client.patch(f"/api/v1/images/{img.id}/favorite")
        assert res.status_code == 200
        assert res.json()["is_favorite"] is True

        # 2. Update rating
        res = client.patch(f"/api/v1/images/{img.id}/rating", json={"rating": 5})
        assert res.status_code == 200
        assert res.json()["rating"] == 5

        # 3. Filter by favorites
        res = client.get("/api/v1/images/gallery?is_favorite=true")
        assert res.status_code == 200
        assert any(i["id"] == img.id for i in res.json())

        # 4. Search keyword
        res = client.get("/api/v1/images/gallery?search=cyberpunk")
        assert res.status_code == 200
        assert any(i["id"] == img.id for i in res.json())

        # 5. Filter by sampler
        res = client.get("/api/v1/images/gallery?sampler=Euler a")
        assert res.status_code == 200
        assert any(i["id"] == img.id for i in res.json())
    finally:
        db.query(Image).filter(Image.filename == "test_gallery_a.png").delete()
        db.query(Prompt).filter(Prompt.name == "Cyber City").delete()
        db.commit()
        db.close()

def test_gallery_batch_actions_and_aesthetic_scoring():
    db = SessionLocal()
    try:
        p1 = Prompt(name="Batch 1", content="beautiful landscape sunset")
        p2 = Prompt(name="Batch 2", content="beautiful mountain sunrise")
        db.add_all([p1, p2])
        db.commit()
        db.refresh(p1)
        db.refresh(p2)

        img1 = Image(filename="batch_test_1.png", prompt_id=p1.id)
        img2 = Image(filename="batch_test_2.png", prompt_id=p2.id)
        db.add_all([img1, img2])
        db.commit()
        db.refresh(img1)
        db.refresh(img2)

        # Aesthetic scoring
        res = client.post(f"/api/v1/images/{img1.id}/score-aesthetic")
        assert res.status_code == 200
        assert res.json()["aesthetic_score"] is not None

        # Batch index RAG
        res = client.post("/api/v1/images/batch/index-rag", json={"image_ids": [img1.id, img2.id], "category": "gallery_vault"})
        assert res.status_code == 200
        assert res.json()["indexed_count"] == 2

        # Batch delete
        res = client.post("/api/v1/images/batch/delete", json={"image_ids": [img1.id, img2.id]})
        assert res.status_code == 200
        assert res.json()["deleted_count"] == 2
    finally:
        db.query(Image).filter(Image.filename.in_(["batch_test_1.png", "batch_test_2.png"])).delete()
        db.query(Prompt).filter(Prompt.name.in_(["Batch 1", "Batch 2"])).delete()
        db.commit()
        db.close()

def test_gallery_similar_and_sorting():
    db = SessionLocal()
    try:
        p1 = Prompt(name="Similar 1", content="serene calm lake at twilight with reflections")
        p2 = Prompt(name="Similar 2", content="calm peaceful lake at dusk with water reflections")
        p3 = Prompt(name="Different", content="neon red sports car racing on Tokyo highway")
        db.add_all([p1, p2, p3])
        db.commit()
        db.refresh(p1)
        db.refresh(p2)
        db.refresh(p3)

        img1 = Image(filename="sim_test_1.png", prompt_id=p1.id, rating=3, aesthetic_score=7.0)
        img2 = Image(filename="sim_test_2.png", prompt_id=p2.id, rating=5, aesthetic_score=8.5)
        img3 = Image(filename="sim_test_3.png", prompt_id=p3.id, rating=1, aesthetic_score=4.2)
        db.add_all([img1, img2, img3])
        db.commit()
        db.refresh(img1)
        db.refresh(img2)
        db.refresh(img3)

        # 1. Test similar renders
        res = client.get(f"/api/v1/images/{img1.id}/similar")
        assert res.status_code == 200
        similar_items = res.json()
        assert len(similar_items) >= 2
        # img2 (lake dusk) should be more similar than img3 (neon car)
        sim_ids = [item["id"] for item in similar_items]
        assert img2.id in sim_ids
        assert img3.id in sim_ids
        assert sim_ids.index(img2.id) < sim_ids.index(img3.id)

        # 2. Test min_rating filter
        res = client.get("/api/v1/images/gallery?min_rating=4")
        assert res.status_code == 200
        rating_ids = [item["id"] for item in res.json()]
        assert img2.id in rating_ids
        assert img1.id not in rating_ids
        assert img3.id not in rating_ids

        # 3. Test sort_by rating
        res = client.get("/api/v1/images/gallery?sort_by=rating")
        assert res.status_code == 200
        all_items = res.json()
        target_items = [item for item in all_items if item["id"] in [img1.id, img2.id, img3.id]]
        assert target_items[0]["id"] == img2.id  # rating 5 first

        # 4. Test sort_by aesthetic_score
        res = client.get("/api/v1/images/gallery?sort_by=aesthetic_score")
        assert res.status_code == 200
        all_items = res.json()
        target_items = [item for item in all_items if item["id"] in [img1.id, img2.id, img3.id]]
        assert target_items[0]["id"] == img2.id  # score 8.5 first
    finally:
        db.query(Image).filter(Image.filename.in_(["sim_test_1.png", "sim_test_2.png", "sim_test_3.png"])).delete()
        db.query(Prompt).filter(Prompt.name.in_(["Similar 1", "Similar 2", "Different"])).delete()
        db.commit()
        db.close()
