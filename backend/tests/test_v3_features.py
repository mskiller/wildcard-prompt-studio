import pytest
from app.services.ai.vision_service import vision_service
from app.services.wildcard_ast import WildcardASTEngine

@pytest.mark.asyncio
async def test_vision_service_describe():
    mock_bytes = b"fake_png_binary_data"
    result = await vision_service.describe_image(mock_bytes, variant="turbo", provider="ollama")
    assert "prompt" in result
    assert result["variant"] == "turbo"
    assert result["provider_used"] == "ollama"

@pytest.mark.asyncio
async def test_vision_service_koboldcpp():
    mock_bytes = b"fake_png_binary_data"
    result = await vision_service.describe_image(mock_bytes, variant="large", provider="koboldcpp")
    assert "prompt" in result
    assert result["variant"] == "large"
    assert result["provider_used"] == "koboldcpp"

def test_ast_macros_and_variables():
    engine = WildcardASTEngine()
    
    # Test variable assignment & ref
    prompt_var = "$hero = dragon; A portrait of a $hero"
    ast_var = engine.parse(prompt_var)
    res_var = engine.evaluate(ast_var)
    assert "A portrait of a dragon" in res_var

    # Test macro $range(1, 5)
    prompt_range = "Value: $range(10, 10)"
    ast_range = engine.parse(prompt_range)
    res_range = engine.evaluate(ast_range)
    assert res_range == "Value: 10"

    # Test macro $repeat(3, test)
    prompt_repeat = "$repeat(3, cat)"
    ast_repeat = engine.parse(prompt_repeat)
    res_repeat = engine.evaluate(ast_repeat)
    assert res_repeat == "cat, cat, cat"

def test_ast_linter_and_danbooru_tags():
    engine = WildcardASTEngine()
    
    # Lint mismatched braces
    lint_res = engine.lint_prompt("A {red|blue dragon")
    assert not lint_res["is_valid"]
    assert len(lint_res["errors"]) > 0

    # Categorize Danbooru tags
    tag_res = engine.categorize_danbooru_tags("by artist_name, hatsune miku, genshin impact, masterpiece, 1girl")
    categories = {item["tag"]: item["category"] for item in tag_res}
    
    assert categories["by artist_name"] == "artist"
    assert categories["hatsune miku"] == "character"
    assert categories["genshin impact"] == "copyright"
    assert categories["masterpiece"] == "meta"
    assert categories["1girl"] == "character"
