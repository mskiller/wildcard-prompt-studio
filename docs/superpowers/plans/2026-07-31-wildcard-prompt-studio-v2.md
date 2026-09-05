# Wildcard Prompt Studio V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Wildcard Prompt Studio V2 with Krea 2 prompt optimization, multi-provider LLM support, AST wildcard expansion, matrix generation, async vector search, and a modernized React UI suite.

**Architecture:** A decoupled FastAPI backend containing pluggable AI Providers (Ollama, KoboldCpp, Gemini), a dedicated `Krea2OptimizerService` (implementing Krea 2 natural language expansion, variant presets, quote wrapping, and buzzword cleaning), an AST-based wildcard parser (`WildcardASTEngine`) with matrix combinatorial sweeps, and an enhanced Vite React frontend (`Krea2StudioPanel`).

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy, Pytest, React 18, Vite, TypeScript.

---

## File Structure & Responsibilities

### Backend Files:
- `backend/app/services/ai/provider.py`: Abstract `AIProvider` base class.
- `backend/app/services/ai/ollama_provider.py`: Ollama REST integration.
- `backend/app/services/ai/kobold_provider.py`: KoboldCpp OpenAI-compatible REST integration.
- `backend/app/services/ai/gemini_provider.py`: Google Gemini REST integration.
- `backend/app/services/ai/provider_manager.py`: Multi-provider registry and fallback manager.
- `backend/app/services/krea2_optimizer.py`: Krea 2 system prompt rules, variant presets (Turbo, Medium, Large), quote formatter, and buzzword stripper.
- `backend/app/services/wildcard_ast.py`: AST lexer, parser, and recursive tree evaluator for nested choices `{a|{b|c}}` and weighted syntax.
- `backend/app/services/matrix_engine.py`: Combinatorial matrix generator for prompt variations.
- `backend/app/api/routers/ai.py`: FastAPI endpoints for Krea 2 improvement and provider configurations.
- `backend/app/api/routers/generate.py`: FastAPI endpoints for prompt expansion and matrix sweeps.

### Frontend Files:
- `frontend/src/api.ts`: Updated API client supporting environment configuration (`import.meta.env.VITE_API_BASE`), Krea 2 endpoints, and matrix expansion.
- `frontend/src/components/editor/Krea2StudioPanel.tsx`: Dedicated Krea 2 panel featuring variant selector, provider selection, 1-click expand/buzzword removal/quote helper, and side-by-side prompt diffing.
- `frontend/src/App.tsx`: App layout integrating Krea 2 studio panel and matrix sweep tool.

---

## Tasks

### Task 1: Pluggable AI Provider Infrastructure

**Files:**
- Create: `backend/app/services/ai/provider.py`
- Create: `backend/app/services/ai/ollama_provider.py`
- Modify: `backend/app/services/ai/kobold_provider.py`
- Create: `backend/app/services/ai/gemini_provider.py`
- Create: `backend/app/services/ai/provider_manager.py`
- Test: `backend/tests/test_ai_providers.py`

- [ ] **Step 1: Write failing tests for AI providers and ProviderManager**

```python
import pytest
from app.services.ai.provider import AIProvider
from app.services.ai.kobold_provider import KoboldCppProvider
from app.services.ai.ollama_provider import OllamaProvider
from app.services.ai.provider_manager import AIProviderManager

def test_provider_manager_fallback():
    manager = AIProviderManager()
    manager.register_provider("kobold", KoboldCppProvider("http://invalid-host:9999"))
    manager.register_provider("ollama", OllamaProvider("http://invalid-host:9999"))
    
    providers = manager.list_providers()
    assert "kobold" in providers
    assert "ollama" in providers
```

- [ ] **Step 2: Implement abstract `AIProvider` base class**

```python
from abc import ABC, abstractmethod

class AIProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.7) -> str:
        pass
```

- [ ] **Step 3: Implement `OllamaProvider`, `GeminiProvider`, and `AIProviderManager`**

Implement `OllamaProvider` targeting Ollama API (`/api/chat`), `GeminiProvider` using Google Gemini REST/SDK, and `AIProviderManager` for provider lookup and failover execution.

- [ ] **Step 4: Run tests and verify PASS**

Run: `python -m pytest backend/tests/test_ai_providers.py`

---

### Task 2: Krea 2 Optimization & Expansion Engine

**Files:**
- Create: `backend/app/services/krea2_optimizer.py`
- Test: `backend/tests/test_krea2_optimizer.py`

- [ ] **Step 1: Write failing unit tests for Krea 2 optimizer functions**

