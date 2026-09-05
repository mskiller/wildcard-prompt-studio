import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.krea2_optimizer import (
    clean_buzzwords,
    format_quotes,
    Krea2Optimizer,
)
from app.services.ai.provider_manager import AIProviderManager, AIProvider


def test_clean_buzzwords_basic():
    """Verify legacy SD quality buzzwords are stripped from prompt."""
    raw_prompt = "masterpiece, 8k, absurdres, highres, a majestic dragon sleeping in a cave, hyper-detailed, trending on artstation, 4k"
    cleaned = clean_buzzwords(raw_prompt)
    assert "masterpiece" not in cleaned.lower()
    assert "absurdres" not in cleaned.lower()
    assert "highres" not in cleaned.lower()
    assert "8k" not in cleaned.lower()
    assert "4k" not in cleaned.lower()
    assert "hyper-detailed" not in cleaned.lower()
    assert "trending on artstation" not in cleaned.lower()
    assert "a majestic dragon sleeping in a cave" in cleaned


def test_clean_buzzwords_case_insensitive_and_mixed():
    """Verify case-insensitivity and punctuation cleanup in buzzwords removal."""
    raw_prompt = "A Cyberpunk City Street, ULTRA DETAILED, 8K, best quality, HDR"
    cleaned = clean_buzzwords(raw_prompt)
    assert cleaned == "A Cyberpunk City Street"


def test_format_quotes_unquoted():
    """Verify target phrases are automatically wrapped in double quotes."""
    prompt = "a neon sign that says Open 24/7 hanging on a wall"
    targets = ["Open 24/7"]
    formatted = format_quotes(prompt, targets)
    assert 'a neon sign that says "Open 24/7" hanging on a wall' in formatted


def test_format_quotes_already_quoted():
    """Verify target phrases already in double quotes are not double-quoted."""
    prompt = 'a neon sign that says "Open 24/7" hanging on a wall'
    targets = ["Open 24/7"]
    formatted = format_quotes(prompt, targets)
    assert '""Open 24/7""' not in formatted
    assert 'a neon sign that says "Open 24/7" hanging on a wall' in formatted


def test_format_quotes_multiple_targets():
    """Verify formatting multiple target phrases in a single prompt."""
    prompt = "a billboard with text Hello World and subtext Welcome Home"
    targets = ["Hello World", "Welcome Home"]
    formatted = format_quotes(prompt, targets)
    assert '"Hello World"' in formatted
    assert '"Welcome Home"' in formatted


def test_system_prompt_variant_presets():
    """Verify system prompt generation for Turbo, Medium, and Large variant presets."""
    optimizer = Krea2Optimizer()

    turbo_sys = optimizer.get_system_prompt("turbo")
    assert "concise" in turbo_sys.lower() or "fast" in turbo_sys.lower()
    assert "krea 2" in turbo_sys.lower() or "faithfulness" in turbo_sys.lower()

    medium_sys = optimizer.get_system_prompt("medium")
    assert "artistic" in medium_sys.lower() or "anime" in medium_sys.lower() or "illustration" in medium_sys.lower()

    large_sys = optimizer.get_system_prompt("large")
    assert "photorealism" in large_sys.lower() or "textures" in large_sys.lower() or "camera" in large_sys.lower()

    # Unknown variant defaults to turbo
    default_sys = optimizer.get_system_prompt("unknown_preset")
    assert default_sys == turbo_sys


@pytest.mark.asyncio
async def test_improve_prompt_with_provider_manager():
    """Verify improve_prompt cleans buzzwords, formats quotes, and calls provider manager."""
    optimizer = Krea2Optimizer()

    mock_provider = AsyncMock(spec=AIProvider)
    mock_provider.generate.return_value = "A high-resolution photograph of a sleeping cat wrapped in a blanket."

    manager = AIProviderManager()
    manager.register_provider("mock", mock_provider)

    raw_prompt = "masterpiece, 8k, a sleeping cat with tag Rest Easy"
    quote_targets = ["Rest Easy"]

    result = await optimizer.improve_prompt(
        prompt=raw_prompt,
        variant="large",
        quote_targets=quote_targets,
        clean_buzzwords_flag=True,
        provider_manager=manager,
    )

    assert result == "A high-resolution photograph of a sleeping cat wrapped in a blanket."
    mock_provider.generate.assert_called_once()
    
    call_kwargs = mock_provider.generate.call_args[1]
    # Input prompt passed to AI should be cleaned of buzzwords and quote formatted
    assert "masterpiece" not in call_kwargs["prompt"].lower()
    assert "8k" not in call_kwargs["prompt"].lower()
    assert '"Rest Easy"' in call_kwargs["prompt"]
    assert "photorealism" in call_kwargs["system_prompt"].lower() or "large" in call_kwargs["system_prompt"].lower()


@pytest.mark.asyncio
async def test_improve_prompt_without_provider_manager():
    """Verify improve_prompt returns cleaned/formatted prompt when provider manager is None."""
    optimizer = Krea2Optimizer()
    raw_prompt = "masterpiece, 4k, a futuristic vehicle displaying Speed Limit 100"
    
    result = await optimizer.improve_prompt(
        prompt=raw_prompt,
        variant="turbo",
        quote_targets=["Speed Limit 100"],
        clean_buzzwords_flag=True,
        provider_manager=None,
    )

    assert "masterpiece" not in result.lower()
    assert "4k" not in result.lower()
    assert '"Speed Limit 100"' in result


@pytest.mark.asyncio
async def test_krea2_optimizer_thinking_extraction_and_max_tokens():
    """Verify Krea2Optimizer parses thinking responses with extract_final_prompt and forwards max_tokens."""
    optimizer = Krea2Optimizer()

    mock_provider = AsyncMock(spec=AIProvider)
    mock_provider.generate.return_value = (
        "<think>\nAnalyzing prompt requirements and composition...\n</think>\n\n"
        "A magnificent castle on a cliff top during golden hour."
    )

    manager = AIProviderManager()
    manager.register_provider("mock", mock_provider)

    result = await optimizer.improve_prompt(
        prompt="a castle on a cliff",
        variant="turbo",
        provider_manager=manager,
        max_tokens=8192,
    )

    assert result == "A magnificent castle on a cliff top during golden hour."
    mock_provider.generate.assert_called_once()

    call_kwargs = mock_provider.generate.call_args[1]
    assert call_kwargs["max_tokens"] == 8192

