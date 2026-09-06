import re
import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.services.ai.provider_manager import AIProviderManager
from app.services.ai.thinking_parser import extract_final_prompt
from app.services.unified_rag import unified_rag_service

logger = logging.getLogger(__name__)

DEFAULT_QUALITY_TAGS = "score_9, score_8, score_7"


def clean_sd_weights(prompt: str) -> str:
    """Cleans SD-style weight syntax like (tag:1.2) -> tag and ((tag)) -> tag."""
    if not prompt:
        return ""

    cleaned = prompt

    # 1. Remove weighted syntax: (tag:1.2) -> tag
    previous = None
    while previous != cleaned:
        previous = cleaned
        cleaned = re.sub(r"\(\s*([^():]+?)\s*:\s*-?\d+(?:\.\d+)?\s*\)", r"\1", cleaned)

    # 2. Remove plain outer parentheses: ((tag)) -> tag, (tag) -> tag
    previous = None
    while previous != cleaned:
        previous = cleaned
        cleaned = re.sub(r"\(\s*([^()]+?)\s*\)", r"\1", cleaned)

    # 3. Clean multiple spaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def format_artist_tags(prompt: str) -> str:
    """Formats artist:name style tags into ANIMA model preferred @name syntax."""
    if not prompt:
        return ""

    formatted = re.sub(r"\bartist:([a-zA-Z0-9_.-]+)", r"@\1", prompt)
    return formatted


def inject_quality_scores(prompt: str, quality_tags: str = DEFAULT_QUALITY_TAGS) -> str:
    """Safely injects ANIMA quality score tags (score_9, score_8, score_7) if not already present."""
    if not prompt:
        return quality_tags

    # Check if any score tag is already present to prevent duplicate injection
    if "score_7" in prompt or "score_8" in prompt or "score_9" in prompt:
        return prompt

    return f"{quality_tags}, {prompt.strip()}"


ANIMA_SYSTEM_BASE = """You are an expert AI prompt engineer specializing in ANIMA model prompt optimization.
Follow official ANIMA prompt formatting guidelines:
1. Quality Score Tags: Prepend ANIMA quality score tags (score_9, score_8, score_7) at the beginning of the prompt.
2. Artist Formatting: Format artist tags using the `@artist_name` syntax (e.g. `@shinkai_makoto`).
3. Weight Syntax: Do NOT use SD-style weight brackets like `(tag:1.2)` or `((tag))`. Use clean natural tags.
4. Logical Structure: Structure the prompt into Quality Scores -> Subject & Character Features -> Clothing & Poses -> Environment & Background -> Lighting, Atmosphere & Composition."""

ANIME_PRESET = ANIMA_SYSTEM_BASE + """

Variant Preset: Anime / Illustrative
- Optimized for vibrant anime, manga, and illustrative artwork.
- Focus on sharp anime aesthetics, expressive character eyes, detailed hair, clean lineart, and dynamic colors.
Output ONLY the final optimized prompt string."""

GENERAL_PRESET = ANIMA_SYSTEM_BASE + """

Variant Preset: General / Digital Art
- Optimized for general digital painting, rich textures, and painterly compositions.
Output ONLY the final optimized prompt string."""

EXPRESSIVE_PRESET = ANIMA_SYSTEM_BASE + """

Variant Preset: Expressive / Cinematic
- Optimized for dramatic cinematic lighting, intense character emotions, atmospheric motion, and dynamic camera angles.
Output ONLY the final optimized prompt string."""


class AnimaOptimizer:
    """ANIMA Model Profile Optimization Core Service."""

    def __init__(self):
        self._presets = {
            "anime": ANIME_PRESET,
            "general": GENERAL_PRESET,
            "expressive": EXPRESSIVE_PRESET,
        }

    def clean_sd_weights(self, prompt: str) -> str:
        return clean_sd_weights(prompt)

    def format_artist_tags(self, prompt: str) -> str:
        return format_artist_tags(prompt)

    def inject_quality_scores(self, prompt: str, quality_tags: str = DEFAULT_QUALITY_TAGS) -> str:
        return inject_quality_scores(prompt, quality_tags)

    def get_system_prompt(self, variant: str = "anime") -> str:
        key = variant.lower().strip() if variant else "anime"
        return self._presets.get(key, ANIME_PRESET)

    async def get_rag_guidelines(self, db: Session, prompt: str) -> str:
        """Retrieves and formats RAG guidelines for ANIMA prompt optimization without altering user prompt."""
        try:
            docs = await unified_rag_service.search_knowledge_async(
                db=db,
                query=prompt,
                top_k=2,
                category="anime_style",
            )
            if not docs:
                docs = await unified_rag_service.search_knowledge_async(
                    db=db,
                    query=prompt,
                    top_k=2,
                )
            if docs:
                guidelines = []
                for doc in docs:
                    guidelines.append(f"- {doc['title']}: {doc['content']}")
                if guidelines:
                    return "RAG Formatting & Style Guidelines:\n" + "\n".join(guidelines)
        except Exception as e:
            logger.warning(f"RAG enrichment failed in AnimaOptimizer: {e}")
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
        variant: str = "anime",
        clean_weights_flag: bool = True,
        format_artist_flag: bool = True,
        inject_scores_flag: bool = True,
        use_rag: bool = False,
        db: Optional[Session] = None,
        provider_manager: Optional[AIProviderManager] = None,
        max_tokens: Optional[int] = 4096,
    ) -> str:
        """Improve prompt adhering to ANIMA model guidelines."""
        processed_prompt = prompt

        if clean_weights_flag:
            processed_prompt = clean_sd_weights(processed_prompt)

        if format_artist_flag:
            processed_prompt = format_artist_tags(processed_prompt)

        if inject_scores_flag:
            processed_prompt = inject_quality_scores(processed_prompt)

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
                return res
            except Exception as e:
                logger.warning(f"AI Provider generation failed during ANIMA optimization: {e}")
                return processed_prompt

        return processed_prompt
