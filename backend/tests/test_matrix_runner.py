import pytest
from app.services.matrix_engine import MatrixEngine

def test_matrix_engine_combinations():
    engine = MatrixEngine()
    prompt = "{red|blue} {cat|dog}"
    combinations = engine.generate_matrix(prompt)
    assert len(combinations) == 4
    assert "red cat" in combinations
    assert "blue dog" in combinations

def test_matrix_engine_expand_wildcards_option():
    wildcards = {
        "color": ["crimson", "sapphire"],
        "size": ["tiny", "giant"]
    }
    engine = MatrixEngine(wildcards=wildcards)
    prompt = "{fast|slow} __color__ __size__"

    # When expand_wildcards is True, should produce 2 * 2 * 2 = 8 combinations
    combos_expanded = engine.generate_matrix(prompt, expand_wildcards=True)
    assert len(combos_expanded) == 8
    assert "fast crimson tiny" in combos_expanded
    assert "slow sapphire giant" in combos_expanded

    # When expand_wildcards is False, should only expand choices and keep wildcards literal
    combos_unexpanded = engine.generate_matrix(prompt, expand_wildcards=False)
    assert len(combos_unexpanded) == 2
    assert "fast __color__ __size__" in combos_unexpanded
    assert "slow __color__ __size__" in combos_unexpanded

def test_matrix_engine_wildcards_inside_choice_groups():
    wildcards = {
        "mskiller/mklan-female-card-anima": ["japanese idol woman", "cyberpunk hacker"],
        "actress": ["Scarlett", "Margot"]
    }
    engine = MatrixEngine(wildcards=wildcards)
    prompt = "1woman, {1::__mskiller/mklan-female-card-anima__|1::A woman, __actress__}{1::|1::, {6::medium|4::flat chest} breasts}"

    # Expand wildcards inside choice groups
    combos_expanded = engine.generate_matrix(prompt, expand_wildcards=True)
    # 4 options (2 from anima + 2 from actress) * 3 options (empty, medium, flat chest) = 12
    assert len(combos_expanded) == 12
    assert "1woman, japanese idol woman" in combos_expanded
    assert "1woman, japanese idol woman, medium breasts" in combos_expanded
    assert "1woman, A woman, Scarlett, flat chest breasts" in combos_expanded

    # Unexpanded: wildcards inside choice options stay literal
    combos_unexpanded = engine.generate_matrix(prompt, expand_wildcards=False)
    # 2 choices * 3 options = 6
    assert len(combos_unexpanded) == 6
    assert "1woman, __mskiller/mklan-female-card-anima__" in combos_unexpanded
    assert "1woman, A woman, __actress__, medium breasts" in combos_unexpanded

