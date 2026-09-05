import json
import logging
import re
from typing import Any, Dict, List, Optional

from app.services.ai.provider_manager import AIProviderManager
from app.services.ai.thinking_parser import extract_final_prompt
from app.services.async_rag import async_rag_engine

logger = logging.getLogger(__name__)


MODEL_SPECIFICATIONS: Dict[str, str] = {
    "anima": (
        "Anima Target Model Specification:\n"
        "- Optimized for high-precision Anime, Illustrative & Digital Art styling.\n"
        "- Focus on character composition, line art quality, cel/digital shading, expressive poses, hair/eye details, and vibrant color palettes.\n"
        "- Structure tags cleanly: Subject & Character, Outfit, Pose & Action, Background, Lighting & Color.\n"
        "- Avoid photorealistic camera buzzwords (e.g., 85mm, f/1.8, RAW photo)."
    ),
    "krea": (
        "KREA 2 Target Model Specification:\n"
        "- Optimized for rich, descriptive natural language sentences rather than comma-separated tag soups.\n"
        "- Structure logically into: [Subject & Action], [Environment & Context], [Lighting & Atmosphere], [Style & Composition].\n"
        "- Clean legacy SD quality buzzwords (masterpiece, 8k resolution, best quality).\n"
        "- Wrap exact text/phrases to render in double quotes (\"text\")."
    ),
    "sdxl": (
        "SDXL 1.0 Target Model Specification:\n"
        "- High-resolution descriptive prompts combining rich aesthetic keywords with clean structural descriptors."
    ),
    "flux": (
        "Flux.1 Target Model Specification:\n"
        "- Pure natural language descriptive prose. Avoid quality tags and comma-heavy tag soups."
    ),
    "midjourney": (
        "Midjourney v6 Target Model Specification:\n"
        "- Cinematic and evocative natural language descriptions with explicit lighting, framing, and aspect composition."
    ),
    "pony": (
        "Pony XL Target Model Specification:\n"
        "- Use quality rating tags (score_9, score_8_up), clear character traits, pose, and aesthetic style tags."
    ),
}

PROMPT_ENGINEER_PROMPTS: Dict[str, str] = MODEL_SPECIFICATIONS


