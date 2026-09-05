import pytest
import random
import os
import tempfile
import yaml
from app.services.wildcard_ast import (
    WildcardASTEngine, TextNode, WildcardNode, ChoiceNode, ChoiceOption, RootNode
)
from app.services.matrix_engine import MatrixEngine

def test_parse_basic_ast():
    engine = WildcardASTEngine({"color": ["red", "blue"]})
    ast = engine.parse("A __color__ car")
    assert isinstance(ast, RootNode)
    assert len(ast.children) == 3
    assert isinstance(ast.children[0], TextNode)
    assert ast.children[0].text == "A "
    assert isinstance(ast.children[1], WildcardNode)
    assert ast.children[1].name == "color"
    assert isinstance(ast.children[2], TextNode)
    assert ast.children[2].text == " car"

def test_evaluate_basic_wildcard():
    engine = WildcardASTEngine({"color": ["red", "blue"]})
    random.seed(42)
    res = engine.expand_prompt("A __color__ car")
    assert res in ["A red car", "A blue car"]

def test_missing_wildcard():
    engine = WildcardASTEngine({"color": ["red", "blue"]})
    res = engine.expand_prompt("A __shape__ car")
    assert res == "A __shape__ car"

def test_nested_inline_choices():
    engine = WildcardASTEngine()
    random.seed(42)
    
    # Nested choice: {light {red|blue}|green}
    prompt = "A {light {red|blue}|green} car"
    ast = engine.parse(prompt)
    assert isinstance(ast.children[1], ChoiceNode)
    
    # Collect options over multiple evaluations
    results = set()
    for _ in range(50):
        results.add(engine.evaluate(ast))
    
    assert results == {"A light red car", "A light blue car", "A green car"}

def test_deeply_nested_choices():
    engine = WildcardASTEngine()
    prompt = "{a|{b|{c|d}}}"
    ast = engine.parse(prompt)
    results = set()
    for _ in range(100):
        results.add(engine.evaluate(ast))
    assert results == {"a", "b", "c", "d"}

def test_weighted_choices():
    engine = WildcardASTEngine()
    prompt = "{3$$optA|1$$optB}"
    ast = engine.parse(prompt)
    
    choice_node = ast.children[0]
    assert isinstance(choice_node, ChoiceNode)
    assert len(choice_node.options) == 2
    assert choice_node.options[0].weight == 3.0
    assert choice_node.options[1].weight == 1.0
    
    # Evaluate 1000 times to check weight distribution ratio (3:1 approx)
    counts = {"optA": 0, "optB": 0}
    random.seed(12345)
    for _ in range(1000):
        res = engine.evaluate(ast)
        counts[res] += 1
        
    assert counts["optA"] > 650
    assert counts["optB"] > 150

def test_weighted_choices_default_weight():
    engine = WildcardASTEngine()
    prompt = "{optA|2.5$$optB}"
    ast = engine.parse(prompt)
    
    choice_node = ast.children[0]
    assert choice_node.options[0].weight == 1.0
    assert choice_node.options[1].weight == 2.5

def test_wildcard_folder_paths():
    engine = WildcardASTEngine({
        "styles/art": ["impressionist", "cubist"],
        "characters/hero": ["knight", "paladin"]
    })
    random.seed(42)
    res = engine.expand_prompt("A __styles/art__ __characters/hero__")
    assert res in [
        "A impressionist knight",
        "A impressionist paladin",
        "A cubist knight",
        "A cubist paladin"
    ]

def test_directory_loading_with_subfolders():
    with tempfile.TemporaryDirectory() as temp_dir:
        sub_dir = os.path.join(temp_dir, "styles")
        os.makedirs(sub_dir)
        
        with open(os.path.join(temp_dir, "character.txt"), "w", encoding="utf-8") as f:
            f.write("elf\nknight\n")
            
        with open(os.path.join(sub_dir, "art.txt"), "w", encoding="utf-8") as f:
            f.write("oil painting\nwatercolor\n")
            
        engine = WildcardASTEngine()
        engine.load_from_directory(temp_dir)
        
        assert "character" in engine.wildcards
        assert set(engine.wildcards["character"]) == {"elf", "knight"}
        
        assert "styles/art" in engine.wildcards
        assert set(engine.wildcards["styles/art"]) == {"oil painting", "watercolor"}

def test_recursive_depth_safeguard():
    engine = WildcardASTEngine({
        "loop1": ["__loop2__"],
        "loop2": ["__loop1__"]
    })
    
    # Should stop expanding when max_depth is reached without crashing
    res = engine.expand_prompt("Test __loop1__", max_depth=5)
    assert "__loop1__" in res or "__loop2__" in res

def test_matrix_engine_basic_combinations():
    wildcards = {"color": ["red", "blue"]}
    matrix_eng = MatrixEngine(wildcards=wildcards)
    
    prompt = "A {warm|cool} __color__ car"
    combos = matrix_eng.generate_matrix(prompt)
    
    expected = [
        "A warm red car",
        "A warm blue car",
        "A cool red car",
        "A cool blue car"
    ]
    assert combos == expected

def test_matrix_engine_nested_choices():
    matrix_eng = MatrixEngine()
    prompt = "A {light {red|blue}|green} car"
    combos = matrix_eng.generate_matrix(prompt)
    
    expected = [
        "A light red car",
        "A light blue car",
        "A green car"
    ]
    assert combos == expected

def test_matrix_engine_max_limit():
    matrix_eng = MatrixEngine(max_limit=5)
    # 2 x 2 x 2 = 8 total combinations
    prompt = "{a|b} {1|2} {x|y}"
    combos = matrix_eng.generate_matrix(prompt)
    
    assert len(combos) == 5
    assert combos == ["a 1 x", "a 1 y", "a 2 x", "a 2 y", "b 1 x"]

def test_matrix_engine_unlimited_thousands():
    matrix_eng = MatrixEngine()
    # 10 x 10 x 3 = 300 total combinations (>100 limit)
    prompt = "{1|2|3|4|5|6|7|8|9|10} {a|b|c|d|e|f|g|h|i|j} {X|Y|Z}"
    combos = matrix_eng.generate_matrix(prompt)
    
    assert len(combos) == 300
    assert "1 a X" in combos
    assert "10 j Z" in combos

