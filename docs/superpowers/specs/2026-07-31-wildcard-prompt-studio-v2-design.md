# Wildcard Prompt Studio V2 — Architecture & Krea 2 Prompt Optimization Design Specification

**Date**: 2026-07-31  
**Status**: Approved  
**Author**: Antigravity Assistant & Engineering Team  

---

## 1. Overview & Objectives

Wildcard Prompt Studio V2 is a major architectural overhaul designed to solve core backend bottlenecks, introduce a robust AST-based wildcard expansion engine, and integrate a specialized **Krea 2 Prompt Optimization Suite**.

### Key Goals:
1. **Krea 2 Prompt Engineering**: Implement official Krea 2 prompting guidelines (natural language focus, faithfulness first, text quote formatting `"text"`, buzzword removal, and model variant tuning for Turbo, Medium, and Large).
2. **Hybrid AI Provider Engine**: Support local LLMs (Ollama, KoboldCpp) alongside Cloud LLM APIs (Google Gemini, OpenAI, Anthropic) with provider fallback chains.
3. **Advanced AST Wildcard Parser**: Handle recursive nested choices (`{a|{b|c}}`), weight syntax (`{3$$optA|1$$optB}`), subdirectory wildcards (`__folder/wildcard__`), and combinatorial matrix sweeps.
4. **Async & Performance Optimizations**: Move vector model embedding operations off web request threads and eliminate blocking DB operations.
5. **Modernized Frontend UX**: Add dedicated Krea 2 controls, side-by-side prompt diffing, matrix batch preview, and environment-configurable API endpoints.

---

## 2. Architecture & System Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            FRONTEND (React + Vite)                          │
│                                                                             │
│  ┌────────────────────────┐ ┌────────────────────────┐ ┌─────────────────┐  │
│  │   Krea2StudioPanel     │ │  WildcardMatrixPanel   │ │ PromptEditor    │  │
│  │ (Variant / Diff / Quote│ │ (AST Preview / Sweep)  │ │ (ComfyUI Batch) │  │
│  └───────────┬────────────┘ └───────────┬────────────┘ └────────┬────────┘  │
└──────────────┼──────────────────────────┼───────────────────────┼───────────┘
               │                          │                       │
               ▼                          ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          BACKEND API (FastAPI)                              │
│                                                                             │
│  ┌───────────────────────┐ ┌─────────────────────────┐ ┌─────────────────┐ │
│  │  /api/v1/ai/improve   │ │ /api/v1/generate/matrix │ │ /api/v1/prompts │ │
│  └───────────┬───────────┘ └────────────┬────────────┘ └────────┬────────┘ │
│              │                          │                       │           │
│              ▼                          ▼                       ▼           │
│  ┌───────────────────────┐ ┌─────────────────────────┐ ┌─────────────────┐ │
│  │ Krea2OptimizerService │ │   WildcardASTEngine     │ │ Async Vector DB │ │
│  └───────────┬───────────┘ └─────────────────────────┘ └─────────────────┘ │
│              │                                                              │
│              ▼                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    AIProviderManager (Fallback Chain)                  │ │
│  │    [Ollama] <──> [KoboldCpp] <──> [Gemini] <──> [OpenAI/Anthropic]     │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Component Specifications

### 3.1 AI Provider Engine & Krea 2 Optimizer (`backend/app/services/ai/`)

#### **`AIProviderManager`**
- Unified async interface `generate(prompt: str, system_prompt: str, options: dict) -> str`.
- Implementations:
  - `OllamaProvider`: Local REST API (`/api/generate`).
  - `KoboldCppProvider`: Local OpenAI-compatible REST endpoint (`/v1/chat/completions`).
  - `GeminiProvider`: Google Gemini client / REST API.
  - `OpenAIProvider`: OpenAI ChatCompletions REST API.
- Priority chain execution with failover error handling.

#### **`Krea2OptimizerService` (`backend/app/services/krea2_optimizer.py`)**
- **System Prompt Expansion**: Injects Krea 2 rules (faithfulness first, T2I structure grouping, style planning, natural language focus).
- **Variant Tuning Presets**:
  - **Turbo**: Direct, high-impact natural language optimized for 2K resolution & rapid generation.
  - **Medium**: Expressive art/illustration styling (anime, paintings, digital art).
  - **Large**: High texture fidelity, camera optics, depth of field, natural lighting for photorealism.
- **Quote Assistant**: Auto-detects text rendering targets and wraps them in exact double quotes (`"text"`).
- **Buzzword Stripper**: Strips legacy SD anti-patterns (`8k`, `4k`, `masterpiece`, `trending on artstation`, `hyper-detailed`).

---

### 3.2 Wildcard AST Engine & Matrix Expansion (`backend/app/services/wildcard_ast.py`)

- **Tokenizer & Parser**:
  - Lexes prompt tokens: `TEXT`, `WILDCARD` (`__name__`), `CHOICE_START` (`{`), `CHOICE_END` (`}`), `PIPE` (`|`), `WEIGHT` (`3$$`).
- **AST Nodes**:
  - `TextNode(content: str)`
  - `WildcardNode(name: str)`
  - `ChoiceNode(options: List[ASTNode], weights: List[int])`
  - `RootNode(children: List[ASTNode])`
- **Evaluator**:
  - Recursive evaluation with max depth protection.
  - `sample()`: Single random prompt generation.
  - `matrix_sweep(max_limit=100)`: Cartesian product matrix generation for batch testing.

---

### 3.3 Backend Performance & Async Database Layer

- **`get_async_embedder()`**: Lazy initialization and background thread execution of `SentenceTransformer` to avoid blocking main FastAPI event loop threads.
- **Async API Handlers**: Update FastAPI routes to handle database queries non-blockingly.

---

### 3.4 Frontend Krea 2 Studio Component Suite (`frontend/src/`)

- **`Krea2StudioPanel.tsx`**:
  - Model Variant Selector (**Turbo**, **Medium**, **Large**).
  - Provider Selector (Local Ollama/KoboldCpp vs Gemini/OpenAI).
  - 1-Click Action Buttons (**Krea 2 Expand**, **Strip Buzzwords**, **Quote Text Helper**).
  - **Side-by-Side Diff Viewer**: Highlights added/removed prompt phrases with "Apply to Editor" option.
- **`WildcardMatrixPanel.tsx`**:
  - Live wildcard preview and combinatorial sweep table.
- **`api.ts` & Config**:
  - Use `import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/v1'`.

---

## 4. Verification & Testing Plan

1. **Unit Tests (`backend/tests/`)**:
   - `test_krea2_optimizer.py`: Verify system prompt injection, buzzword stripping, quote wrapping, and variant presets.
   - `test_wildcard_ast.py`: Test nested choice parsing, weighted choices, subdirectory wildcards, and matrix sweep generation.
   - `test_ai_providers.py`: Mock provider endpoints and verify fallback logic.
2. **Frontend Component Tests**:
   - Verify Krea 2 panel rendering, variant toggle, and diff viewer state updates.
3. **Integration Verification**:
   - Test end-to-end prompt expansion flow from frontend to backend.
