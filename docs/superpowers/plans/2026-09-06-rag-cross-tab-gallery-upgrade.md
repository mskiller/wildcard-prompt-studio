# RAG System Enhancement, Cross-Tab Integration & Gallery Studio Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Unify the RAG system into a persistent 384-dimensional pgvector backend, integrate RAG intelligence across all studio tabs (Editor, Krea 2, Anima, Tags, Vision), and completely overhaul the Gallery into a modern, searchable, filterable visual studio with A/B comparison and 1-click workflow dispatches.

**Architecture:** A unified PostgreSQL `pgvector` service (`UnifiedRAGService`) runs non-blocking embeddings via `all-MiniLM-L6-v2` in thread pools with offline mock fallbacks, indexing domain knowledge and prompts. Studio tabs consume RAG context for prompt optimization and tag discovery. The Gallery data layer is upgraded with favorites, star ratings, aesthetic scores, and batch operations, exposed through a responsive glassmorphic UI.

**Tech Stack:** Python 3.11/FastAPI, SQLAlchemy, Alembic, PostgreSQL + pgvector, sentence-transformers, React 18, TypeScript, Vite, Lucide icons, CSS glassmorphism.

---

## File Structure & Responsibilities

### Backend
* `backend/app/models/knowledge.py`: Defines `KnowledgeDocument` model with 384-dim vector, categories, and tags.
* `backend/app/models/image.py`: Updates `Image` model with `is_favorite`, `rating`, and `aesthetic_score`.
* `backend/alembic/versions/20260906_rag_gallery_upgrade.py`: Alembic migration aligning vectors to 384-dim and adding image metadata columns.
* `backend/app/services/unified_rag.py`: Database-backed RAG service providing embedding generation, pgvector cosine search, hybrid keyword filtering, and default knowledge seeding.
* `backend/app/api/routers/ai.py`: Updated endpoints for `/rag/search`, `/rag/index`, `/rag/documents`, `/krea2-improve`, `/anima-improve`.
* `backend/app/services/krea2_optimizer.py`: Incorporates RAG knowledge into Krea 2 system prompts.
* `backend/app/services/anima_optimizer.py`: Incorporates RAG anime rules into Anima system prompts.
* `backend/app/api/routers/images.py`: Upgraded Gallery endpoints with search, filters, favorites, ratings, batch delete/index, and similar image queries.

### Frontend
* `frontend/src/api.ts`: API client functions for enhanced Gallery operations, RAG options, and semantic tag discovery.
* `frontend/src/components/editor/Krea2StudioPanel.tsx`: Adds "Use RAG Guidelines" toggle.
* `frontend/src/components/editor/AnimaStudioPanel.tsx`: Adds "Use RAG Guidelines" toggle.
* `frontend/src/components/editor/TagsView.tsx`: Adds "Semantic Tag Discovery" input.
* `frontend/src/components/editor/VisionInspectorPanel.tsx`: Adds editable Title/Category/Tags when saving styles to RAG.
* `frontend/src/components/gallery/GalleryView.tsx`: Complete overhaul with search, filters, zoom slider, multi-select, batch actions, A/B compare modal, and workflow roundtrips.
* `frontend/src/components/gallery/GalleryView.css`: Glassmorphic styling for new Gallery components.

---

### Task 1: Database Models & Alembic Migration for 384-dim Vectors & Image Metadata

**Files:**
* Modify: `backend/app/models/knowledge.py`
* Modify: `backend/app/models/image.py`
* Create: `backend/alembic/versions/20260906_rag_gallery_upgrade.py`
* Create: `backend/tests/test_database_models.py`

- [ ] **Step 1: Write failing model unit test**

