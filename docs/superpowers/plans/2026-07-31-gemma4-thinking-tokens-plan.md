# Gemma 4 Thinking Mode Token Boost & Prompt Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow thinking models (Gemma 4, DeepSeek R1, Qwen Thought) to output complete reasoning traces and final prompts by introducing a configurable Max Output Tokens setting (defaulting to 4096) and robustly extracting the clean result prompt while preserving Unthinking mode.

**Architecture:** Frontend Zustand settings store (`useAppStore.ts`) holds `enableThinkingTokenBoost` and `maxOutputTokens`. These parameters pass through API calls (`api.ts`) to backend endpoints (`/ai/krea2-improve`, `/ai/improve`, `/ai/vision/describe`). Backend AI providers (`KoboldCppProvider`, `OllamaProvider`, `GeminiProvider`) output up to `max_tokens`. An `extract_final_prompt()` parser strips `<|channel>thought ... <|channel>text` metadata before returning the final prompt.

**Tech Stack:** React 18, TypeScript, Zustand (`persist`), Python 3.11+, FastAPI, Pydantic, pytest, httpx.

---

### Task 1: Backend Thinking Response Parser (`extract_final_prompt`)

**Files:**
- Create: `backend/app/services/ai/thinking_parser.py`
- Test: `backend/tests/test_thinking_parser.py`

- [ ] **Step 1: Write failing unit tests for `extract_final_prompt`**

```python
# backend/tests/test_thinking_parser.py
from app.services.ai.thinking_parser import extract_final_prompt

def test_extract_final_prompt_gemma4_channel():
    raw = (
        "<|channel>thought\n"
        "Here is a thinking process:\n"
        "1. Analyze image...\n"
        "<|channel>text\n"
        "A handsome steampunk inventor inspecting a brass chronometer device in a foggy laboratory."
    )
    extracted = extract_final_prompt(raw)
    assert extracted == "A handsome steampunk inventor inspecting a brass chronometer device in a foggy laboratory."

def test_extract_final_prompt_xml_think():
    raw = "<think>\nStep 1: Details...\n</think>\nA futuristic cybernetic cityscape with neon reflections."
    extracted = extract_final_prompt(raw)
    assert extracted == "A futuristic cybernetic cityscape with neon reflections."

def test_extract_final_prompt_unthinking_mode():
    raw = "A simple portrait of a cat sitting on a windowsill in soft daylight."
    extracted = extract_final_prompt(raw)
    assert extracted == "A simple portrait of a cat sitting on a windowsill in soft daylight."

def test_extract_final_prompt_empty():
    assert extract_final_prompt("") == ""
    assert extract_final_prompt(None) == ""
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest backend/tests/test_thinking_parser.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.ai.thinking_parser'`

- [ ] **Step 3: Implement `extract_final_prompt`**

```python
# backend/app/services/ai/thinking_parser.py
import re
from typing import Optional

def extract_final_prompt(raw_text: Optional[str]) -> str:
    """
    Extracts the clean final prompt from model responses, handling thinking channels
    (e.g., Gemma 4 <|channel>thought ... <|channel>text, DeepSeek <think>...</think>),
    while leaving unthinking mode responses untouched.
    """
    if not raw_text:
        return ""

    text = raw_text.strip()

    # 1. Gemma 4 / multi-channel format: <|channel>thought...\n<|channel>text\n...
    if "<|channel>text" in text:
        parts = text.split("<|channel>text")
        text = parts[-1].strip()

    # 2. XML think tag format: <think>...</think>...
    elif "</think>" in text:
        parts = text.split("</think>")
        text = parts[-1].strip()

    # 3. Fallback: If output starts with thought tag but lacks closing text tag, attempt regex header extraction
    elif text.startswith("<|channel>thought"):
        match = re.search(r'(?:Krea 2 Prompt|Optimized Prompt|Prompt|Final Prompt):\s*(.*)', text, re.IGNORECASE | re.DOTALL)
        if match:
            text = match.group(1).strip()

    # Strip any residual channel tags
    text = re.sub(r'<\|channel\|?>', '', text).strip()
    return text
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_thinking_parser.py -v`
Expected: PASS

---

### Task 2: AI Provider `max_tokens` Support

**Files:**
- Modify: `backend/app/services/ai/provider.py`
- Modify: `backend/app/services/ai/kobold_provider.py`
- Modify: `backend/app/services/ai/ollama_provider.py`
- Modify: `backend/app/services/ai/gemini_provider.py`
- Modify: `backend/app/services/ai/provider_manager.py`
- Test: `backend/tests/test_ai_providers.py`

- [ ] **Step 1: Write failing test in `test_ai_providers.py` for max_tokens payload**

