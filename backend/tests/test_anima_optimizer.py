import pytest
from unittest.mock import AsyncMock

from app.services.anima_optimizer import (
    clean_sd_weights,
    format_artist_tags,
    inject_quality_scores,
    AnimaOptimizer,
)
from app.services.ai.provider_manager import AIProviderManager, AIProvider


def test_clean_sd_weights():
    """Verify SD-style weight brackets like (tag:1.2) and ((tag)) are cleaned to tag."""
    raw_prompt = "(masterpiece:1.2), ((1girl)), solo, (blue eyes:0.9), ((scenic background))"
    cleaned = clean_sd_weights(raw_prompt)
    assert "(masterpiece:1.2)" not in cleaned
    assert "((1girl))" not in cleaned
    assert "masterpiece" in cleaned
    assert "1girl" in cleaned
    assert "blue eyes" in cleaned
    assert "scenic background" in cleaned
    
    # Specific test cases required by spec
    assert clean_sd_weights("(tag:1.2)") == "tag"
    assert clean_sd_weights("((tag))") == "tag"


def test_format_artist_tags():
    """Verify artist:name tags are formatted to @name."""
    raw_prompt = "1girl, solo, artist:shinkai_makoto, artist:gogh"
    formatted = format_artist_tags(raw_prompt)
    assert "artist:shinkai_makoto" not in formatted
    assert "artist:gogh" not in formatted
    assert "@shinkai_makoto" in formatted
    assert "@gogh" in formatted

    # Specific test case required by spec
    assert format_artist_tags("artist:name") == "@name"


def test_inject_quality_scores():
    """Verify quality score tags (score_7) are safely injected without duplicates."""
    raw_prompt = "1girl, solo, vibrant landscape"
    injected = inject_quality_scores(raw_prompt)
    assert "score_7" in injected

    # Safe injection: calling twice or when score_7 is already present does not duplicate
    already_has_score = "score_9, score_8, score_7, 1girl, solo"
    second_injection = inject_quality_scores(already_has_score)
    assert second_injection.count("score_7") == 1
    assert second_injection == already_has_score


def test_anima_optimizer_get_system_prompt():
    """Verify system prompt retrieval from AnimaOptimizer."""
    optimizer = AnimaOptimizer()
    
    sys_prompt = optimizer.get_system_prompt()
    assert isinstance(sys_prompt, str)
    assert len(sys_prompt) > 0
    assert "anima" in sys_prompt.lower() or "prompt" in sys_prompt.lower()

    # Variant support
    anime_prompt = optimizer.get_system_prompt("anime")
    assert isinstance(anime_prompt, str)


@pytest.mark.asyncio
async def test_improve_prompt_without_provider():
    """Verify improve_prompt cleans weights, formats artist tags, and injects quality scores."""
    optimizer = AnimaOptimizer()
    raw = "(1girl:1.2), ((solo)), artist:picasso, blue sky"
    
    result = await optimizer.improve_prompt(raw, provider_manager=None)
    assert "(1girl:1.2)" not in result
    assert "((solo))" not in result
    assert "artist:picasso" not in result
    assert "@picasso" in result
    assert "score_7" in result


@pytest.mark.asyncio
async def test_improve_prompt_with_provider():
    """Verify improve_prompt routes prompt through AIProviderManager."""
    optimizer = AnimaOptimizer()
    mock_provider = AsyncMock(spec=AIProvider)
    mock_provider.generate.return_value = "score_9, score_8, score_7, 1girl, solo, @picasso, blue sky, cinematic lighting"

    manager = AIProviderManager()
    manager.register_provider("mock", mock_provider)

    raw = "(1girl:1.2), artist:picasso, blue sky"
    result = await optimizer.improve_prompt(raw, provider_manager=manager)

    assert result == "score_9, score_8, score_7, 1girl, solo, @picasso, blue sky, cinematic lighting"
    mock_provider.generate.assert_called_once()
