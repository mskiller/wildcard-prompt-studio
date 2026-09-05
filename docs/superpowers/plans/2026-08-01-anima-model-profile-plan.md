# ANIMA Model Profile & Studio Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate ANIMA model profile (Qwen-based hybrid Danbooru + natural language text-to-image optimizer) into backend services and build a dedicated Anima Studio Panel in the frontend.

**Architecture:** A standalone `AnimaOptimizer` service in Python backend handles SD weight stripping `(tag:1.2)` $\rightarrow$ `tag`, quality score injection (`score_7, safe`), and 3 style presets (`hybrid`, `tag_focused`, `natural_language`). The FastAPI router exposes `/api/ai/anima-improve`. The React frontend adds a dedicated `AnimaStudioPanel` tab, state routing, and prompt chat drawer options.

**Tech Stack:** FastAPI, Pydantic, Python 3.10+, Pytest, React, TypeScript, Vite.

---

### Task 1: Backend `AnimaOptimizer` Core Service

**Files:**
- Create: `backend/app/services/anima_optimizer.py`
- Test: `backend/tests/test_anima_optimizer.py`

- [ ] **Step 1: Write failing unit tests for `AnimaOptimizer`**

Create `backend/tests/test_anima_optimizer.py`:
```python
import pytest
from app.services.anima_optimizer import AnimaOptimizer, clean_sd_weights, format_artist_tags, inject_quality_scores

def test_clean_sd_weights():
    raw = "(masterpiece:1.2), ((1girl)), (blue hair:0.8), pose"
    cleaned = clean_sd_weights(raw)
    assert "(masterpiece:1.2)" not in cleaned
    assert "((1girl))" not in cleaned
    assert "1girl" in cleaned
    assert "blue hair" in cleaned

def test_format_artist_tags():
    raw = "artist:by_artist_name, 1girl"
    formatted = format_artist_tags(raw)
    assert "@by_artist_name" in formatted or "by_artist_name" in formatted

def test_inject_quality_scores():
    raw = "1girl, solo, smiling"
    res = inject_quality_scores(raw, add_quality=True)
    assert "score_7" in res
    assert "safe" in res

def test_anima_optimizer_get_system_prompt():
    optimizer = AnimaOptimizer()
    hybrid_sys = optimizer.get_system_prompt("hybrid")
    assert "Qwen" in hybrid_sys or "Danbooru" in hybrid_sys or "natural language" in hybrid_sys
```

- [ ] **Step 2: Run pytest to verify tests fail**

Run: `pytest backend/tests/test_anima_optimizer.py`
Expected: FAIL with ModuleNotFoundError or import error for `anima_optimizer`.

- [ ] **Step 3: Implement `AnimaOptimizer` service**

