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

### 2.4 Persistent Unified RAG & pgvector Store (`app/services/unified_rag.py`)
- **pgvector Native Storage**: Upgraded knowledge store using PostgreSQL `pgvector` with 384-dimensional dense vectors generated via `all-MiniLM-L6-v2`.
- **Pre-Seeded Knowledge Bases**: Automatically ingests domain prompting guides for Krea 2, ANIMA, ComfyUI workflows, and Wildcard AST grammar upon database initialization.
- **Thread Safety & Mutex Lock**: Employs an `asyncio.Lock` to guarantee safe concurrent embedding computations across worker threads.
- **Graceful Runtime Fallback**: Employs an offline/mock fallback mechanism when model weights cannot be downloaded or hardware acceleration is unavailable, ensuring API calls never hang.
- **Application Lifespan Integration**: Properly registers and terminates during FastAPI lifespan events, cleanly closing vector model sessions.

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

### 2.9 Gallery Architecture & Image Metadata Auto-Healing (`app/api/routers/images.py`, `app/services/image_metadata.py`)
- **PNG Chunk Metadata Extraction**: Scans embedded ComfyUI workflow JSON and prompt texts from rendered PNG files directly using standard library chunks parsing.
- **Auto-Healing Relational Repair**: On image retrieval (`/gallery` or `/{id}`), automatically resolves broken prompt links and backfills missing generation parameters (seed, steps, CFG, sampler, dimensions) from disk into PostgreSQL.
- **pgvector Cosine Distance Similarity**: Computes real-time cosine distance over prompt embedding vectors to discover visually and conceptually related images without requiring external vector indices.
- **Safe Batch Operations**: Atomic deletion guarantees that disk files are only removed after database transactions commit successfully.

---

### 2.10 Matrix Engine Safety & Caching Pipeline (`app/services/matrix_engine.py`, `app/services/wildcard_service.py`)
- **Cartesian Explosion Safety**: Implements strict safety limits and early stopping to prevent server freeze and memory crashes when computing massive matrix permutations.
- **In-Memory Wildcard Cache**: Caches parsed wildcard files with automatic cache invalidation triggers on create, update, or deletion.
- **Lightweight Serialization**: `GET /api/v1/wildcards` queries project metadata columns by default (`include_content=false`), reducing serialization overhead and payload bandwidth by ~99%.

---

### 2.11 Direct Indexing Engine & Factor Decomposition (`MatrixIndexingEngine`)
- **Mathematical Space Formulation**: Models Cartesian combinations as a multi-dimensional space $S = C_1 \times C_2 \times \dots \times C_k$ where $|S| = \prod_{i=1}^k |C_i|$.
- **Closed-Form Permutation Counting**: Computes total permutation spaces in $O(k)$ time where $k$ is the number of choice dimensions, eliminating the need to materialize combinations in memory.
- **Mixed-Radix Coordinate Decomposition**:
  - Defines coordinate stride weights $w_i = \prod_{j=i+1}^k |C_j|$ with $w_k = 1$.
  - For any integer index $n \in [0, |S|-1]$, choice option $c_i = \lfloor \frac{n}{w_i} \rfloor \pmod{|C_i|}$.
  - Computes any specific prompt combination in $O(k)$ time without generating prior permutations.
- **Arbitrary Range Slicing & Sampling**:
  - `slice(start_index, limit)`: Evaluates indices $[start, start+limit)$ on demand in sub-millisecond response times.
  - `sample(count, seed)`: Generates pseudo-random unique index sets within $[0, |S|-1]$ and resolves them directly.

---

### 2.12 Discord Sweep Delivery & Reliability Pipeline (`app/api/routers/comfyui.py`)
- **Multi-Source Config Resolution**: Dynamically reads webhook configuration with fallback priority:
  1. Local ComfyUI custom node config file: `ComfyUI-SendToDiscord/config.ini`.
  2. Server environment variable: `DISCORD_WEBHOOK_URL`.
  3. User settings database value.
- **Background Polling & Multi-Part Dispatch**:
  - Background asynchronous task monitors ComfyUI WebSocket job completion.
  - Dispatches rendered PNG image bytes alongside structured metadata (prompt text, seed, steps, sampler, scheduler, dimensions) as `multipart/form-data`.
  - Implements exponential backoff retry logic for handling Discord rate limits (HTTP 429) and network transients.

---

## 3. Frontend Architecture (`frontend/src/`)

The frontend is a single-page React 18 application built with Vite:

- **Monaco Code Editor (`MonacoPromptEditor.tsx`)**: Customized Monaco Editor instance supporting wildcard token highlighting, autocompletion, and live syntax validation.
- **Wildcard Search Picker (`WildcardSearchPicker.tsx`)**:
  - Reusable search dropdown supporting real-time fuzzy filtering, categorized taxonomy display, and query highlighting.
  - Full keyboard accessibility (Arrow Up/Down navigation, Enter selection, Escape dismissal).
  - Wheel event decoupling: intercepts mouse wheel events internally to enable smooth dropdown scrolling without propagating zoom or pan events to parent Visual AST canvases.
  - Deployed in Visual AST Canvas nodes (`CanvasWildcardNode`), Node Inspector drawer, and Matrix Studio toolbar.
- **Slice Navigator (`WildcardMatrixPanel.tsx`)**:
  - High-performance pagination controls (50, 100, 250, 500 items/page).
  - Direct index jump and pseudo-random sampling with reproducible seed.
  - Flexible batch queue integration supporting range slice and sample dispatch modes to ComfyUI.
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
