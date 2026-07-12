import pytest
import random
from app.services.wildcard_engine import WildcardEngine

def test_basic_wildcard_replacement():
    engine = WildcardEngine({"color": ["red", "blue"]})
    random.seed(42)
    
    res = engine.expand_prompt("A __color__ car")
    assert res in ["A red car", "A blue car"]
    
def test_missing_wildcard():
    engine = WildcardEngine({"color": ["red", "blue"]})
    res = engine.expand_prompt("A __shape__ car")
    assert res == "A __shape__ car"

def test_inline_choices():
    engine = WildcardEngine()
    random.seed(42)
    
    res = engine.expand_prompt("A {red|blue|green} car")
    assert res in ["A red car", "A blue car", "A green car"]

def test_recursive_wildcard_replacement():
    engine = WildcardEngine({
        "color": ["red", "blue"],
        "vehicle": ["car", "truck"],
        "colored_vehicle": ["__color__ __vehicle__"]
    })
    random.seed(42)
    
    res = engine.expand_prompt("A __colored_vehicle__")
    assert any(res == f"A {c} {v}" for c in ["red", "blue"] for v in ["car", "truck"])

def test_inline_choice_recursive():
    engine = WildcardEngine({
        "color": ["red", "blue"]
    })
    random.seed(42)
    
    res = engine.expand_prompt("A {__color__|green} car")
    assert res in ["A red car", "A blue car", "A green car"]
    
def test_inline_choice_nested():
    engine = WildcardEngine()
    random.seed(42)
    
    res = engine.expand_prompt("A {light {red|blue}|green} car")
    assert res in ["A light red car", "A light blue car", "A green car"]

def test_infinite_recursion_safeguard():
    engine = WildcardEngine({
        "loop1": ["__loop2__"],
        "loop2": ["__loop1__"]
    })
    
    # Should not crash/hang, and will stop at max_depth
    res = engine.expand_prompt("Test __loop1__", max_depth=5)
    assert "Test __loop1__" in res or "Test __loop2__" in res
