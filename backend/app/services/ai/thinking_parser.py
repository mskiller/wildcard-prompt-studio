import re
from typing import Optional


def extract_final_prompt(raw_text: Optional[str]) -> str:
    """Extract final prompt text from thinking model raw output.

    Handles Gemma 4 channel tags (<|channel>thought / <|channel>text),
    XML style thinking tags (<think>...</think>), regex header fallbacks,
    and residual tag cleaning.

    Args:
        raw_text: Raw completion text from AI provider.

    Returns:
        Extracted final prompt string (trimmed).
    """
    if raw_text is None or not raw_text.strip():
        return ""

    text = raw_text.strip()

    # 1. Gemma 4 <|channel>text block handling
    if "<|channel>text" in text:
        result = text.rsplit("<|channel>text", 1)[-1]
    # 2. XML style </think> block handling
    elif "</think>" in text:
        result = text.rsplit("</think>", 1)[-1]
    # 3. Gemma 4 thought channel without text channel (fallback header search)
    elif "<|channel>thought" in text:
        match = re.search(
            r"(?:Krea 2 Prompt|Optimized Prompt|Prompt|Final Prompt):\s*(.*)",
            text,
            re.DOTALL | re.IGNORECASE,
        )
        if match:
            result = match.group(1)
        else:
            result = text
    # 4. Unthinking mode (raw text without thinking tags)
    else:
        result = text

    # Strip any residual <|channel> or <|channel|> tags
    result = re.sub(r"<\|channel[>|]*>?", "", result)

    return result.strip()