```python
# backend/tests/test_database_models.py
import pytest
from app.models.knowledge import KnowledgeDocument
from app.models.image import Image

def test_knowledge_document_model_attributes():
    doc = KnowledgeDocument(
        title="Test Doc",
        content="Test Content",
        category="optics",
        tags='["lighting", "cyberpunk"]',
        embedding=[0.1] * 384
    )
    assert doc.title == "Test Doc"
    assert doc.category == "optics"
    assert len(doc.embedding) == 384

def test_image_model_attributes():
    img = Image(
        filename="test_render.png",
        is_favorite=True,
        rating=5,
        aesthetic_score=8.7
    )
    assert img.is_favorite is True
    assert img.rating == 5
    assert img.aesthetic_score == 8.7
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_database_models.py -v`
Expected: FAIL due to missing `category` or `is_favorite` attributes on models.

- [ ] **Step 3: Update `KnowledgeDocument` and `Image` models**

In `backend/app/models/knowledge.py`:
```python
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.database import Base

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=False)
    category = Column(String, default="general", index=True)
    tags = Column(Text, default="[]")  # Stored as JSON string or comma-separated
    embedding = Column(Vector(384), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

In `backend/app/models/image.py`:
```python
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, BigInteger, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, nullable=False)
    prompt_id = Column(Integer, ForeignKey("prompts.id", ondelete="SET NULL"), nullable=True)
    
    seed = Column(BigInteger, nullable=True)
    cfg_scale = Column(Float, nullable=True)
    steps = Column(Integer, nullable=True)
    sampler_name = Column(String, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    comfy_workflow_id = Column(String, nullable=True)
    
    is_favorite = Column(Boolean, default=False, index=True)
    rating = Column(Integer, default=0, index=True)
    aesthetic_score = Column(Float, nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    prompt = relationship("Prompt", back_populates="images")
```

- [ ] **Step 4: Create migration script**

Create `backend/alembic/versions/20260906_rag_gallery_upgrade.py` adding columns `is_favorite`, `rating`, `aesthetic_score` to `images`, and altering `knowledge_documents.embedding` to `VECTOR(384)`.

- [ ] **Step 5: Run tests and verify they pass**

Run: `pytest backend/tests/test_database_models.py -v`
Expected: PASS

- [ ] **Step 6: Commit changes**

```bash
git add backend/app/models/ backend/alembic/versions/ backend/tests/test_database_models.py
git commit -m "feat(db): update models with 384-dim vector and gallery metadata"
```

---

### Task 2: Persistent Unified RAG Service & Pre-Seeded Knowledge

**Files:**
* Create: `backend/app/services/unified_rag.py`
* Modify: `backend/app/api/routers/ai.py`
* Create: `backend/tests/test_unified_rag_service.py`

- [ ] **Step 1: Write failing test for UnifiedRAGService**

```python
# backend/tests/test_unified_rag_service.py
import pytest
from app.database import SessionLocal
from app.services.unified_rag import unified_rag_service
from app.models.knowledge import KnowledgeDocument

@pytest.mark.asyncio
async def test_compute_embedding_dimensions():
    vec = await unified_rag_service.compute_embedding_async("cyberpunk rainy street")
    assert isinstance(vec, list)
    assert len(vec) == 384

@pytest.mark.asyncio
async def test_seed_and_search_knowledge():
    db = SessionLocal()
    try:
        await unified_rag_service.seed_default_knowledge_if_empty(db)
        docs = db.query(KnowledgeDocument).all()
        assert len(docs) >= 3

        results = await unified_rag_service.search_knowledge_async(db, "optics 85mm lens portrait", top_k=2)
        assert len(results) > 0
        assert "similarity_score" in results[0]
    finally:
        db.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_unified_rag_service.py -v`
Expected: FAIL due to missing `unified_rag_service`.

- [ ] **Step 3: Implement `UnifiedRAGService`**

Create `backend/app/services/unified_rag.py`:
* Asynchronous embedding generation with ThreadPoolExecutor and SentenceTransformer with fallback.
* `seed_default_knowledge_if_empty(db)`: Seeds Krea 2 guidelines, ANIMA anime rules, photorealism camera descriptors, negative prompt heuristics.
* `search_knowledge_async(db, query, top_k, category, tag)`: Queries `KnowledgeDocument` using `embedding.cosine_distance(query_vec)` and text ILIKE fallback, calculating normalized similarity score (`0.0` to `1.0`).
* `index_document_async(db, title, content, category, tags)`: Embeds content and inserts `KnowledgeDocument`.
* `delete_document_async(db, doc_id)`: Removes document.
* `get_documents_async(db, query, category, tag)`: Filtered listing.
* `get_stats_async(db)`: Returns total document count, categories, tags, and model name.

- [ ] **Step 4: Update `/api/v1/ai/rag/*` endpoints in `backend/app/api/routers/ai.py`**

Refactor `rag_search_endpoint`, `rag_index_endpoint`, `rag_stats_endpoint`, `rag_get_documents_endpoint`, and `rag_delete_document_endpoint` to use `unified_rag_service` with `db: Session = Depends(get_db)`.

- [ ] **Step 5: Run tests and verify they pass**

Run: `pytest backend/tests/test_unified_rag_service.py -v`
Expected: PASS

- [ ] **Step 6: Commit changes**

```bash
git add backend/app/services/unified_rag.py backend/app/api/routers/ai.py backend/tests/test_unified_rag_service.py
git commit -m "feat(rag): implement persistent UnifiedRAGService with pgvector and pre-seeded knowledge"
```

---

### Task 3: Cross-Tab RAG Integration in AI Endpoints & Studio Services

**Files:**
* Modify: `backend/app/schemas/ai.py`
* Modify: `backend/app/services/krea2_optimizer.py`
* Modify: `backend/app/services/anima_optimizer.py`
* Modify: `backend/app/api/routers/ai.py`
* Create: `backend/tests/test_cross_tab_rag.py`

- [ ] **Step 1: Write failing test for Krea 2 and Anima RAG enrichment**

```python
# backend/tests/test_cross_tab_rag.py
import pytest
from app.database import SessionLocal
from app.services.krea2_optimizer import Krea2Optimizer
from app.services.anima_optimizer import AnimaOptimizer
from app.services.unified_rag import unified_rag_service

@pytest.mark.asyncio
async def test_krea2_enrichment_with_rag():
    db = SessionLocal()
    try:
        await unified_rag_service.seed_default_knowledge_if_empty(db)
        optimizer = Krea2Optimizer()
        prompt = "a majestic dragon flying over snowy mountains"
        prompt_with_rag = await optimizer.enrich_prompt_with_rag(db, prompt)
        assert len(prompt_with_rag) > len(prompt)
    finally:
        db.close()

@pytest.mark.asyncio
async def test_anima_enrichment_with_rag():
    db = SessionLocal()
    try:
        await unified_rag_service.seed_default_knowledge_if_empty(db)
        optimizer = AnimaOptimizer()
        prompt = "1girl, solo, school uniform"
        prompt_with_rag = await optimizer.enrich_prompt_with_rag(db, prompt)
        assert len(prompt_with_rag) > len(prompt)
    finally:
        db.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_cross_tab_rag.py -v`
Expected: FAIL due to missing `enrich_prompt_with_rag`.

- [ ] **Step 3: Implement RAG enrichment in `krea2_optimizer.py` and `anima_optimizer.py`**

1. In `backend/app/schemas/ai.py`: Add `use_rag: Optional[bool] = False` to `Krea2ImproveRequest` and `AnimaImproveRequest`.
2. In `backend/app/services/krea2_optimizer.py`: Add `enrich_prompt_with_rag(db, prompt)` that fetches top matching Krea 2 / cinematic knowledge documents and prepends formatting guidance to the system prompt.
3. In `backend/app/services/anima_optimizer.py`: Add `enrich_prompt_with_rag(db, prompt)` that fetches ANIMA anime rules, danbooru tag structure, and quality score tag directives.
4. In `backend/app/api/routers/ai.py`: Update `/krea2-improve` and `/anima-improve` to pass `db` and `request.use_rag` into the optimizer calls.

- [ ] **Step 4: Run tests and verify they pass**

Run: `pytest backend/tests/test_cross_tab_rag.py -v`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add backend/app/schemas/ai.py backend/app/services/krea2_optimizer.py backend/app/services/anima_optimizer.py backend/app/api/routers/ai.py backend/tests/test_cross_tab_rag.py
git commit -m "feat(ai): integrate RAG domain knowledge into Krea 2 and Anima optimizers"
```

---

### Task 4: Gallery Backend Endpoints (Filtering, Rating, Aesthetic Scoring, Batch Actions, Similar Renders)

**Files:**
* Modify: `backend/app/schemas/image.py`
* Modify: `backend/app/api/routers/images.py`
* Create: `backend/tests/test_gallery_api.py`

- [ ] **Step 1: Write failing tests for Gallery API endpoints**

```python
# backend/tests/test_gallery_api.py
import pytest
from fastapi.testclient import TestClient
from main import app
from app.database import SessionLocal
from app.models.image import Image
from app.models.prompt import Prompt

client = TestClient(app)

def test_gallery_search_and_favorite():
    db = SessionLocal()
    try:
        p = Prompt(name="Neon City", content="neon cyberpunk city in rain")
        db.add(p)
        db.commit()
        db.refresh(p)

        img = Image(filename="test_gallery_1.png", prompt_id=p.id, seed=1234, is_favorite=False, rating=0)
        db.add(img)
        db.commit()
        db.refresh(img)

        # 1. Toggle favorite
        res = client.patch(f"/api/v1/images/{img.id}/favorite")
        assert res.status_code == 200
        assert res.json()["is_favorite"] is True

        # 2. Update rating
        res = client.patch(f"/api/v1/images/{img.id}/rating", json={"rating": 5})
        assert res.status_code == 200
        assert res.json()["rating"] == 5

        # 3. Filter by favorites
        res = client.get("/api/v1/images/gallery?is_favorite=true")
        assert res.status_code == 200
        items = res.json()
        assert any(i["id"] == img.id for i in items)

        # 4. Search prompt keyword
        res = client.get("/api/v1/images/gallery?search=cyberpunk")
        assert res.status_code == 200
        assert len(res.json()) >= 1
    finally:
        db.query(Image).filter(Image.filename == "test_gallery_1.png").delete()
        db.query(Prompt).filter(Prompt.name == "Neon City").delete()
        db.commit()
        db.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_gallery_api.py -v`
Expected: FAIL due to missing routes or parameters.

- [ ] **Step 3: Update `backend/app/schemas/image.py`**

Add `is_favorite`, `rating`, `aesthetic_score` to `ImageResponse`, `ImageCreate`, and `ImageUpdate`. Create `RatingUpdateRequest(BaseModel)` and `BatchActionRequest(BaseModel)`.

- [ ] **Step 4: Implement new endpoints in `backend/app/api/routers/images.py`**

* Update `GET /gallery`: Add query parameters `search`, `sampler`, `is_favorite`, `min_rating`, `sort_by` (`newest`, `oldest`, `rating`, `aesthetic_score`), `skip`, `limit`.
* Add `PATCH /{image_id}/favorite`: Toggles boolean `is_favorite`.
* Add `PATCH /{image_id}/rating`: Validates and updates `rating` (0–5).
* Add `POST /{image_id}/score-aesthetic`: Calls `score_aesthetic_prompt(img.prompt_content)` and sets `img.aesthetic_score`.
* Add `POST /batch/delete`: Deletes multiple images and static files.
* Add `POST /batch/index-rag`: Indexes selected image prompts into `KnowledgeDocument` via `unified_rag_service`.
* Add `GET /{image_id}/similar`: Computes cosine distance against other prompts to return related images.

- [ ] **Step 5: Run tests and verify they pass**

Run: `pytest backend/tests/test_gallery_api.py -v`
Expected: PASS

- [ ] **Step 6: Commit changes**

```bash
git add backend/app/schemas/image.py backend/app/api/routers/images.py backend/tests/test_gallery_api.py
git commit -m "feat(gallery): add search, filtering, ratings, favorites, batch actions, and similar image lookup"
```

---

### Task 5: Frontend API Client & State Management

**Files:**
* Modify: `frontend/src/api.ts`

- [ ] **Step 1: Add new Gallery and RAG interfaces and functions in `frontend/src/api.ts`**

* Update `Krea2Options` and `AnimaOptions` to include `use_rag?: boolean`.
* Add `GalleryQueryParams`:
  ```typescript
  export interface GalleryQueryParams {
    skip?: number;
    limit?: number;
    search?: string;
    sampler?: string;
    is_favorite?: boolean;
    min_rating?: number;
    sort_by?: 'newest' | 'oldest' | 'rating' | 'aesthetic_score';
  }
  ```
* Add API methods:
  * `getGalleryImages(params?: GalleryQueryParams): Promise<any[]>`
  * `toggleImageFavorite(id: number): Promise<any>`
  * `setImageRating(id: number, rating: number): Promise<any>`
  * `scoreImageAesthetic(id: number): Promise<any>`
  * `batchDeleteImages(imageIds: number[]): Promise<{ deleted_count: number }>`
  * `batchIndexImagesToRAG(imageIds: number[], category?: string): Promise<{ indexed_count: number }>`
  * `getSimilarImages(id: number, topK?: number): Promise<any[]>`
  * `searchTagsSemantic(query: string, limit?: number): Promise<any[]>`

- [ ] **Step 2: Verify TypeScript compilation**

Run: `cd frontend && npx tsc --noEmit`
Expected: PASS with 0 errors.

- [ ] **Step 3: Commit changes**

```bash
git add frontend/src/api.ts
git commit -m "feat(api): update frontend API client with gallery filters, batch actions, and cross-tab RAG methods"
```

---

### Task 6: Cross-Tab RAG Frontend UI (Krea 2, Anima, Tags View, Vision Inspector)

**Files:**
* Modify: `frontend/src/components/editor/Krea2StudioPanel.tsx` & `.css`
* Modify: `frontend/src/components/editor/AnimaStudioPanel.tsx` & `.css`
* Modify: `frontend/src/components/editor/TagsView.tsx` & `.css`
* Modify: `frontend/src/components/editor/VisionInspectorPanel.tsx`

- [ ] **Step 1: Add RAG Guidelines toggle to Krea 2 Studio**

In `Krea2StudioPanel.tsx`:
* Add state `const [useRAG, setUseRAG] = useState<boolean>(true);`
* In `handleKrea2Expand()`, pass `use_rag: useRAG` to `krea2ImprovePrompt()`.
* Add a styled switch/checkbox: `📚 Use RAG Optics & Guidelines` with active pill badge.

- [ ] **Step 2: Add RAG Guidelines toggle to Anima Studio**

In `AnimaStudioPanel.tsx`:
* Add state `const [useRAG, setUseRAG] = useState<boolean>(true);`
* In `handleAnimaImprove()`, pass `use_rag: useRAG` to `animaImprovePrompt()`.
* Add a styled switch/checkbox: `📚 Use RAG Anime Tag Rules` with active pill badge.

- [ ] **Step 3: Add Semantic Tag Discovery to Tags View**

In `TagsView.tsx`:
* Add state for `semanticQuery`, `semanticResults`, and `isSearchingSemantic`.
* Add a search header banner above tags: "Discover Tags via Semantic Concept" with an input field and "Search RAG Vectors" button.
* When results return, display interactive tag chips with 1-click "Insert into Active Prompt" and "Copy Tag".

- [ ] **Step 4: Enhance Vision Inspector RAG Style Save Modal**

In `VisionInspectorPanel.tsx`:
* Provide editable modal/inputs for Title, Category (`optics`, `lighting`, `palette`), and Tags when clicking "Save to RAG Knowledge Base".

- [ ] **Step 5: Verify TypeScript compilation**

Run: `cd frontend && npx tsc --noEmit`
Expected: PASS with 0 errors.

- [ ] **Step 6: Commit changes**

```bash
git add frontend/src/components/editor/Krea2StudioPanel.tsx frontend/src/components/editor/AnimaStudioPanel.tsx frontend/src/components/editor/TagsView.tsx frontend/src/components/editor/VisionInspectorPanel.tsx
git commit -m "feat(ui): add cross-tab RAG controls to Krea 2, Anima, Tags, and Vision panels"
```

---

### Task 7: Gallery Studio Complete Overhaul (Toolbar, Cards, Lightbox, A/B Compare)

**Files:**
* Modify: `frontend/src/components/gallery/GalleryView.tsx`
* Modify: `frontend/src/components/gallery/GalleryView.css`

- [ ] **Step 1: Implement Glassmorphic Toolbar**

In `GalleryView.tsx`:
* Search input (debounced prompt & filename search).
* Filter buttons: "Favorites Only" toggle (`Heart` icon), Sampler dropdown, Min-Rating selector (1–5 stars).
* Sort dropdown: `Newest First`, `Oldest First`, `Highest Rated`, `Highest Aesthetic Score`.
* Thumbnail Zoom Slider: Controls CSS grid minmax between `160px` (Compact), `240px` (Medium), `340px` (Large).
* Multi-select Mode toggle: Enables batch checkboxes.
* Batch Action Bar: Displays when 1+ items are selected: "Delete Selected ({n})", "Index to RAG ({n})", "Compare A/B" (active when exactly 2 selected).

- [ ] **Step 2: Implement Interactive Image Cards**

* Top bar on card: Clickable Favorite Heart icon (`❤️` / `🤍`) calling `toggleImageFavorite`, and 5-star rating stars calling `setImageRating`.
* Bottom bar on card: Aesthetic score badge (with dynamic color code: green for >= 8.0, blue for 6.5–7.9, gray otherwise), Seed/Sampler chips, and 2-line prompt text with 1-click copy button.

- [ ] **Step 3: Implement Comprehensive Lightbox Modal**

* Full-resolution image preview with fit/zoom toggle.
* Metadata table: Prompt, Negative Prompt, Seed, Steps, CFG, Sampler, Model, Workflow ID, Aesthetic score.
* 1-Click Workflow Roundtrip Buttons:
  * 📝 *Use in Prompt Editor*
  * ✨ *Send to Krea 2 Studio*
  * 🎨 *Send to Anima Studio*
  * ⚡ *Re-queue in ComfyUI*
  * 👁️ *Send to Vision Inspector*
  * 📚 *Index to RAG Knowledge*
  * 🔍 *Find Similar Generations* (triggers inline similarity carousel)

- [ ] **Step 4: Implement Side-by-Side (A/B) Compare Modal**

* When 2 images are selected in multi-select mode and the user clicks "Compare A/B":
* Opens a dual split-view modal displaying Image A and Image B side-by-side with synchronized zoom.
* Displays a diff comparison table below: Prompt differences, Seed A vs B, CFG A vs B, Sampler A vs B, Steps A vs B, and Aesthetic Scores.

- [ ] **Step 5: Verify TypeScript compilation and CSS styling**

Run: `cd frontend && npx tsc --noEmit`
Expected: PASS with 0 errors.

- [ ] **Step 6: Commit changes**

```bash
git add frontend/src/components/gallery/GalleryView.tsx frontend/src/components/gallery/GalleryView.css
git commit -m "feat(gallery): overhaul gallery studio with search, filters, zoom, lightbox actions, and A/B compare"
```

---

### Task 8: End-to-End Verification, Frontend Build & Test Suite Execution

**Files:**
* Run: Backend test suite (`pytest`)
* Run: Frontend production build (`npm run build`)

- [ ] **Step 1: Run complete backend test suite**

Run: `pytest backend/tests/ -v`
Expected: All tests PASS.

- [ ] **Step 2: Run frontend production build**

Run: `cd frontend && npm run build`
Expected: Vite build completes successfully without errors.

- [ ] **Step 3: Final commit and clean up**

```bash
git status
git commit -m "chore: complete verification for RAG persistence, cross-tab integration, and gallery studio overhaul"
```
