# Design Specification: RAG System Enhancement, Cross-Tab Integration & Gallery Studio Overhaul

**Date:** 2026-09-06  
**Status:** Approved by User  
**Scope:** Backend persistent vector pipeline (pgvector), Cross-Tab RAG intelligence (Editor, Krea 2, Anima, Tags, Vision), and Gallery Studio workstation overhaul.

---

## 1. Overview & Objectives

Wildcard Prompt Studio currently features several specialized prompt engineering and generation tabs (Monaco Editor, Wildcard Matrix, Krea 2 Studio, Anima Studio, Tags View, Vision Inspector, and Gallery). However, two major limitations hinder its workflow:
1. **RAG Isolation & Fragility**: The RAG implementation uses an in-memory mock store that does not persist across restarts, employs arbitrary token matching rather than true semantic vector embeddings, has fragmented embedding dimensions (`Vector(1536)` vs `Vector(384)`), and is not leveraged in primary generation tabs like Krea 2 and Anima.
2. **Gallery Limitations**: The Gallery view is a basic, unsearchable grid that only displays minimal metadata (seed, cfg, sampler) on hover. It lacks prompt search, filtering, star ratings/favorites, aesthetic score badges, batch operations, side-by-side comparison, and direct workflow roundtrips back into the studios.

This specification unifies the RAG backend into a persistent 384-dimensional pgvector service, integrates RAG intelligence across all studio tabs, and transforms the Gallery into a high-productivity visual studio.

---

## 2. Architecture & Backend Services

### 2.1 Persistent 384-Dimension Vector Architecture

All vector stores in PostgreSQL (`pgvector`) are standardized on **384 dimensions** matching `sentence-transformers/all-MiniLM-L6-v2`:
* **`KnowledgeDocument` (`app/models/knowledge.py`)**:
  * `id`: Integer, primary key, index.
  * `title`: String, non-nullable.
  * `content`: Text, non-nullable.
  * `category`: String (e.g., `model_guide`, `optics`, `anime_style`, `negative_rules`, `user_vault`).
  * `tags`: JSON/List of strings.
  * `embedding`: `Vector(384)`.
  * `created_at`: DateTime, server default `func.now()`.
  * `updated_at`: DateTime, on update `func.now()`.
* **`Image` (`app/models/image.py`)**:
  * Existing fields: `id`, `filename`, `prompt_id`, `seed`, `cfg_scale`, `steps`, `sampler_name`, `width`, `height`, `comfy_workflow_id`, `created_at`.
  * Added fields:
    * `is_favorite`: Boolean, default `False`, indexed.
    * `rating`: Integer, default `0` (range 0–5 stars), indexed.
    * `aesthetic_score`: Float, nullable, indexed.
* **Alembic Migration**:
  * Adjust `knowledge_documents.embedding` column to `Vector(384)` if currently 1536.
  * Add `category`, `tags`, `created_at`, `updated_at` to `knowledge_documents`.
  * Add `is_favorite`, `rating`, `aesthetic_score` to `images`.

### 2.2 Unified RAG Service (`app/services/unified_rag.py`)

A singleton service `unified_rag_service` replaces the mock in-memory store in `async_rag.py`:
* **Model Management & Fallback**:
  * Lazy-loads `SentenceTransformer("all-MiniLM-L6-v2")` inside an asynchronous thread pool executor (`ThreadPoolExecutor(max_workers=2)`).
  * In offline or resource-constrained environments where model weights cannot be downloaded, smoothly falls back to deterministic MD5-based pseudo-embeddings so the application never crashes.
* **Pre-Seeded Domain Knowledge**:
  On startup or when the knowledge table is empty, seeds official prompt knowledge:
  1. *Krea 2 Prose & Composition*: Structuring prompts into natural descriptive language, subject framing, lighting cues, and quote formatting.
  2. *ANIMA Anime Rules*: Character-focused tag hierarchy, cel shading, line art, and quality score tag conventions (`score_9, score_8`).
  3. *Photorealism & Lighting*: Prime lenses (85mm, 50mm, f/1.4), volumetric light, subsurface scattering, skin texture, Rembrandt lighting.
  4. *Negative Prompting Guidelines*: Artifact suppression, anatomy fixers, and background cleaner rules.
