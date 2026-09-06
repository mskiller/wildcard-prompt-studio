import pytest
import time
from app.services.matrix_engine import MatrixEngine

def test_large_wildcard_default_safe_cap():
    # Simulate a large wildcard with 50,000 entries
    large_entries = [f"tag_{i}" for i in range(50000)]
    engine = MatrixEngine(wildcards={"large_tags": large_entries})
    
    # Prompt without explicit max_limit
    t0 = time.time()
    combos = engine.generate_matrix("__large_tags__")
    duration = time.time() - t0
    
    # Must complete fast (< 1.0s) and be capped at the safe limit
    assert duration < 1.0
    assert len(combos) <= MatrixEngine.DEFAULT_SAFE_LIMIT
    assert len(combos) > 0

def test_combinatorial_explosion_safety_cap():
    # 10 x 10000 = 100,000 combinations
    ten_choices = "{" + "|".join(f"c{i}" for i in range(10)) + "}"
    large_entries = [f"item_{i}" for i in range(10000)]
    engine = MatrixEngine(wildcards={"large_items": large_entries})
    
    prompt = f"{ten_choices} __large_items__"
    
    t0 = time.time()
    # Call with max_limit=100
    combos = engine.generate_matrix(prompt, max_limit=100)
    duration = time.time() - t0
    
    assert duration < 0.5
    assert len(combos) == 100

def test_matrix_engine_respects_custom_max_limit_within_bounds():
    large_entries = [f"item_{i}" for i in range(5000)]
    engine = MatrixEngine(wildcards={"items": large_entries})
    
    combos = engine.generate_matrix("__items__", max_limit=50)
    assert len(combos) == 50
    assert combos[0] == "item_0"
    assert combos[49] == "item_49"

def test_matrix_engine_hard_ceiling_prevents_excessive_allocation():
    large_entries = [f"item_{i}" for i in range(200000)]
    engine = MatrixEngine(wildcards={"huge": large_entries})
    
    # Even if caller passes a massive limit like 10,000,000, it must be capped at MAX_ALLOWED_LIMIT
    combos = engine.generate_matrix("__huge__", max_limit=10000000)
    assert len(combos) <= MatrixEngine.MAX_ALLOWED_LIMIT

def test_cartesian_product_explosion_capped_at_safe_limit():
    wc1 = [f"a_{i}" for i in range(5000)]
    wc2 = [f"b_{i}" for i in range(5000)]
    engine = MatrixEngine(wildcards={"wc1": wc1, "wc2": wc2})
    
    # 5,000 * 5,000 = 25,000,000 combinations without limit
    t0 = time.time()
    combos = engine.generate_matrix("__wc1__ __wc2__")
    duration = time.time() - t0
    
    # Must finish very fast and not freeze or OOM
    assert duration < 1.0
    assert len(combos) <= MatrixEngine.DEFAULT_SAFE_LIMIT