```python
# Add to backend/tests/test_ai_providers.py
@pytest.mark.asyncio
async def test_kobold_provider_max_tokens():
    provider = KoboldCppProvider(base_url="http://localhost:5001")
    with respx.mock:
        respx.post("http://localhost:5001/v1/chat/completions").mock(
            return_value=httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})
        )
        res = await provider.generate(prompt="Test", max_tokens=4096)
        assert res == "ok"
        request = respx.calls.last.request
        payload = json.loads(request.content)
        assert payload["max_tokens"] == 4096
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest backend/tests/test_ai_providers.py::test_kobold_provider_max_tokens -v`
Expected: FAIL due to unexpected keyword argument `max_tokens`

- [ ] **Step 3: Update AIProvider interface and implementations**

In `backend/app/services/ai/provider.py`:
```python
class AIProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        pass
```

In `backend/app/services/ai/kobold_provider.py`:
```python
    async def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens if max_tokens is not None else 4096,
        }
```

In `backend/app/services/ai/ollama_provider.py`:
```python
    async def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        options = {"temperature": temperature}
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        payload = {
            "model": self.model,
            "messages": messages,
            "options": options,
            "stream": False
        }
```

In `backend/app/services/ai/gemini_provider.py`:
```python
    async def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        gen_config = {"temperature": temperature}
        if max_tokens is not None:
            gen_config["maxOutputTokens"] = max_tokens

        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": gen_config
        }
```

In `backend/app/services/ai/provider_manager.py`:
```python
    async def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        # ...
        return await provider.generate(prompt=prompt, system_prompt=system_prompt, temperature=temperature, max_tokens=max_tokens)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_ai_providers.py -v`
Expected: PASS

---

### Task 3: Backend API Endpoints & Service Integration

**Files:**
- Modify: `backend/app/schemas/ai.py`
- Modify: `backend/app/api/routers/ai.py`
- Modify: `backend/app/services/krea2_optimizer.py`
- Modify: `backend/app/services/ai/vision_service.py`
- Modify: `backend/app/services/prompt_assistant.py`
- Test: `backend/tests/test_krea2_optimizer.py`, `backend/tests/test_vision_service.py`

- [ ] **Step 1: Update schemas (`backend/app/schemas/ai.py`)**

```python
class PromptImproveRequest(BaseModel):
    prompt: str
    target_model: Optional[str] = "SDXL"
    kobold_url: Optional[str] = "http://host.docker.internal:5001"
    use_rag: Optional[bool] = False
    max_tokens: Optional[int] = 4096

class Krea2ImproveRequest(BaseModel):
    prompt: str
    variant: Optional[str] = "turbo"
    quote_targets: Optional[List[str]] = None
    clean_buzzwords: Optional[bool] = True
    provider: Optional[str] = "kobold"
    max_tokens: Optional[int] = 4096
```

- [ ] **Step 2: Update `Krea2Optimizer.improve_prompt()` and `VisionService`**

In `backend/app/services/krea2_optimizer.py`:
Import `extract_final_prompt` from `app.services.ai.thinking_parser`.
Update `improve_prompt` to accept `max_tokens: Optional[int] = 4096`:
```python
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
```

In `backend/app/services/ai/vision_service.py`:
Update `_call_koboldcpp_vision` to accept `max_tokens: int = 4096`:
```python
        payload = {
            "model": "koboldcpp-vision",
            "messages": [...],
            "max_tokens": max_tokens or 4096
        }
```
And wrap output returned from `describe_image` with `extract_final_prompt`:
```python
        return {
            "prompt": extract_final_prompt(prompt_text),
            "variant": variant,
            "provider_used": selected_provider
        }
```

In `backend/app/api/routers/ai.py`:
Update endpoints `/improve`, `/krea2-improve`, and `/vision/describe` to pass `max_tokens`.

- [ ] **Step 3: Run existing test suites to verify backend functionality**

Run: `pytest backend/tests/test_krea2_optimizer.py backend/tests/test_ai_endpoints.py -v`
Expected: PASS

---

### Task 4: Frontend Store, i18n & Settings UI

**Files:**
- Modify: `frontend/src/store/useAppStore.ts`
- Modify: `frontend/src/i18n.ts`
- Modify: `frontend/src/components/settings/SettingsView.tsx`

- [ ] **Step 1: Update `useAppStore.ts`**