* **Hybrid Search Engine**:
  * Executes vector cosine distance queries via `KnowledgeDocument.embedding.cosine_distance(query_vec)` using SQLAlchemy and pgvector.
  * Combines vector distance with optional text keyword matching (`content.ilike(...)`) and tag/category filtering.
  * Returns normalized similarity scores (`0.0` to `1.0` or `0%` to `100%`).

---

## 3. Cross-Tab RAG Integration

### 3.1 Prompt Editor & Prompt Chat Drawer
* **Contextual Improvement**:
  * In `/api/v1/ai/improve` and `/api/v1/ai/chat-refine`, when `use_rag=True`, the engine queries both `KnowledgeDocument` (for style/syntax rules) and `Prompt` (for user past examples) using the prompt embedding.
* **Editor Quick Action**:
  * Adds an "Index to RAG Vault" action in the editor header and Context Panel to save any prompt directly into the persistent vector database.

### 3.2 Krea 2 Studio Panel
* **Backend (`krea2_optimizer.py`)**:
  * Update `Krea2ImproveRequest` to accept `use_rag: bool = False`.
  * When `use_rag=True`, `krea2_optimizer` retrieves top matching knowledge documents tagged with `krea`, `cinematic`, or `optics` and appends them as concrete formatting instructions in the system prompt.
* **Frontend (`Krea2StudioPanel.tsx`)**:
  * Add a "Use RAG Guidelines" toggle switch with a real-time badge indicating active knowledge retrieval.

### 3.3 Anima Studio Panel
* **Backend (`anima_optimizer.py`)**:
  * Update `AnimaImproveRequest` to accept `use_rag: bool = False`.
  * When `use_rag=True`, `anima_optimizer` retrieves knowledge documents tagged with `anima`, `anime`, or `danbooru` to ensure correct tag order, score tag placement, and artist token conventions.
* **Frontend (`AnimaStudioPanel.tsx`)**:
  * Add a "Use RAG Guidelines" toggle switch directly next to the variant selector.

### 3.4 Tags View (Tags & Danbooru Lexicon)
* **Semantic Tag Discovery**:
  * Add an input bar: "Discover Tags via Semantic Meaning (e.g. moody rain, glowing neon cyber city)".
  * On search, queries the vector engine against indexed tag descriptions and Danbooru concepts, displaying recommended tags with 1-click "Add to Active Prompt" and "Copy Tag".

### 3.5 Vision Inspector Panel
* **Structured RAG Indexing**:
  * After extracting visual descriptors from an uploaded image, the user can review and edit the Title, Category, and Tags before submitting to `/api/v1/ai/vision/extract-style?index_rag=true`, saving directly into persistent `knowledge_documents`.

---

## 4. Gallery Studio Overhaul

### 4.1 Backend Endpoints (`app/api/routers/images.py`)

* **`GET /api/v1/images/gallery`**:
  * Parameters:
    * `skip: int = 0`
    * `limit: int = 50`
    * `search: Optional[str] = None` (filters prompt content and filename)
    * `sampler: Optional[str] = None`
    * `is_favorite: Optional[bool] = None`
    * `min_rating: Optional[int] = None`
    * `sort_by: str = "newest"` (`newest`, `oldest`, `rating`, `aesthetic_score`)
  * Returns list of images with linked prompt content and metadata.
* **`PATCH /api/v1/images/{image_id}/favorite`**:
  * Toggles `is_favorite` boolean; returns updated record.
* **`PATCH /api/v1/images/{image_id}/rating`**:
  * Body: `{"rating": int}` (0–5); returns updated record.
* **`POST /api/v1/images/{image_id}/score-aesthetic`**:
  * Runs backend aesthetic scorer on the image prompt/file and saves `aesthetic_score`.
* **`POST /api/v1/images/batch/delete`**:
  * Body: `{"image_ids": List[int]}`
  * Deletes database records and static image files; returns `{ "deleted_count": int }`.