class PromptChatService:
    def _fallback_refine(self, current_prompt: str, user_message: str) -> Dict[str, Any]:
        """Deterministic fallback refinement when LLM is unavailable or fails to output valid JSON."""
        added: List[str] = []
        removed: List[str] = []

        parts = [p.strip() for p in re.split(r'[,;]\s*', user_message) if p.strip()]
        prompt_parts = [p.strip() for p in current_prompt.split(',') if p.strip()]

        for part in parts:
            p_lower = part.lower()
            if p_lower.startswith("remove ") or p_lower.startswith("delete "):
                target = re.sub(r'^(remove|delete)\s+', '', part, flags=re.IGNORECASE).strip()
                if target:
                    removed.append(target)
            elif p_lower.startswith("add ") or p_lower.startswith("incorporate "):
                target = re.sub(r'^(add|incorporate)\s+', '', part, flags=re.IGNORECASE).strip()
                if target:
                    added.append(target)
            elif "change " in p_lower or "set " in p_lower:
                added.append(part)

        cleaned_parts = []
        for p in prompt_parts:
            should_remove = False
            for rem in removed:
                if rem.lower() in p.lower():
                    should_remove = True
                    break
            if not should_remove:
                cleaned_parts.append(p)

        for add_item in added:
            if not any(add_item.lower() in p.lower() for p in cleaned_parts):
                cleaned_parts.append(add_item)

        updated_prompt = ", ".join(cleaned_parts) if cleaned_parts else current_prompt

        explanation_items = []
        if added:
            explanation_items.append(f"Added: {', '.join(added)}")
        if removed:
            explanation_items.append(f"Removed: {', '.join(removed)}")
        explanation = "; ".join(explanation_items) if explanation_items else f"Refined prompt based on input: '{user_message}'."

        return {
            "updated_prompt": updated_prompt,
            "explanation": explanation,
            "changes": {
                "added": added,
                "removed": removed
            }
        }

    @staticmethod
    def _normalize_string_list(val: Any) -> List[str]:
        if val is None:
            return []
        if isinstance(val, str):
            val = val.strip()
            return [val] if val else []
        if isinstance(val, list):
            result = []
            for item in val:
                if item is not None:
                    s = str(item).strip()
                    if s:
                        result.append(s)
            return result
        s = str(val).strip()
        return [s] if s else []

    async def refine_prompt_chat(
        self,
        current_prompt: str,
        user_message: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        provider: Optional[str] = "auto",
        target_model: Optional[str] = None,
        use_rag: bool = False,
        provider_manager: Optional[AIProviderManager] = None,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """Conversational Prompt Refinement.

        Takes current prompt, user edit message, conversation history, target model, and RAG options
        to return structured prompt updates, explanations, and change diffs.
        """
        rag_context = ""
        if use_rag:
            try:
                search_query = f"{current_prompt} {user_message}"
                rag_results = await async_rag_engine.search_knowledge_async(search_query, top_k=3)
                if rag_results:
                    desc_list = []
                    for item in rag_results:
                        if isinstance(item, dict):
                            title = item.get("title", "") or ""
                            content = item.get("content", "") or ""
                        elif item is not None:
                            title = getattr(item, "title", "") or ""
                            content = getattr(item, "content", "") or ""
                        else:
                            continue
                        desc_list.append(f"- {title}: {content}")
                    if desc_list:
                        rag_context = "RAG Style Descriptors & Guidance:\n" + "\n".join(desc_list)
            except Exception as e:
                logger.warning(f"RAG search failed in refine_prompt_chat: {e}")

        if not provider_manager or not provider_manager.list_providers():
            return self._fallback_refine(current_prompt, user_message)

        history_str = ""
        if chat_history:
            formatted_turns = []
            for turn in chat_history:
                role = turn.get("role", "user").capitalize()
                content = turn.get("content", "")
                formatted_turns.append(f"{role}: {content}")
            history_str = "Conversation History:\n" + "\n".join(formatted_turns)

        system_prompt = (
            "You are an expert AI prompt engineer specializing in iterative image generation prompt refinement.\n"
            "Your task is to update the current prompt according to the user's edit request, conversation history, and style guidance.\n\n"
            "CRITICAL INSTRUCTION: You MUST output ONLY valid JSON matching this exact schema, with no markdown outside code fence:\n"
            "{\n"
            '  "updated_prompt": "<modified prompt>",\n'
            '  "explanation": "<summary of changes made>",\n'
            '  "changes": {\n'
            '    "added": ["<added tag or style 1>", ...],\n'
            '    "removed": ["<removed tag 1>", ...]\n'
            "  }\n"
            "}"
        )

        model_spec = ""
        if target_model:
            tm_lower = target_model.lower()
            for key, spec in MODEL_SPECIFICATIONS.items():
                if key in tm_lower:
                    model_spec = spec
                    break

        user_content = f"Current Prompt: {current_prompt}\nUser Edit Request: {user_message}"
        if target_model:
            user_content += f"\nTarget Model: {target_model}"
        if model_spec:
            user_content += f"\n\n{model_spec}"
        if rag_context:
            user_content += f"\n\n{rag_context}"
        if history_str:
            user_content += f"\n\n{history_str}"

        try:
            raw_response = await provider_manager.generate(
                prompt=user_content,
                system_prompt=system_prompt,
                max_tokens=max_tokens
            )

            cleaned_response = extract_final_prompt(raw_response)

            first_brace = cleaned_response.find("{")
            last_brace = cleaned_response.rfind("}")
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                json_str = cleaned_response[first_brace:last_brace + 1]
            else:
                json_str = cleaned_response

            parsed = json.loads(json_str)
            if isinstance(parsed, dict) and "updated_prompt" in parsed:
                changes_raw = parsed.get("changes")
                if not isinstance(changes_raw, dict):
                    changes_raw = {}

                added = self._normalize_string_list(changes_raw.get("added"))
                removed = self._normalize_string_list(changes_raw.get("removed"))

                return {
                    "updated_prompt": str(parsed.get("updated_prompt", current_prompt)),
                    "explanation": str(parsed.get("explanation", "Updated prompt.")),
                    "changes": {
                        "added": added,
                        "removed": removed
                    }
                }
        except Exception as e:
            logger.warning(f"LLM generation/parsing failed in refine_prompt_chat: {e}. Using fallback.")

        return self._fallback_refine(current_prompt, user_message)


prompt_chat_service = PromptChatService()