Create `backend/app/services/anima_optimizer.py`:
```python
import re
import logging
from typing import List, Optional
from app.services.ai.provider_manager import AIProviderManager
from app.services.ai.thinking_parser import extract_final_prompt

logger = logging.getLogger(__name__)

def clean_sd_weights(prompt: str) -> str:
    """Strips SD weight syntax such as (tag:1.2) or ((tag)) -> tag."""
    if not prompt:
        return ""
    # Remove (tag:weight) -> tag
    cleaned = re.sub(r"\(([^:]+):[0-9.]+\)", r"\1", prompt)
    # Remove extra parentheses ((tag)) -> tag
    cleaned = re.sub(r"[\(\)]+", "", cleaned)
    # Clean whitespace and trailing commas
    parts = [p.strip() for p in cleaned.split(",") if p.strip()]
    return ", ".join(parts)

def format_artist_tags(prompt: str) -> str:
    """Formats artist names into @artist_name syntax if prefixed with artist: or by_."""
    if not prompt:
        return ""
    def _repl(match):
        name = match.group(1).strip()
        if not name.startswith("@"):
            return f"@{name}"
        return name
    return re.sub(r"\bartist:([a-zA-Z0-9_]+)\b", _repl, prompt)

def inject_quality_scores(prompt: str, add_quality: bool = True) -> str:
    """Injects Anima standard quality scores (score_7, safe, masterpiece, best quality)."""
    if not add_quality or not prompt:
        return prompt
    prefix = "masterpiece, best quality, score_7, safe"
    if prefix in prompt or "score_7" in prompt:
        return prompt
    return f"{prefix}, {prompt}"

ANIMA_SYSTEM_BASE = """You are an expert AI prompt engineer specializing in ANIMA text-to-image prompt optimization.
ANIMA relies on a Qwen language encoder that understands both Danbooru tags and rich natural language descriptions.
Follow official ANIMA guidelines:
1. Hybrid Prompting: Use Danbooru tags for core quality, rating, and character identifiers, combined with descriptive natural language sentences for pose, scene composition, lighting, and atmosphere.
2. Weighting: Do NOT output Stable Diffusion weight syntax like (tag:1.3) or ((tag)). Write plain tags or sentences.
3. Artist Formatting: Format artist tags using the @artist_name syntax.
4. Output ONLY the optimized prompt string."""

HYBRID_PRESET = ANIMA_SYSTEM_BASE + """

Variant Preset: Hybrid (Tags + Natural Language)
- Balance Danbooru tags for character attributes with rich descriptive English sentences for action, scenery, and lighting.
- Output ONLY the final optimized prompt string."""

TAG_PRESET = ANIMA_SYSTEM_BASE + """

Variant Preset: Tag Heavy
- Focus heavily on dense, structured Danbooru tags for character, hair, eyes, outfit, and background elements.
- Output ONLY the final optimized prompt string."""

NATURAL_PRESET = ANIMA_SYSTEM_BASE + """

Variant Preset: Natural Language
- Focus on fluid, descriptive English paragraphs for storytelling, detailed scene composition, and artistic atmosphere.
- Output ONLY the final optimized prompt string."""

class AnimaOptimizer:
    """ANIMA Optimization & Expansion Engine."""

    def __init__(self):
        self._presets = {
            "hybrid": HYBRID_PRESET,
            "tag_focused": TAG_PRESET,
            "natural_language": NATURAL_PRESET,
        }

    def get_system_prompt(self, variant: str = "hybrid") -> str:
        key = variant.lower().strip() if variant else "hybrid"
        return self._presets.get(key, HYBRID_PRESET)

    async def improve_prompt(
        self,
        prompt: str,
        variant: str = "hybrid",
        add_quality_tags: bool = True,
        clean_weights: bool = True,
        negative_prompt: Optional[str] = None,
        provider_manager: Optional[AIProviderManager] = None,
        max_tokens: Optional[int] = 4096,
    ) -> str:
        processed = prompt
        if clean_weights:
            processed = clean_sd_weights(processed)
        processed = format_artist_tags(processed)
        if add_quality_tags:
            processed = inject_quality_scores(processed, True)

        system_prompt = self.get_system_prompt(variant)

        if provider_manager:
            try:
                improved = await provider_manager.generate(
                    prompt=processed,
                    system_prompt=system_prompt,
                    temperature=0.7,
                    max_tokens=max_tokens,
                )
                res = extract_final_prompt(improved)
                if clean_weights:
                    res = clean_sd_weights(res)
                return res
            except Exception as e:
                logger.warning(f"AI Provider generation failed during Anima optimization: {e}")
                return processed

        return processed
```

- [ ] **Step 4: Run pytest to verify tests pass**

Run: `pytest backend/tests/test_anima_optimizer.py`
Expected: PASS

---

### Task 2: Backend Router, Schemas & Dependency Integration

**Files:**
- Modify: `backend/app/schemas/ai.py`
- Modify: `backend/app/dependencies.py`
- Modify: `backend/app/api/routers/ai.py`
- Modify: `backend/app/services/prompt_chat_service.py`
- Modify: `backend/scripts/seed.py`
- Modify: `backend/tests/test_api_endpoints.py`

- [ ] **Step 1: Update Schemas `backend/app/schemas/ai.py`**

Add `AnimaImproveRequest` class:
```python
class AnimaImproveRequest(BaseModel):
    prompt: str
    variant: Optional[str] = "hybrid"
    add_quality_tags: Optional[bool] = True
    clean_weights: Optional[bool] = True
    negative_prompt: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
```

- [ ] **Step 2: Add `get_anima_optimizer` in `backend/app/dependencies.py`**

Add singleton factory:
```python
from app.services.anima_optimizer import AnimaOptimizer

anima_optimizer_instance = None

def get_anima_optimizer() -> AnimaOptimizer:
    global anima_optimizer_instance
    if anima_optimizer_instance is None:
        anima_optimizer_instance = AnimaOptimizer()
    return anima_optimizer_instance
```

- [ ] **Step 3: Add `/anima-improve` Endpoint in `backend/app/api/routers/ai.py`**

Import `get_anima_optimizer`, `AnimaImproveRequest`, `AnimaOptimizer` and add endpoint:
```python
@router.post("/anima-improve", response_model=PromptImproveResponse)
async def anima_improve_prompt_endpoint(
    request: AnimaImproveRequest,
    optimizer: AnimaOptimizer = Depends(get_anima_optimizer),
    provider_mgr: AIProviderManager = Depends(get_provider_manager),
):
    improved_prompt = await optimizer.improve_prompt(
        prompt=request.prompt,
        variant=request.variant or "hybrid",
        add_quality_tags=request.add_quality_tags if request.add_quality_tags is not None else True,
        clean_weights=request.clean_weights if request.clean_weights is not None else True,
        negative_prompt=request.negative_prompt,
        provider_manager=provider_mgr,
    )
    return PromptImproveResponse(
        improved_prompt=improved_prompt,
        provider="anima_optimizer",
        model=request.variant or "hybrid",
    )
```

