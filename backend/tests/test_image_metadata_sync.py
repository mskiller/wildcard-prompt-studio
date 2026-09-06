import os
import pytest
from app.database import SessionLocal
from app.models.image import Image
from app.models.prompt import Prompt
from app.services.image_metadata import extract_metadata_from_png
from app.api.routers.images import ensure_image_prompt_linked, STATIC_IMAGES_DIR
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_extract_metadata_from_png():
    test_path = os.path.join(STATIC_IMAGES_DIR, "MatrixSweep_Krea2_00187_.png")
    if not os.path.exists(test_path):
        pytest.skip("Test image not available in static directory")

    meta = extract_metadata_from_png(test_path)
    assert meta["prompt_text"] is not None
    assert "cybernetic woman" in meta["prompt_text"]
    assert meta["seed"] == 51
    assert meta["width"] == 896
    assert meta["height"] == 1152

def test_ensure_image_prompt_linked():
    test_fn = "MatrixSweep_Krea2_00187_.png"
    test_path = os.path.join(STATIC_IMAGES_DIR, test_fn)
    if not os.path.exists(test_path):
        pytest.skip("Test image not available in static directory")

    db = SessionLocal()
    try:
        img = db.query(Image).filter(Image.filename == test_fn).first()
        if not img:
            img = Image(filename=test_fn)
            db.add(img)
            db.commit()
            db.refresh(img)

        # Force unlinked state
        img.prompt_id = None
        img.prompt = None
        db.commit()
        db.refresh(img)

        prompt_text = ensure_image_prompt_linked(img, db)
        assert prompt_text is not None
        assert "cybernetic woman" in prompt_text
        assert img.prompt_id is not None

        # Verify through gallery API
        res = client.get(f"/api/v1/images/gallery?search={test_fn}")
        assert res.status_code == 200
        items = res.json()
        assert len(items) > 0
        target = next(i for i in items if i["filename"] == test_fn)
        assert target["prompt_content"] != ""
        assert "cybernetic woman" in target["prompt_content"]
    finally:
        db.close()
