import time
import pytest
from app.services.matrix_engine import MatrixEngine
from app.services.wildcard_ast import WildcardASTEngine


def test_large_combinatorial_space_benchmark():
    """
    Benchmark a combinatorial template with 10,000,000 permutations.
    Verifies that:
    1. count_permutations executes in < 5ms and returns exact count.
    2. get_permutation_at_index at index 500,000 executes in < 1ms.
    3. get_matrix_slice(offset=500000, limit=10) executes in < 5ms.
    4. get_matrix_sample(sample_size=50) executes in < 10ms.
    """
    # 10 x 100 x 100 x 100 = 10,000,000 permutations (> 1,000,000)
    wildcards = {
        "w1": [f"item_{i}" for i in range(10)],
        "w2": [f"color_{i}" for i in range(100)],
        "w3": [f"style_{i}" for i in range(100)],
        "w4": [f"setting_{i}" for i in range(100)],
    }
    engine = MatrixEngine(wildcards=wildcards)
    prompt = "__w1__ __w2__ __w3__ __w4__"

    # Warm-up run to eliminate JIT/import cold cache jitter
    engine.count_permutations(prompt)

    # 1. count_permutations executes in < 5ms and returns exact count
    t0 = time.perf_counter()
    total_count = engine.count_permutations(prompt)
    t_count_ms = (time.perf_counter() - t0) * 1000.0

    assert total_count == 10_000_000, f"Expected 10,000,000 permutations, got {total_count}"
    assert t_count_ms < 5.0, f"count_permutations took {t_count_ms:.3f}ms (expected < 5ms)"

    # 2. get_permutation_at_index at index 500,000 executes in < 1ms
    ast = engine.ast_engine.parse(prompt)
    # Warm-up
    engine.ast_engine.get_permutation_at_index(ast, 0)

    t0 = time.perf_counter()
    perm_500k = engine.ast_engine.get_permutation_at_index(ast, 500_000)
    t_perm_ms = (time.perf_counter() - t0) * 1000.0

    assert isinstance(perm_500k, str)
    assert len(perm_500k.strip()) > 0
    assert t_perm_ms < 1.0, f"get_permutation_at_index took {t_perm_ms:.3f}ms (expected < 1ms)"

    # 3. get_matrix_slice(offset=500000, limit=10) executes in < 5ms
    # Warm-up
    engine.get_matrix_slice(prompt, offset=0, limit=2)

    t0 = time.perf_counter()
    slice_res = engine.get_matrix_slice(prompt, offset=500_000, limit=10)
    t_slice_ms = (time.perf_counter() - t0) * 1000.0

    assert slice_res["total_count"] == 10_000_000
    assert slice_res["offset"] == 500_000
    assert len(slice_res["items"]) == 10
    assert t_slice_ms < 5.0, f"get_matrix_slice took {t_slice_ms:.3f}ms (expected < 5ms)"

    # 4. get_matrix_sample(sample_size=50) executes in < 10ms
    # Warm-up
    engine.get_matrix_sample(prompt, sample_size=5, seed=1)

    t0 = time.perf_counter()
    sample_res = engine.get_matrix_sample(prompt, sample_size=50, seed=42)
    t_sample_ms = (time.perf_counter() - t0) * 1000.0

    assert sample_res["total_count"] == 10_000_000
    assert len(sample_res["items"]) == 50
    assert sample_res["is_sample"] is True
    assert t_sample_ms < 10.0, f"get_matrix_sample took {t_sample_ms:.3f}ms (expected < 10ms)"
