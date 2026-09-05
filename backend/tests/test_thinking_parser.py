import pytest
from app.services.ai.thinking_parser import extract_final_prompt


def test_extract_final_prompt_gemma4_channel():
    """Test extracting prompt from Gemma 4 <|channel>text format."""
    # Basic channel format
    raw = "<|channel>thought\nAnalyzing request for prompt...\n<|channel>text\nA glowing magical forest at twilight."
    assert extract_final_prompt(raw) == "A glowing magical forest at twilight."

    # Channel format with residual tags (<|channel> and <|channel|>)
    raw_residual = "<|channel>thought\nDeep thinking\n<|channel>text\nCyberpunk detective in rain <|channel>"
    assert extract_final_prompt(raw_residual) == "Cyberpunk detective in rain"

    raw_residual_bar = "<|channel>thought\nDeep thinking\n<|channel>text\nCyberpunk detective in rain <|channel|>"
    assert extract_final_prompt(raw_residual_bar) == "Cyberpunk detective in rain"

    # Multiple text channel tags (should return after the last one)
    raw_multiple = "<|channel>thought\nThinking\n<|channel>text\nDraft 1\n<|channel>text\nFinal prompt version"
    assert extract_final_prompt(raw_multiple) == "Final prompt version"


def test_extract_final_prompt_xml_think():
    """Test extracting prompt from XML style <think> tags."""
    raw = "<think>\nConsider lighting and composition.\nUse soft morning light.\n</think>\nPortrait of a warrior holding a sword."
    assert extract_final_prompt(raw) == "Portrait of a warrior holding a sword."


def test_extract_final_prompt_unthinking_mode():
    """Test raw prompt pass-through when no thinking tags exist."""
    raw = "   An astronaut riding a horse on Mars, photorealistic   "
    assert extract_final_prompt(raw) == "An astronaut riding a horse on Mars, photorealistic"


def test_extract_final_prompt_empty():
    """Test empty/None inputs return empty string."""
    assert extract_final_prompt(None) == ""
    assert extract_final_prompt("") == ""
    assert extract_final_prompt("   \n\t  ") == ""


def test_extract_final_prompt_header_fallback():
    """Test regex fallback when text contains <|channel>thought but lacks <|channel>text."""
    # Krea 2 Prompt header with preamble before <|channel>thought
    raw_preamble = "Preamble metadata\n<|channel>thought\nReasoning about details...\nKrea 2 Prompt: A majestic owl perched on a crystal tree."
    assert extract_final_prompt(raw_preamble) == "A majestic owl perched on a crystal tree."

    # Krea 2 Prompt header
    raw_krea = "<|channel>thought\nReasoning about details...\nKrea 2 Prompt: A majestic owl perched on a crystal tree."
    assert extract_final_prompt(raw_krea) == "A majestic owl perched on a crystal tree."

    # Optimized Prompt header
    raw_opt = "<|channel>thought\nPlanning...\nOptimized Prompt: Futuristic car floating in cloud city"
    assert extract_final_prompt(raw_opt) == "Futuristic car floating in cloud city"

    # Prompt header
    raw_prompt = "<|channel>thought\nInternal monologue...\nPrompt: Vintage photograph of 1920s jazz band"
    assert extract_final_prompt(raw_prompt) == "Vintage photograph of 1920s jazz band"

    # Final Prompt header
    raw_final = "<|channel>thought\nThought process...\nFinal Prompt: A dragon over snowy mountains"
    assert extract_final_prompt(raw_final) == "A dragon over snowy mountains"