- [ ] **Step 4: Add `anima` profile to `prompt_chat_service.py` & `seed.py`**

In `backend/app/services/prompt_chat_service.py`:
Add `"anima"` profile mapping in `PROMPT_ENGINEER_PROMPTS`.

In `backend/scripts/seed.py`:
Add `"anima"` profile dict in model profiles list.

- [ ] **Step 5: Write API test and verify**

Add test in `backend/tests/test_api_endpoints.py`:
```python
def test_anima_improve_endpoint_basic():
    with TestClient(app) as client:
        res = client.post("/api/ai/anima-improve", json={"prompt": "(1girl:1.2), cat ears"})
        assert res.status_code == 200
        data = res.json()
        assert "improved_prompt" in data
```
Run `pytest backend/tests/test_api_endpoints.py`

---

### Task 3: Frontend API & Store Updates

**Files:**
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/store/useAppStore.ts`

- [ ] **Step 1: Add `AnimaOptions` & `animaImprovePrompt` in `frontend/src/api.ts`**

```typescript
export interface AnimaOptions {
  prompt: string;
  variant?: 'hybrid' | 'tag_focused' | 'natural_language';
  add_quality_tags?: boolean;
  clean_weights?: boolean;
  negative_prompt?: string;
}

export async function animaImprovePrompt(options: AnimaOptions): Promise<string> {
  const res = await fetch(`${API_BASE}/ai/anima-improve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(options),
  });
  if (!res.ok) {
    throw new Error(`Failed to improve Anima prompt: ${res.statusText}`);
  }
  const data = await res.json();
  return data.improved_prompt;
}
```

- [ ] **Step 2: Update `ActiveView` in `frontend/src/store/useAppStore.ts`**

Update `ActiveView` type union to include `'anima'`:
```typescript
export type ActiveView =
  | 'editor'
  | 'wildcards'
  | 'matrix'
  | 'history'
  | 'batch'
  | 'chat'
  | 'krea2'
  | 'anima'
  | 'comfyui'
  | 'settings';
```

---

### Task 4: Frontend `AnimaStudioPanel` Component

**Files:**
- Create: `frontend/src/components/editor/AnimaStudioPanel.tsx`
- Create: `frontend/src/components/editor/AnimaStudioPanel.css`

- [ ] **Step 1: Create `AnimaStudioPanel.css`**

Define sleek dark styling, controls grid, badge headers, and quick-action buttons consistent with Krea 2 panel styling.

- [ ] **Step 2: Create `AnimaStudioPanel.tsx`**

Implement interactive React component:
- State for prompt, variant (`hybrid`, `tag_focused`, `natural_language`), `addQualityTags`, `cleanWeights`, `negativePrompt`, and `outputPrompt`.
- Clean SD weights helper button.
- Improve prompt trigger calling `animaImprovePrompt`.
- Copy & Send to Prompt Editor / ComfyUI buttons.

---

### Task 5: App Router & Navigation Integration

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/layout/Sidebar.tsx`
- Modify: `frontend/src/components/editor/PromptEditor.tsx`
- Modify: `frontend/src/components/layout/ContextPanel.tsx`
- Modify: `frontend/src/components/editor/PromptChatDrawer.tsx`

- [ ] **Step 1: Render `AnimaStudioPanel` in `frontend/src/App.tsx`**

Import `AnimaStudioPanel` and render when `activeView === 'anima'`.

- [ ] **Step 2: Add Anima icon tab in `Sidebar.tsx`**

Add navigation item for `anima` with an icon (Sparkles or Wand) and title "Anima Studio".

- [ ] **Step 3: Update model dropdown in `PromptEditor.tsx`, `ContextPanel.tsx`, and `PromptChatDrawer.tsx`**

Add `{ id: 'anima', name: 'ANIMA AI' }` option.

---

### Task 6: Documentation & Verification

**Files:**
- Create: `docs/ANIMA_PROMPTING_GUIDE.md`

- [ ] **Step 1: Write `docs/ANIMA_PROMPTING_GUIDE.md`**

Document Anima Qwen text encoder guidelines, hybrid prompt structure, weight stripping, `@artist` tags, quality scores, and Studio panel features.

- [ ] **Step 2: Run Full Suite Verification**

Run backend tests: `pytest`
Run frontend check: `npm run build` or `npx tsc --noEmit` inside `frontend/`.
