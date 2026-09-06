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

### 2.5 Danbooru Lexicon & Co-occurrence Synergy Graph (`app/services/danbooru_service.py`)
- **Dedicated SQLite B-Tree Index**: Stores 31,060 curated Danbooru tags and 3,236,959 co-occurrence edges at `backend/app/data/danbooru_lexicon.db`.
- **Sub-Millisecond Traversal**: Composite index on `(tag_a, count DESC)` allows querying top co-occurring tags in **0.22ms**.
- **Prompt Synergy Algorithm**:
  1. Tokenizes incoming prompt string, strips SD weights and punctuation, ignores wildcard syntax (`__tag__`).
  2. Traverses co-occurrence edges for each token up to top 40 relations.
  3. Computes cumulative synergy score across all token pairings.
  4. Returns top candidates with domain categories (`artist`, `character`, `copyright`, `meta`, `general`) and pairing explanations (e.g., `"Pairs with 1girl"`).
- **PostgreSQL Ingestion**: Provides optional one-click ingestion into the main PostgreSQL `tags` table without bloating primary database transactions with 3.2M edge rows.

---

### 2.6 AST Tag Extraction & Sanitization Pipeline (`app/services/wildcard_ast.py`)
- **Automated Extraction**: Traverses `TextNode`, `ChoiceNode`, and `VarAssignmentNode` trees to extract atomic leaves when wildcards are created, edited, or imported.
- **Heuristic Cleaner (`sanitize_single_tag`)**:
  - Strips dynamic prompt choice syntax (`{4::`, `{1::1::`, `1$$`).
  - Strips Stable Diffusion weights (`(tag:1.3)`, `[tag:1.2]`, `:1.2)`).
  - Filters punctuation noise, English stop words, and lengthy natural-language sentence fragments (>60 chars / >7 words).
- **Semantic Domain Classifier (`classify_tag_category`)**: Automatically sorts tags into `Character`, `Clothing`, `Lighting`, `Style`, `Camera`, `Quality / Score`, or `General`.

---

### 2.7 Database Integrity & Foreign Key Safeguards (`app/api/routers/system.py`)
- **System Administration**: Provides unified counts of tags, wildcards, prompts, versions, images, and model profiles.
- **Foreign Key Safeguards**:
  - `prompt_tags`: `ondelete="CASCADE"` deletes association links cleanly.
  - `images.prompt_id`: `ondelete="SET NULL"` detaches images when parent prompts are deleted, ensuring generated gallery images remain intact and accessible without orphaned foreign key errors.
- **Protected Factory Reset**: Guarded endpoint requiring confirmation code `"RESET"` before purging all user data.

---

### 2.8 ComfyUI Sweep Dispatch & Discord Webhook Integration (`app/api/routers/comfyui.py`)
- **Background Task Poller**: Asynchronously tracks batch sweep job IDs on ComfyUI via HTTP/WebSocket without blocking client requests.
- **Discord Bot Webhook Dispatch**:
  - Automatically loads webhook URL from `ComfyUI-SendToDiscord/config.ini` or user settings.
  - Transmits rendered PNG files with companion `prompt.txt` as multi-part form data to Discord channels using `httpx.AsyncClient`.


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
