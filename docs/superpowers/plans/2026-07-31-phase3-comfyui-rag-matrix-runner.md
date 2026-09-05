# Phase 3: ComfyUI Live Bridge, Async Vector RAG & Batch Matrix Runner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate real-time WebSocket ComfyUI progress tracking, asynchronous non-blocking vector search RAG indexing (`pgvector`), batch matrix sweep runner, and import/export wildcard synchronization.

**Architecture:** A WebSocket proxy layer (`comfyui_ws.py`) forwarding ComfyUI progress events, an executor-offloaded background vector embedder (`async_rag.py`), a batch execution router (`generate.py`), and a matrix visual sweep panel (`WildcardMatrixPanel.tsx`).

**Tech Stack:** Python 3.11, FastAPI WebSockets, Pytest, SQLAlchemy (`pgvector`), React 18, TypeScript.

---

## File Structure & Responsibilities

### Backend Files:
- `backend/app/services/comfyui_ws.py`: WebSocket manager connecting client frontend to ComfyUI WS `/ws?clientId=...`.
- `backend/app/services/async_rag.py`: Async wrapper for `SentenceTransformer` and `pgvector` similarity search via thread-pool executor.
- `backend/app/api/routers/comfyui.py`: Endpoints for prompt dispatching, history querying, image viewing, and object info.
- `backend/app/api/routers/generate.py`: Updated with `/api/v1/generate/matrix/execute` batch dispatch.

### Frontend Files:
- `frontend/src/components/editor/WildcardMatrixPanel.tsx`: Interactive grid preview for matrix combinations and batch queue trigger.
- `frontend/src/api.ts`: API endpoints for matrix execution and ComfyUI status.

---

## Tasks

### Task 1: ComfyUI Live WebSocket Manager & API Router

**Files:**
- Create: `backend/app/services/comfyui_ws.py`
- Create: `backend/app/api/routers/comfyui.py`
- Modify: `backend/app/api/routers/__init__.py`
- Test: `backend/tests/test_comfyui_connector.py`

- [ ] **Step 1: Write unit tests for ComfyUI API endpoints**

```python
import pytest

def test_comfyui_router_imports():
    from app.api.routers.comfyui import router
    assert router.prefix == "/api/v1/comfyui"
```

- [ ] **Step 2: Implement `ComfyUIWSManager`**

Implement WebSocket client manager handling active connections and proxying execution progress (`executing`, `progress`, `execution_cached`).

- [ ] **Step 3: Create `/api/v1/comfyui` API router**

Add endpoints `/queue`, `/history/{prompt_id}`, `/image/{filename}`, and `/object_info`.

- [ ] **Step 4: Run backend tests**

---

### Task 2: Async Thread-Pool Vector RAG Indexer

**Files:**
- Create: `backend/app/services/async_rag.py`
- Test: `backend/tests/test_async_rag.py`

- [ ] **Step 1: Write failing test for async vector search**

```python
import pytest
from app.services.async_rag import AsyncRAGEngine

@pytest.mark.asyncio
async def test_async_embedding_computation():
    engine = AsyncRAGEngine()
    vec = await engine.compute_embedding_async("a beautiful cinematic landscape")
    assert isinstance(vec, list)
    assert len(vec) > 0
```

- [ ] **Step 2: Implement `AsyncRAGEngine` with `asyncio.get_running_loop().run_in_executor`**

Wrap heavy vector calculation off the main event loop.

- [ ] **Step 3: Run tests and verify PASS**

---

### Task 3: Combinatorial Matrix Batch Sweep Execution Engine

**Files:**
- Modify: `backend/app/api/routers/generate.py`
- Create: `frontend/src/components/editor/WildcardMatrixPanel.tsx`
- Test: `backend/tests/test_matrix_runner.py`

- [ ] **Step 1: Implement `/api/v1/generate/matrix/execute` endpoint**
- [ ] **Step 2: Build `WildcardMatrixPanel.tsx` component with live grid preview and batch status tracking**
- [ ] **Step 3: Add view tab in `App.tsx` and test matrix batch generation UI**

---

### Task 4: Wildcard & Prompt Export/Import Sync Engine

**Files:**
- Modify: `backend/app/services/importer.py`
- Test: `backend/tests/test_importer.py`

- [ ] **Step 1: Implement zip/txt file wildcard importer and exporter**
- [ ] **Step 2: Run all backend and frontend tests for verification**

---
