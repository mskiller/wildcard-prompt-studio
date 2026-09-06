import pytest
from app.services.wildcard_ast import WildcardASTEngine, RootNode, TextNode, ChoiceNode, WildcardNode
from app.services.matrix_engine import MatrixEngine

def test_ast_exact_counting():
    engine = WildcardASTEngine(wildcards={
        "colors": ["red", "blue", "green"],
        "animals": ["cat", "dog"],
        "styles": ["anime", "photo", "oil", "sketch"]
    })
    
    # Simple choice: 3 options
    ast1 = engine.parse("{red|blue|green}")
    assert engine.count_permutations(ast1) == 3
    
    # Text + choices: 3 * 2 = 6
    ast2 = engine.parse("A {red|blue|green} {cat|dog}")
    assert engine.count_permutations(ast2) == 6
    
    # Wildcard expansion: 3 * 2 * 4 = 24
    ast3 = engine.parse("__colors__ __animals__ in __styles__ style")
    assert engine.count_permutations(ast3, expand_wildcards=True) == 24
    assert engine.count_permutations(ast3, expand_wildcards=False) == 1

def test_ast_direct_indexing():
    engine = WildcardASTEngine(wildcards={
        "colors": ["red", "blue"],
        "animals": ["cat", "dog"]
    })
    ast = engine.parse("{red|blue} {cat|dog}")
    assert engine.count_permutations(ast) == 4
    
    # 0: red cat, 1: red dog, 2: blue cat, 3: blue dog
    p0 = engine.get_permutation_at_index(ast, 0)
    p1 = engine.get_permutation_at_index(ast, 1)
    p2 = engine.get_permutation_at_index(ast, 2)
    p3 = engine.get_permutation_at_index(ast, 3)
    
    assert p0.strip() == "red cat"
    assert p1.strip() == "red dog"
    assert p2.strip() == "blue cat"
    assert p3.strip() == "blue dog"

def test_matrix_engine_slice_and_sample():
    matrix = MatrixEngine(wildcards={
        "w1": [f"item_{i}" for i in range(100)],
        "w2": [f"mod_{j}" for j in range(100)]
    })
    # 100 * 100 = 10,000 permutations
    res = matrix.get_matrix_slice("__w1__ __w2__", offset=500, limit=10, expand_wildcards=True)
    assert res["total_count"] == 10000
    assert res["offset"] == 500
    assert len(res["items"]) == 10
    assert res["items"][0]["index"] == 501  # 1-based index
    assert res["items"][0]["prompt"] == "item_5 mod_0"

    # Random sampling
    sample_res = matrix.get_matrix_sample("__w1__ __w2__", sample_size=25, seed=42, expand_wildcards=True)
    assert sample_res["total_count"] == 10000
    assert len(sample_res["items"]) == 25
    assert sample_res["is_sample"] is True

def test_nested_choices_and_recursive_wildcards():
    engine = WildcardASTEngine(wildcards={
        "nested": ["simple", "{fast|slow} car"],
        "sub": ["__nested__ edition"]
    })
    # nested has 1 ("simple") + 2 ("fast car", "slow car") = 3 permutations
    ast_nested = engine.parse("__nested__")
    assert engine.count_permutations(ast_nested, expand_wildcards=True) == 3
    assert engine.get_permutation_at_index(ast_nested, 0).strip() == "simple"
    assert engine.get_permutation_at_index(ast_nested, 1).strip() == "fast car"
    assert engine.get_permutation_at_index(ast_nested, 2).strip() == "slow car"

    # sub has 3 permutations
    ast_sub = engine.parse("__sub__")
    assert engine.count_permutations(ast_sub, expand_wildcards=True) == 3
    assert engine.get_permutation_at_index(ast_sub, 0).strip() == "simple edition"
    assert engine.get_permutation_at_index(ast_sub, 1).strip() == "fast car edition"
    assert engine.get_permutation_at_index(ast_sub, 2).strip() == "slow car edition"

def test_direct_indexing_out_of_bounds():
    engine = WildcardASTEngine()
    ast = engine.parse("{a|b}")
    assert engine.count_permutations(ast) == 2
    with pytest.raises(IndexError):
        engine.get_permutation_at_index(ast, -1)
    with pytest.raises(IndexError):
        engine.get_permutation_at_index(ast, 2)

def test_matrix_engine_count_permutations():
    matrix = MatrixEngine(wildcards={
        "c": ["red", "green"],
        "s": ["big", "small", "tiny"]
    })
    assert matrix.count_permutations("__c__ __s__", expand_wildcards=True) == 6
    assert matrix.count_permutations("__c__ __s__", expand_wildcards=False) == 1
