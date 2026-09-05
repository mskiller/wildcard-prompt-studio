# Wildcard Prompt Studio V2 — Architecture Specification

This document provides a technical overview of the system architecture, design decisions, data flow, and component interactions in **Wildcard Prompt Studio V2**.

---

## 1. High-Level Architecture Overview

Wildcard Prompt Studio V2 is designed as a decoupled client-server web platform optimized for low latency and high concurrency:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            FRONTEND (React 18 + Vite)                       │
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

## 2. Backend Services (`backend/app/`)

The backend is built with **FastAPI** using asynchronous (`async/await`) request handlers and background task delegation.

### 2.1 Krea 2 Optimizer Service (`app/services/krea2_optimizer.py`)
- **System Prompt Formulation**: Generates Krea 2 compliance system prompts based on targeted model variants:
  - **Turbo**: Prioritizes concise, direct natural language descriptions.
  - **Medium**: Embeds artistic, digital painting, and stylized parameters.
  - **Large**: Emphasizes camera optics (lens, depth-of-field, lighting, physical texture properties).
- **Buzzword Stripper Engine**: Employs regex pattern matching to remove legacy SD quality modifiers (`8k`, `masterpiece`, `trending on artstation`).
- **Quote Text Transformer**: Scans prompts for text targets (`a neon sign saying hello`) and formats them to exact quoted expressions (`"hello"`).

---

### 2.2 Wildcard AST Engine (`app/services/wildcard_ast.py`)
The Abstract Syntax Tree (AST) parser replaces legacy string-replacement wildcards:

1. **Tokenizer (Lexer)**: Scans raw prompt string into token streams:
   - `TEXT`: Plain string literals.
   - `WILDCARD`: `__category/file__`.
   - `CHOICE_START` / `CHOICE_END`: `{` and `}`.
   - `PIPE`: `|`.
   - `WEIGHT`: `3$$`.
2. **Parser**: Constructs recursive AST node hierarchies:
   - `RootNode([children])`
   - `TextNode(content)`
   - `WildcardNode(name)`
   - `ChoiceNode(options, weights)`
3. **Evaluator**:
   - `sample()`: Random evaluation traversing choice nodes according to probability weights.
   - `matrix_sweep()`: Computes Cartesian products to generate all possible prompt permutations up to configurable limits.

---

### 2.3 Hybrid AI Provider Engine (`app/services/ai/`)
Unified async provider management with failover support:

- `AIProviderManager`: Orchestrates request dispatches to configured providers.
- **Provider Implementations**:
  - `OllamaProvider`: Local REST API integration (`/api/generate`).
  - `KoboldCppProvider`: Local OpenAI-compatible REST integration.
  - `GeminiProvider`: Async Google Gemini client integration.
  - `OpenAIProvider`: OpenAI REST API.
- **Priority Chain**: Executes provider requests in user-defined priority order; automatically captures exceptions and retries via secondary provider if primary fails.

---

### 2.4 Non-Blocking Async RAG & Vector DB (`app/services/async_rag.py`)
- **Lazy Initialization**: `SentenceTransformer` models are loaded lazily on first access.
- **Background Thread Offloading**: Embedding generation is delegated to `asyncio.to_thread` workers to prevent blocking FastAPI's main event loop.

---

## 3. Frontend Architecture (`frontend/src/`)

The frontend is a single-page React 18 application built with Vite:

- **Monaco Code Editor (`MonacoPromptEditor.tsx`)**: Customized Monaco Editor instance supporting wildcard token highlighting, autocompletion, and live syntax validation.
- **State Management (`store/`)**: Powered by **Zustand** for lightweight, predictable reactive state handling:
  - `usePromptStore`: Holds active prompt text, prompt library, history, and diff buffers.
  - `useSettingsStore`: Stores theme selection (Cyberpunk, Dark, Light), i18n locale, and API host config.
- **Internationalization (`i18n.ts`)**: Supports EN, ZH, and JP localization across all UI components.

---

## 4. Sequence & Execution Workflows

### Prompt Optimization Workflow
```
[User Clicks Krea 2 Expand]
         │
         ▼
[Frontend: Krea2StudioPanel] ──(POST /api/v1/ai/improve)──► [Backend API]
                                                                  │
                                                                  ▼
                                                      [Krea2OptimizerService]
                                                                  │
                                                                  ▼
                                                       [AIProviderManager]
                                                                  │
                                                    ┌─────────────┴─────────────┐
                                                    ▼                           ▼
                                             (Primary: Ollama)          (Fallback: Gemini)
                                                    │                           │
                                                    └─────────────┬─────────────┘
                                                                  │
                                                                  ▼
                                                     [Generated Clean Prompt]
                                                                  │
                                                                  ▼
                                                      [Return Diff & Prompt]
                                                                  │
                                                                  ▼
                                                     [Render Side-by-Side Diff]
```