* **`POST /api/v1/images/batch/index-rag`**:
  * Body: `{"image_ids": List[int], "category": Optional[str]}`
  * Embeds and inserts prompt content and generation parameters into `knowledge_documents`.
* **`GET /api/v1/images/{image_id}/similar`**:
  * Returns images with prompt embeddings closest to the target image's prompt.

### 4.2 Frontend Architecture (`GalleryView.tsx` & `GalleryView.css`)

* **Control Bar**:
  * **Search Input**: Live debounced search across prompt text and file names.
  * **Filters**:
    * Favorite toggle button (`All` / `Favorites Only`).
    * Sampler dropdown (extracted dynamically from loaded images).
    * Minimum rating dropdown (`Any`, `3+ Stars`, `4+ Stars`, `5 Stars`).
    * Sort dropdown (`Newest First`, `Oldest First`, `Highest Rated`, `Highest Aesthetic Score`).
  * **Grid Zoom Slider**:
    * 3 presets: `Compact` (grid-template-columns: repeat(auto-fill, minmax(160px, 1fr))), `Medium` (240px), `Large` (340px).
  * **Multi-Select Toggle**: Enables selection checkboxes on all cards for batch actions.
* **Interactive Image Card**:
  * Top-left: Interactive Favorite Heart icon (`❤️` / `🤍`).
  * Top-right: 5-star interactive rating overlay.
  * Bottom overlay:
    * Aesthetic score badge (e.g. `8.7` with green/amber/blue gradient).
    * Parameter chips (`Seed: 4921`, `CFG: 7.0`, `Euler a`).
    * 2-line prompt preview with 1-click copy button.
* **Enhanced Lightbox Modal**:
  * Full resolution image display with zoom controls.
  * Detailed Parameters Table: Prompt, Negative Prompt, Seed, Sampler, Steps, CFG, Model, Workflow ID, Created Date.
  * **Workflow Dispatch Actions**:
    * 📝 *Use in Prompt Editor*
    * ✨ *Send to Krea 2 Studio*
    * 🎨 *Send to Anima Studio*
    * ⚡ *Re-queue in ComfyUI*
    * 👁️ *Send to Vision Inspector*
    * 📚 *Index to RAG Knowledge*
    * 🔍 *Find Similar Renders* (opens inline carousel of semantically related generations)
* **Side-by-Side (A/B) Comparison Modal**:
  * Enabled when exactly 2 images are selected.
  * Shows both images side-by-side with a synchronized metadata difference table comparing parameter variations.

---

## 5. Error Handling & Resilience

1. **Embedding Resilience**: Thread-pool execution with MD5 pseudo-vector fallback prevents crashes on offline or test environments.
2. **Database Integrity**: Automatic rollback on SQLAlchemy session errors; cascade handling for deleted prompts.
3. **Optimistic UI**: Rating and favorite toggles update state immediately in React, rolling back only if the API rejects the change.
4. **ComfyUI Connectivity**: Clear error states and local image cache serving if ComfyUI is offline.

---

## 6. Verification Plan

### 6.1 Automated Tests
* `pytest backend/tests/test_unified_rag_service.py`: Verify embedding generation, document indexing, vector cosine retrieval, tag filtering, and fallback behavior.
* `pytest backend/tests/test_cross_tab_rag.py`: Verify Krea 2 and Anima endpoints with `use_rag=True`.
* `pytest backend/tests/test_gallery_api.py`: Verify gallery search, filters, favorite/rating updates, batch delete, batch RAG indexing, and similar image retrieval.
* `npm run build` in `frontend/`: Verify zero TypeScript errors and successful bundle creation.

### 6.2 Manual & UI Verification
* Test RAG document CRUD and persistence across backend reloads.
* Test Krea 2 & Anima "Use RAG Guidelines" toggle.
* Test Semantic Tag Discovery in Tags View.
* Test Gallery search, filtering, favorites, rating, zoom slider, A/B comparison modal, and 1-click workflow dispatches.