```python
import pytest
from app.services.krea2_optimizer import Krea2Optimizer, clean_buzzwords, format_quotes

def test_clean_buzzwords():
    raw_prompt = "a cute red panda, 8k, masterpiece, hyper-detailed, photorealistic"
    cleaned = clean_buzzwords(raw_prompt)
    assert "8k" not in cleaned
    assert "masterpiece" not in cleaned
    assert "hyper-detailed" not in cleaned
    assert "a cute red panda" in cleaned

def test_format_quotes():
    prompt = "a poster with text hello world on it"
    formatted = format_quotes(prompt, targets=["hello world"])
    assert '"hello world"' in formatted
```

- [ ] **Step 2: Implement `clean_buzzwords` and `format_quotes` utility functions**

```python
import re

BUZZWORDS = [
    r'\b8k\b', r'\b4k\b', r'\bmasterpiece\b', r'\bhyper-detailed\b',
    r'\bphotorealistic\b', r'\btrending on artstation\b', r'\bultra detailed\b'
]

def clean_buzzwords(prompt: str) -> str:
    cleaned = prompt
    for pattern in BUZZWORDS:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    # clean extra commas and double spaces
    cleaned = re.sub(r',\s*,', ',', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip(', ')
    return cleaned

def format_quotes(prompt: str, targets: list[str]) -> str:
    res = prompt
    for target in targets:
        if target and target in res and not f'"{target}"' in res:
            res = res.replace(target, f'"{target}"')
    return res
```

- [ ] **Step 3: Implement `Krea2Optimizer` class with Turbo, Medium, and Large variant system prompts**

Implement system prompt builder using official Krea 2 rules (faithfulness first, T2I natural language structure, style planning, resolution handling).

- [ ] **Step 4: Run tests and verify PASS**

Run: `python -m pytest backend/tests/test_krea2_optimizer.py`

---

### Task 3: Wildcard AST Parser & Combinatorial Matrix Generator

**Files:**
- Create: `backend/app/services/wildcard_ast.py`
- Create: `backend/app/services/matrix_engine.py`
- Test: `backend/tests/test_wildcard_ast.py`

- [ ] **Step 1: Write failing tests for nested choices and weighted choices**

```python
import pytest
from app.services.wildcard_ast import WildcardASTEngine

def test_nested_choice_parsing():
    engine = WildcardASTEngine()
    prompt = "a {cat|{dog|lion}}"
    results = set()
    for _ in range(50):
        results.add(engine.expand(prompt))
    assert "a cat" in results
    assert "a dog" in results or "a lion" in results

def test_matrix_sweep():
    engine = WildcardASTEngine()
    prompt = "{red|blue} {car|bike}"
    combinations = engine.matrix_sweep(prompt)
    assert len(combinations) == 4
    assert "red car" in combinations
    assert "blue bike" in combinations
```

- [ ] **Step 2: Implement `WildcardASTEngine` parser & evaluator**

Implement recursive descent parser for tokens `{`, `}`, `|`, `weight$$`, `__wildcard__`, returning an AST representation and resolving `sample()` and `matrix_sweep()`.

- [ ] **Step 3: Run tests and verify PASS**

Run: `python -m pytest backend/tests/test_wildcard_ast.py`

---

### Task 4: Backend Async Routes & Krea 2 API Integration

**Files:**
- Modify: `backend/app/api/routers/ai.py`
- Modify: `backend/app/api/routers/generate.py`
- Test: `backend/tests/test_api_endpoints.py`

- [ ] **Step 1: Add `/api/v1/ai/krea2-improve` and `/api/v1/generate/matrix` endpoints**

Expose Krea 2 options (variant: Turbo/Medium/Large, quote_targets, clean_buzzwords) and matrix combinatorial generator endpoint.

- [ ] **Step 2: Run backend tests to verify API endpoints**

Run: `python -m pytest backend/tests`

---

### Task 5: Frontend Krea 2 Studio Component Suite

**Files:**
- Modify: `frontend/src/api.ts`
- Create: `frontend/src/components/editor/Krea2StudioPanel.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Update `frontend/src/api.ts` to use `import.meta.env.VITE_API_BASE` and add `krea2ImprovePrompt` and `expandMatrixPrompt`**
- [ ] **Step 2: Build `Krea2StudioPanel.tsx` with variant toggle (Turbo/Medium/Large), 1-click action buttons, and side-by-side prompt diffing view**
- [ ] **Step 3: Integrate `Krea2StudioPanel` into `frontend/src/App.tsx`**

---
