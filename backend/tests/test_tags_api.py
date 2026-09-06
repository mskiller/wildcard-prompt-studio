import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi.testclient import TestClient
from main import app
from app.services.wildcard_ast import (
    sanitize_single_tag,
    classify_tag_category,
    extract_atomic_tags_from_text
)

client = TestClient(app)
BASE_URL = "/api/v1"

def test_sanitize_single_tag_heuristics():
    assert sanitize_single_tag("feathers:1.3)") == "feathers"
    assert sanitize_single_tag("kinomoto sakura{4::") == "kinomoto sakura"
    assert sanitize_single_tag("princess king boo{1::1::") == "princess king boo"
    assert sanitize_single_tag("((cyberpunk))") == "cyberpunk"
    assert sanitize_single_tag("[photorealistic:1.2]") == "photorealistic"
    assert sanitize_single_tag("aged up{1::}") == "aged up"
    # Filter out sentence fragments
    assert sanitize_single_tag("bridges the green felt near solid yellow and red balls. Her right hand tightly grips a polished cue stick") is None
    # Filter out empty or purely numeric
    assert sanitize_single_tag("12345") is None
    assert sanitize_single_tag("   ") is None

def test_classify_tag_category():
    assert classify_tag_category("score_9") == "Quality / Score"
    assert classify_tag_category("8k resolution") == "Quality / Score"
    assert classify_tag_category("1girl") == "Character"
    assert classify_tag_category("black leather armor") == "Clothing"
    assert classify_tag_category("cinematic lighting") == "Lighting"
    assert classify_tag_category("85mm portrait") == "Camera"
    assert classify_tag_category("cyberpunk") == "Style"

def test_extract_atomic_tags_from_ast_text():
    text = "a {cyberpunk|steampunk} 1girl, wearing (black leather armor:1.2), cinematic lighting"
    extracted = extract_atomic_tags_from_text(text)
    names = [t[0] for t in extracted]
    assert "cyberpunk" in names
    assert "steampunk" in names
    assert "1girl" in names
    assert any("black leather armor" in n for n in names)
    assert "cinematic lighting" in names

def test_tag_search_and_category_endpoints():
    # Insert unique test tag
    unique_tag_name = "test_cyber_dragon_x99"
    create_resp = client.post(
        f"{BASE_URL}/tags/",
        json={"name": unique_tag_name, "category": "Character"}
    )
    assert create_resp.status_code == 200
    tag_id = create_resp.json()["id"]

    try:
        # Test search query
        search_resp = client.get(f"{BASE_URL}/tags/?q=dragon_x99")
        assert search_resp.status_code == 200
        items = search_resp.json()
        assert any(t["name"] == unique_tag_name for t in items)

        # Test category filter
        cat_resp = client.get(f"{BASE_URL}/tags/?category=Character&q=dragon_x99")
        assert cat_resp.status_code == 200
        assert len(cat_resp.json()) >= 1

        # Test categories breakdown endpoint
        cats_resp = client.get(f"{BASE_URL}/tags/categories")
        assert cats_resp.status_code == 200
        data = cats_resp.json()
        assert "total" in data
        assert "categories" in data

    finally:
        client.delete(f"{BASE_URL}/tags/{tag_id}")

def test_wildcard_create_auto_extracts_tags():
    wc_resp = client.post(
        f"{BASE_URL}/wildcards/",
        json={
            "filename": "test_auto_tag_wildcard.txt",
            "content": "bioluminescent glowing mushrooms, dark enchanted forest",
            "type": "txt"
        }
    )
    assert wc_resp.status_code == 200
    wc_id = wc_resp.json()["id"]

    try:
        # Check that the extracted tags exist
        search_resp = client.get(f"{BASE_URL}/tags/?q=bioluminescent")
        assert search_resp.status_code == 200
        tags = search_resp.json()
        assert any("bioluminescent" in t["name"].lower() for t in tags)
    finally:
        client.delete(f"{BASE_URL}/wildcards/{wc_id}")
