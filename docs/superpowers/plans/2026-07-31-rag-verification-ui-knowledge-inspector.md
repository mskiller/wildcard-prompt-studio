# RAG System Verification, Knowledge Indexing & UI Inspector Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Verify existing pgvector RAG implementation, connect RAG to `Krea2OptimizerService`, and build a dedicated **RAG Knowledge Inspector UI** for indexing, searching, and previewing retrieved vector contexts in real-time.

**Architecture:** An extended RAG service (`async_rag.py` & `rag_engine.py`), FastAPI endpoints for RAG vector search & knowledge document indexing (`/api/v1/ai/rag/search` and `/api/v1/ai/rag/index`), RAG context injection in `Krea2Optimizer`, and a new React UI component (`RAGKnowledgeInspector.tsx`).

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy (`pgvector`), Pytest, React 18, TypeScript.

---

## File Structure & Responsibilities

### Backend Files:
- `backend/app/services/async_rag.py`: Non-blocking vector embedding & similarity search engine.
- `backend/app/services/krea2_optimizer.py`: Updated to accept RAG vector context for natural language prompt expansion.
- `backend/app/api/routers/ai.py`: Expose `/api/v1/ai/rag/search` and `/api/v1/ai/rag/index` endpoints.
- `backend/tests/test_ai_rag.py`: Unit tests for vector search and indexing.

### Frontend Files:
- `frontend/src/components/editor/RAGKnowledgeInspector.tsx`: Interactive RAG inspection panel with vector similarity search preview and custom knowledge indexing.
- `frontend/src/components/editor/RAGKnowledgeInspector.css`: Styling for similarity score badges, document lists, and search results.
- `frontend/src/api.ts`: Client endpoints for `searchRAGKnowledge` and `indexRAGKnowledge`.

---

## Tasks

### Task 1: RAG Backend Verification & Indexing API Endpoints

**Files:**
- Modify: `backend/app/api/routers/ai.py`
- Modify: `backend/app/services/krea2_optimizer.py`
- Test: `backend/tests/test_ai_rag.py`

- [ ] **Step 1: Write failing unit test for RAG search and indexing**

```python
import pytest

def test_rag_knowledge_search():
    from app.services.async_rag import async_rag_engine
    res = async_rag_engine.search_knowledge_mock("cyberpunk neon lighting", top_k=2)
    assert len(res) > 0
    assert "score" in res[0]
```

- [ ] **Step 2: Add RAG context injection into `Krea2Optimizer.improve_prompt`**
- [ ] **Step 3: Create `/api/v1/ai/rag/search` and `/api/v1/ai/rag/index` FastAPI endpoints**
- [ ] **Step 4: Run backend unit tests**

---

### Task 2: UI RAG Knowledge Inspector Panel (`RAGKnowledgeInspector.tsx`)

**Files:**
- Create: `frontend/src/components/editor/RAGKnowledgeInspector.tsx`
- Create: `frontend/src/components/editor/RAGKnowledgeInspector.css`
- Modify: `frontend/src/api.ts`

- [ ] **Step 1: Add RAG API client functions in `frontend/src/api.ts`**
- [ ] **Step 2: Build `RAGKnowledgeInspector.tsx` component**
  - Vector similarity search bar with real-time score % matching.
  - Custom style guide / knowledge text indexer.
  - Retained context preview panel showing how retrieved vector snippets modify prompt outputs.

---

### Task 3: Navigation Integration & End-to-End Verification

**Files:**
- Modify: `frontend/src/store/useAppStore.ts`
- Modify: `frontend/src/components/layout/Sidebar.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Add `'rag'` view tab with `Database` icon in Sidebar and App router**
- [ ] **Step 2: Verify RAG vector search and knowledge indexing in browser UI**

---
