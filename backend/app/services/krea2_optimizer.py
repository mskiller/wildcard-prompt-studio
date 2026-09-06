import re
import logging
from typing import List, Optional
from sqlalchemy.orm import Session

from app.services.ai.provider_manager import AIProviderManager
from app.services.ai.thinking_parser import extract_final_prompt
from app.services.unified_rag import unified_rag_service

logger = logging.getLogger(__name__)

# Legacy SD quality buzzwords to strip
BUZZWORD_PATTERNS = [
    r"\b8k\b",
    r"\b8k resolution\b",
    r"\b4k\b",
    r"\b4k resolution\b",
    r"\bmasterpiece\b",
    r"\bhyper-detailed\b",
    r"\bhyper detailed\b",
    r"\btrending on artstation\b",
    r"\bultra detailed\b",
    r"\bultra-detailed\b",
    r"\bbest quality\b",
    r"\bhigh quality\b",
    r"\bhdr\b",
    r"\bultra high res\b",
    r"\bultra high resolution\b",
    r"\babsurdres\b",
    r"\bhighres\b",
]


def clean_buzzwords(prompt: str) -> str:
    """Automatically removes legacy SD quality tags and cleans up extra whitespace/commas."""
    if not prompt:
        return ""

    cleaned = prompt
    # Remove patterns case-insensitively
    for pat in BUZZWORD_PATTERNS:
        cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)

    # Handle comma-separated list cleanup
    parts = [part.strip() for part in cleaned.split(",") if part.strip()]
    cleaned = ", ".join(parts)

    # Clean multiple spaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def format_quotes(prompt: str, targets: Optional[List[str]]) -> str:
    """Auto-wraps requested text/phrases in exact double quotes ("text") if not already quoted."""
    if not prompt or not targets:
        return prompt

    formatted = prompt
    for target in targets:
        if not target or not isinstance(target, str):
            continue
        # Replace instances of target not preceded or followed by double quotes
        pattern = re.compile(r'(?<!")' + re.escape(target) + r'(?!")')
        formatted = pattern.sub(f'"{target}"', formatted)

    return formatted


KREA2_SYSTEM_BASE = """You are an expert AI prompt engineer specializing in Krea 2 prompt optimization.
Follow official Krea 2 guidelines:
1. Faithfulness First: Maintain the user's original concept, subject, and core intent strictly.
2. T2I Structure Grouping: Organize the prompt logically into [Subject & Action], [Environment & Context], [Lighting & Atmosphere], and [Style & Composition].
3. Style Planning: Provide explicit, harmonious style direction without conflicting terms.
4. Natural Language: Write in rich, coherent, descriptive natural language sentences rather than disconnected tags or buzzwords."""


TURBO_PRESET = KREA2_SYSTEM_BASE + """

Variant Preset: Turbo
- Optimized for fast ideation and concise, direct natural language.
- Target resolution: 2k resolution fast generation.
- Keep output concise, direct, and focused on essential visual elements without unnecessary filler.
Output ONLY the final optimized prompt string."""


MEDIUM_PRESET = KREA2_SYSTEM_BASE + """

Variant Preset: Medium
- Optimized for rich expressive artistic descriptions.
- Ideal for anime, digital illustrations, concept art, stylized artwork, and traditional paintings.
- Focus on vibrant color palettes, artistic medium, brushwork, line quality, rendering style, and expressive character poses.
Output ONLY the final optimized prompt string."""


LARGE_PRESET = KREA2_SYSTEM_BASE + """

Variant Preset: Large
- Optimized for raw photorealism and ultra-high fidelity.
- Focus on camera optics (lens focal length, aperture f-stop, camera angle), fine skin/material textures, realistic depth of field, optical lighting, subsurface scattering, and natural physical details.
Output ONLY the final optimized prompt string."""


class Krea2Optimizer:
    """Krea 2 Optimization & Expansion Engine."""

    def __init__(self):
        self._presets = {
            "turbo": TURBO_PRESET,
            "medium": MEDIUM_PRESET,
            "large": LARGE_PRESET,
        }

    def clean_buzzwords(self, prompt: str) -> str:
        return clean_buzzwords(prompt)

    def format_quotes(self, prompt: str, targets: Optional[List[str]]) -> str:
        return format_quotes(prompt, targets)

    def get_system_prompt(self, variant: str = "turbo") -> str:
        key = variant.lower().strip() if variant else "turbo"
        return self._presets.get(key, TURBO_PRESET)

    async def get_rag_guidelines(self, db: Session, prompt: str) -> str:
        """Retrieves and formats RAG guidelines for prompt optimization without altering user prompt."""
        try:
            results = await unified_rag_service.search_knowledge_async(
                db=db,
                query=prompt,
                top_k=2,
                category="model_guide"
            )
            if not results:
                results = await unified_rag_service.search_knowledge_async(
                    db=db,
                    query=prompt,
                    top_k=2
                )
            if results:
                guidelines = []
                for item in results:
                    title = item.get("title", "")
                    content = item.get("content", "")
                    guidelines.append(f"- {title}: {content}")
                if guidelines:
                    return "RAG Formatting & Style Guidelines:\n" + "\n".join(guidelines)
        except Exception as e:
            logger.warning(f"RAG enrichment failed in Krea2Optimizer: {e}")
        return ""

    async def enrich_prompt_with_rag(self, db: Session, prompt: str) -> str:
        """Enriches prompt with RAG guidance for backward compatibility."""
        guidelines = await self.get_rag_guidelines(db, prompt)
        if guidelines:
            return f"{prompt}\n\n{guidelines}"
        return prompt

    async def improve_prompt(
        self,
        prompt: str,
        variant: str = "turbo",
        quote_targets: Optional[List[str]] = None,
        clean_buzzwords_flag: bool = True,
        use_rag: bool = False,
        db: Optional[Session] = None,
        provider_manager: Optional[AIProviderManager] = None,
        max_tokens: Optional[int] = 4096,
    ) -> str:
        """Improve prompt adhering to Krea 2 guidelines and variant presets."""
        processed_prompt = prompt

        if clean_buzzwords_flag:
            processed_prompt = clean_buzzwords(processed_prompt)

        if quote_targets:
            processed_prompt = format_quotes(processed_prompt, quote_targets)

        system_prompt = self.get_system_prompt(variant)

        if use_rag and db:
            rag_guidelines = await self.get_rag_guidelines(db, processed_prompt)
            if rag_guidelines:
                system_prompt = f"{system_prompt}\n\n{rag_guidelines}"

        if provider_manager:
            try:
                improved = await provider_manager.generate(
                    prompt=processed_prompt,
                    system_prompt=system_prompt,
                    temperature=0.7,
                    max_tokens=max_tokens,
                )
                res = extract_final_prompt(improved)
                if quote_targets:
                    res = format_quotes(res, quote_targets)
                return res
            except Exception as e:
                logger.warning(f"AI Provider generation failed during Krea2 optimization: {e}")
                return processed_prompt

        return processed_prompt
