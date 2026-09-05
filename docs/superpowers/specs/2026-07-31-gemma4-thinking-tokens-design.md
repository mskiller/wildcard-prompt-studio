# Gemma 4 Thinking Mode Token Boost & Prompt Extraction Design

**Date:** 2026-07-31  
**Status:** Approved  
**Topic:** Configurable Max Output Token Setting for Thinking Models & Response Extraction in KoboldCpp, Ollama, Gemini, Krea 2, and Vision Services.

---

## 1. Problem Statement
When using Gemma 4 (or other reasoning/thinking models such as DeepSeek R1 or Qwen Thought) via local KoboldCpp, Ollama, or cloud endpoints to improve prompts or reverse-engineer prompts from images using Vision:
- Low hardcoded max output token limits (e.g. 512 tokens in `kobold_provider.py` and 300 in `vision_service.py`) cause generation to stop midway through the model's `<|channel>thought ...` trace before the actual prompt is produced.
- The raw output contains internal reasoning channels (`<|channel>thought ...`, `<think> ... </think>`) without extracting the final generated prompt string.
- In **unthinking mode**, models output the prompt directly without thought channels, which must remain unaffected.

---

## 2. Requirements
1. **Configurable Output Token Limit**:
   - Add a switch/toggle in **Settings > AI & Prompt Improvement** to enable/disable High Token Limit for Thinking Models.
   - Allow custom selection of `maxOutputTokens` (default: 4096 tokens when enabled, 512 tokens when disabled; options: 1024, 2048, 4096, 8192, or custom input).
2. **Backend AI Provider Support**:
   - Update `AIProvider.generate()` signature and concrete implementations (`KoboldCppProvider`, `OllamaProvider`, `GeminiProvider`, `AIProviderManager`) to support passing `max_tokens`.
3. **Response Parsing & Prompt Extraction**:
   - Create `extract_final_prompt(raw_text: str) -> str` in backend services.
   - Extract content after `<|channel>text` (Gemma 4 format), after `</think>` (DeepSeek/Qwen format), or after explicit prompt headers (`Krea 2 Prompt:`, `Optimized Prompt:`, `Prompt:`).
   - If no thinking tags/headers are present (**Unthinking Mode**), return the raw trimmed text as-is.
4. **End-to-End Propagation**:
   - Pass `max_tokens` from frontend settings state store (`useAppStore.ts`) through API calls (`api.ts`, `Krea2StudioPanel.tsx`, `VisionInspectorPanel.tsx`) to backend API endpoints (`/api/v1/ai/krea2-improve`, `/api/v1/ai/improve`, `/api/v1/ai/vision/describe`, `/api/v1/ai/vision/extract-style`).

---

## 3. Component Design & Changes

### 3.1 Store & i18n (`frontend/src/store/useAppStore.ts`, `frontend/src/i18n.ts`)
- Add state properties to `AppState`:
  - `enableThinkingTokenBoost: boolean` (default: `true`)
  - `maxOutputTokens: number` (default: `4096`)
  - `setEnableThinkingTokenBoost: (enable: boolean) => void`
  - `setMaxOutputTokens: (tokens: number) => void`
- Add i18n dictionary entries for English (`en`) and French (`fr`):
  - `enableThinkingTokenBoost`: "Enable High Token Limit for Thinking Models (Gemma 4 / DeepSeek R1)"
  - `maxOutputTokens`: "Max Output Tokens"
  - `thinkingTokenHelp`: "Increases max token allowance so thinking models can generate complete thought logs and final prompts without cutoff."

### 3.2 Settings View (`frontend/src/components/settings/SettingsView.tsx`)
- In **AI & Prompt Improvement** section:
  - Add checkbox/toggle for `enableThinkingTokenBoost`.
  - Add select/input for `maxOutputTokens` (Options: 1024, 2048, 4096, 8192).

### 3.3 Frontend API Layer & Panels (`api.ts`, `Krea2StudioPanel.tsx`, `VisionInspectorPanel.tsx`)
- Update `Krea2Options` interface to include `max_tokens?: number`.
- Update `krea2ImprovePrompt`, `improvePrompt` in `api.ts` to forward `max_tokens`.
- In `Krea2StudioPanel.tsx` & `VisionInspectorPanel.tsx`, pull `maxOutputTokens` and `enableThinkingTokenBoost` from `useAppStore` and pass `max_tokens` in request payloads.

### 3.4 Backend Schemas & Endpoints (`backend/app/schemas/ai.py`, `backend/app/api/routers/ai.py`)
- Add `max_tokens: Optional[int] = 4096` to `PromptImproveRequest` and `Krea2ImproveRequest`.
- Add `max_tokens` optional form field to `/vision/describe` and `/vision/extract-style` endpoints in `ai.py`.

### 3.5 Backend Providers (`provider.py`, `kobold_provider.py`, `ollama_provider.py`, `gemini_provider.py`, `provider_manager.py`)
- Update `AIProvider.generate()` signature to:
  ```python
  async def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.7, max_tokens: Optional[int] = None) -> str
  ```
- **`KoboldCppProvider`**:
  - Set `"max_tokens": max_tokens or 4096` in JSON payload.
- **`OllamaProvider`**:
  - Set `"num_predict": max_tokens or 4096` in `options` JSON payload.
- **`GeminiProvider`**:
  - Set `"maxOutputTokens": max_tokens or 4096` in `generationConfig` JSON payload.
- **`AIProviderManager`**:
  - Forward `max_tokens` in `generate()` method call.

### 3.6 Response Parser & Prompt Extractor (`backend/app/services/ai/utils.py` / `krea2_optimizer.py` / `vision_service.py` / `prompt_assistant.py`)
Add `extract_final_prompt(raw_text: str) -> str`:
```python
def extract_final_prompt(raw_text: str) -> str:
    if not raw_text:
        return ""
    
    text = raw_text.strip()

    # 1. Gemma 4 channel format: <|channel>thought...\n<|channel>text\n...
    if "<|channel>text" in text:
        parts = text.split("<|channel>text")
        text = parts[-1].strip()

    # 2. XML think tag format: <think>...</think>...
    if "</think>" in text:
        parts = text.split("</think>")
        text = parts[-1].strip()

    # 3. Handle leftover opening thinking tags if truncated or isolated
    if text.startswith("<|channel>thought"):
        # Look for double newline or prompt header
        match = re.search(r'(?:Krea 2 Prompt|Optimized Prompt|Prompt|Final):\s*(.*)', text, re.IGNORECASE | re.DOTALL)
        if match:
            text = match.group(1).strip()

    # Clean residual tags
    text = re.sub(r'<\|channel\|?>', '', text).strip()
    return text
```
Wrap all returned prompts in `krea2_optimizer.py`, `vision_service.py`, and `prompt_assistant.py` with `extract_final_prompt()`.

---

## 4. Verification Plan
1. **Unit Tests**:
   - Test `extract_final_prompt()` with:
     - Gemma 4 thinking trace (`<|channel>thought ... <|channel>text Here is prompt`).
     - DeepSeek XML think trace (`<think> reasoning </think> Here is prompt`).
     - Truncated/header thought response.
     - Pure unthinking mode response (returns input untouched).
   - Test `KoboldCppProvider.generate()` sending `max_tokens` in payload.
   - Test `Krea2Optimizer.improve_prompt()` with `max_tokens` and thinking responses.
   - Test `VisionService.describe_image()` with `max_tokens` and thinking responses.
2. **Integration Verification**:
   - Run backend pytest suite: `pytest backend/tests`
   - Test API connection and generation endpoints.