Add state fields to `AppState`:
```typescript
  enableThinkingTokenBoost: boolean;
  setEnableThinkingTokenBoost: (enable: boolean) => void;
  maxOutputTokens: number;
  setMaxOutputTokens: (tokens: number) => void;
```
Default values:
```typescript
  enableThinkingTokenBoost: true,
  setEnableThinkingTokenBoost: (enableThinkingTokenBoost) => set({ enableThinkingTokenBoost }),
  maxOutputTokens: 4096,
  setMaxOutputTokens: (maxOutputTokens) => set({ maxOutputTokens }),
```

- [ ] **Step 2: Update `i18n.ts`**

In `en`:
```typescript
    enableThinkingTokenBoost: "Enable Thinking Model Token Boost",
    thinkingTokenHelp: "Allows local models (Gemma 4, DeepSeek R1) in thinking mode to output complete thought logs and final prompts without cutoff.",
    maxOutputTokens: "Max Output Tokens",
```

In `fr`:
```typescript
    enableThinkingTokenBoost: "Activer le Boost de Tokens pour Modèles de Pensée",
    thinkingTokenHelp: "Permet aux modèles locaux (Gemma 4, DeepSeek R1) en mode pensée de générer le journal de pensée complet et le prompt final sans coupure.",
    maxOutputTokens: "Tokens de sortie max",
```

- [ ] **Step 3: Add UI controls in `SettingsView.tsx`**

In the `prompt` tab of `SettingsView.tsx`:
```tsx
  <div className="settings-form-group" style={{ marginTop: 20 }}>
    <label className="checkbox-label">
      <input
        type="checkbox"
        checked={enableThinkingTokenBoost}
        onChange={(e) => setEnableThinkingTokenBoost(e.target.checked)}
      />
      <span>{t('enableThinkingTokenBoost')}</span>
    </label>
    <p className="form-help">{t('thinkingTokenHelp')}</p>
  </div>

  {enableThinkingTokenBoost && (
    <div className="settings-form-group">
      <label>{t('maxOutputTokens')}</label>
      <select
        value={maxOutputTokens}
        onChange={(e) => setMaxOutputTokens(Number(e.target.value))}
        className="glass-input"
        style={{ width: '200px' }}
      >
        <option value={1024}>1024 Tokens</option>
        <option value={2048}>2048 Tokens</option>
        <option value={4096}>4096 Tokens (Recommended for Gemma 4)</option>
        <option value={8192}>8192 Tokens</option>
      </select>
    </div>
  )}
```

---

### Task 5: Frontend API Integration & Panel Wiring

**Files:**
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/components/editor/Krea2StudioPanel.tsx`
- Modify: `frontend/src/components/editor/VisionInspectorPanel.tsx`

- [ ] **Step 1: Update `Krea2Options` & API functions in `api.ts`**

```typescript
export interface Krea2Options {
  prompt: string;
  variant?: 'turbo' | 'medium' | 'large' | string;
  quote_targets?: string[];
  clean_buzzwords?: boolean;
  provider?: 'kobold' | 'ollama' | 'gemini' | string;
  max_tokens?: number;
}
```
Update `krea2ImprovePrompt` and `improvePrompt` to send `max_tokens` in JSON body.

- [ ] **Step 2: Update `Krea2StudioPanel.tsx` & `VisionInspectorPanel.tsx`**

Pull `enableThinkingTokenBoost` and `maxOutputTokens` from `useAppStore`.
In `Krea2StudioPanel.tsx`:
```typescript
  const { maxOutputTokens, enableThinkingTokenBoost } = useAppStore();
  // ...
  const options: Krea2Options = {
    prompt: originalPrompt,
    variant,
    provider,
    clean_buzzwords: cleanBuzzwords,
    quote_targets: quoteTargets.length > 0 ? quoteTargets : undefined,
    max_tokens: enableThinkingTokenBoost ? maxOutputTokens : 512,
  };
```

In `VisionInspectorPanel.tsx`:
Add `formData.append('max_tokens', String(enableThinkingTokenBoost ? maxOutputTokens : 512));` to `handleDescribe`.

- [ ] **Step 3: Run frontend build check**

Run: `npx vite build`
Expected: Successful production build without TypeScript errors.

---

## Plan Self-Review
1. **Spec coverage**:
   - High token limit toggle + selector in settings? Yes (Task 4).
   - Backend `max_tokens` support in Kobold/Ollama/Gemini? Yes (Task 2).
   - Response parsing for `<|channel>thought ... <|channel>text` and `<think>`? Yes (Task 1 & 3).
   - Unthinking mode preserved? Yes (Task 1 test `test_extract_final_prompt_unthinking_mode`).
   - Vision & Krea 2 prompt improvement integration? Yes (Task 3 & 5).
2. **Placeholder scan**: None.
3. **Type consistency**: `max_tokens` signature verified across backend and frontend.
