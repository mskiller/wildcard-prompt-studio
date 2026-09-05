# Conversational Prompt Chat, RAG Inspector & ComfyUI Live Stream Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement interactive Conversational Prompt Chat, complete RAG Inspector & CRUD management, and real-time ComfyUI Live WebSocket Stream in Wildcard Prompt Studio.

**Architecture:** 
- FastApi endpoints for `/api/v1/ai/chat-refine` and `/api/v1/ai/rag/*` CRUD & status search.
- Fix bug in `AsyncRAGEngine` (`async_rag.py`) so `_knowledge_store` initializes properly.
- FastAPI WebSocket proxy to ComfyUI native WS (`/api/v1/comfyui/ws/{client_id}`) forwarding progress, execution state, and live image frames.
- React frontend components: `PromptChatDrawer.tsx`, `RAGKnowledgeInspector.tsx`, and updated `ComfyUILiveStream.tsx`.

**Tech Stack:** Python (FastAPI, asyncio, websockets, pytest), TypeScript (React, Zustand, CSS glassmorphism).

---

### Task 1: Fix RAG Engine Initialization & Add RAG Management Endpoints

**Files:**
- Modify: `backend/app/services/async_rag.py`
- Modify: `backend/app/api/routers/ai.py`
- Test: `backend/tests/test_rag.py`

- [ ] **Step 1: Write failing unit tests for AsyncRAGEngine**

Create `backend/tests/test_rag.py`:
```python
import pytest
from app.services.async_rag import AsyncRAGEngine

@pytest.mark.asyncio
async def test_rag_initialization_and_search():
    rag = AsyncRAGEngine()
    assert hasattr(rag, "_knowledge_store")
    assert len(rag._knowledge_store) >= 3

    results = await rag.search_knowledge_async("cyberpunk lighting")
    assert len(results) > 0
    assert "cyberpunk" in results[0]["title"].lower()

@pytest.mark.asyncio
async def test_rag_crud_operations():
    rag = AsyncRAGEngine()
    doc = await rag.index_document_async("Test Doc", "Test content for studio", ["test"])
    assert doc["id"] is not None

    stats = await rag.get_stats_async()
    assert stats["doc_count"] >= 4

    deleted = await rag.delete_document_async(doc["id"])
    assert deleted is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_rag.py -v`  
Expected: FAIL with `AttributeError: 'AsyncRAGEngine' object has no attribute '_knowledge_store'`

- [ ] **Step 3: Fix `async_rag.py` and implement CRUD methods**

Update `backend/app/services/async_rag.py`:
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Dict, Any

class AsyncRAGEngine:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._knowledge_store = [
            {"id": 1, "title": "Cyberpunk Lighting & Optics Guide", "content": "Use neon reflections, rainy streets, volumetric fog, and anamorphic lens flare for cyberpunk aesthetic.", "tags": ["cyberpunk", "lighting"]},
            {"id": 2, "title": "Photorealistic Portrait Parameters", "content": "Specify 85mm prime lens, f/1.8 aperture, subsurface scattering, skin pores texture, and Rembrandt lighting.", "tags": ["portrait", "photography"]},
            {"id": 3, "title": "Fantasy Environment Styling", "content": "Incorporate misty mountains, ancient runes, bioluminescent flora, and epic scale atmospheric fog.", "tags": ["fantasy", "landscape"]}
        ]

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except Exception:
                self._model = "MOCK"
        return self._model

    def _compute_sync(self, text: str) -> List[float]:
        model = self._get_model()
        if model == "MOCK":
            import hashlib, random
            seed = int(hashlib.md5(text.encode('utf-8')).hexdigest(), 16)
            rng = random.Random(seed)
            return [rng.uniform(-1.0, 1.0) for _ in range(384)]
        else:
            vec = model.encode(text)
            return vec.tolist()

    async def compute_embedding_async(self, text: str) -> List[float]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, self._compute_sync, text)

    async def search_knowledge_async(self, query: str, top_k: int = 5) -> List[dict]:
        query_words = set(query.lower().split())
        results = []
        for doc in self._knowledge_store:
            doc_words = set(doc["content"].lower().split())
            intersection = query_words.intersection(doc_words)
            score = round(min(98.5, max(45.0, (len(intersection) + 1) * 22.5)), 1)
            results.append({
                "id": doc["id"],
                "title": doc["title"],
                "content": doc["content"],
                "tags": doc.get("tags", []),
                "similarity_score": score
            })
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:top_k]

    async def index_document_async(self, title: str, content: str, tags: List[str] = None) -> dict:
        new_id = max([d["id"] for d in self._knowledge_store], default=0) + 1
        doc = {
            "id": new_id,
            "title": title,
            "content": content,
            "tags": tags or []
        }
        self._knowledge_store.append(doc)
        return doc

    async def delete_document_async(self, doc_id: int) -> bool:
        initial_len = len(self._knowledge_store)
        self._knowledge_store = [d for d in self._knowledge_store if d["id"] != doc_id]
        return len(self._knowledge_store) < initial_len

    async def get_documents_async(self, query: Optional[str] = None, tag: Optional[str] = None) -> List[dict]:
        docs = self._knowledge_store
        if tag:
            docs = [d for d in docs if tag.lower() in [t.lower() for t in d.get("tags", [])]]
        if query:
            q = query.lower()
            docs = [d for d in docs if q in d["title"].lower() or q in d["content"].lower()]
        return docs

    async def get_stats_async(self) -> Dict[str, Any]:
        return {
            "status": "active",
            "doc_count": len(self._knowledge_store),
            "vector_dim": 384,
            "model_name": self.model_name
        }

async_rag_engine = AsyncRAGEngine()
```

- [ ] **Step 4: Update RAG endpoints in `backend/app/api/routers/ai.py`**

Add stats, list, and delete endpoints to `ai.py`:
```python
@router.get("/rag/stats")
async def rag_stats_endpoint():
    return await async_rag_engine.get_stats_async()

@router.get("/rag/documents")
async def rag_list_documents_endpoint(query: Optional[str] = None, tag: Optional[str] = None):
    docs = await async_rag_engine.get_documents_async(query=query, tag=tag)
    return {"documents": docs, "count": len(docs)}

@router.delete("/rag/documents/{doc_id}")
async def rag_delete_document_endpoint(doc_id: int):
    success = await async_rag_engine.delete_document_async(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "deleted", "doc_id": doc_id}
```

- [ ] **Step 5: Run tests to verify pass**

Run: `pytest backend/tests/test_rag.py -v`  
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/async_rag.py backend/app/api/routers/ai.py backend/tests/test_rag.py
git commit -m "fix(rag): initialize knowledge store and add stats, list, and delete endpoints"
```

---

### Task 2: Build RAG Management & Inspection Frontend Panel

**Files:**
- Modify: `frontend/src/components/editor/RAGKnowledgeInspector.tsx`
- Modify: `frontend/src/components/editor/RAGKnowledgeInspector.css`
- Modify: `frontend/src/api.ts`

- [ ] **Step 1: Add RAG API methods to `frontend/src/api.ts`**

```typescript
export const getRAGStats = async () => {
  const res = await fetch('/api/v1/ai/rag/stats');
  return res.json();
};

export const getRAGDocuments = async (query?: string, tag?: string) => {
  const params = new URLSearchParams();
  if (query) params.append('query', query);
  if (tag) params.append('tag', tag);
  const res = await fetch(`/api/v1/ai/rag/documents?${params.toString()}`);
  return res.json();
};

export const deleteRAGDocument = async (docId: number) => {
  const res = await fetch(`/api/v1/ai/rag/documents/${docId}`, { method: 'DELETE' });
  return res.json();
};

export const indexRAGDocument = async (title: string, content: string, tags: string[]) => {
  const res = await fetch('/api/v1/ai/rag/index', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, content, tags })
  });
  return res.json();
};

export const searchRAGKnowledge = async (query: string, topK: number = 5) => {
  const res = await fetch('/api/v1/ai/rag/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, top_k: topK })
  });
  return res.json();
};
```

- [ ] **Step 2: Update `RAGKnowledgeInspector.tsx` UI**

Implement status header, search bar, document cards with delete action, index form, and search sandbox in `RAGKnowledgeInspector.tsx`.

- [ ] **Step 3: Update `RAGKnowledgeInspector.css`**

Add CSS styling for status badge, search inputs, tags, document card layout, and similarity percentage progress bars.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/api.ts frontend/src/components/editor/RAGKnowledgeInspector.tsx frontend/src/components/editor/RAGKnowledgeInspector.css
git commit -m "feat(rag): enhance RAG Knowledge Inspector UI with doc browsing, deletion, and query testing"
```

---

### Task 3: Backend Conversational Prompt Refinement Chat API

**Files:**
- Modify: `backend/app/api/routers/ai.py`
- Create: `backend/app/services/prompt_chat_service.py`
- Test: `backend/tests/test_prompt_chat.py`

- [ ] **Step 1: Write failing unit test for PromptChatService**

Create `backend/tests/test_prompt_chat.py`:
```python
import pytest
from app.services.prompt_chat_service import prompt_chat_service

@pytest.mark.asyncio
async def test_chat_refinement():
    result = await prompt_chat_service.refine_prompt_chat(
        current_prompt="a portrait of a cyberpunk hacker in rain",
        user_message="add glowing neon signs and make colors teal and gold",
        chat_history=[]
    )
    assert "updated_prompt" in result
    assert "explanation" in result
    assert "glowing neon" in result["updated_prompt"].lower() or "neon" in result["updated_prompt"].lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_prompt_chat.py -v`  
Expected: FAIL with module/class missing.

- [ ] **Step 3: Implement `prompt_chat_service.py`**

Create `backend/app/services/prompt_chat_service.py` with parsing logic and LLM provider integration.

- [ ] **Step 4: Add `/api/v1/ai/chat-refine` endpoint in `backend/app/api/routers/ai.py`**

```python
class ChatRefineRequest(BaseModel):
    current_prompt: str
    user_message: str
    chat_history: Optional[List[Dict[str, str]]] = []
    provider: Optional[str] = "auto"
    target_model: Optional[str] = "krea2"
    use_rag: Optional[bool] = True

@router.post("/chat-refine")
async def chat_refine_endpoint(req: ChatRefineRequest):
    return await prompt_chat_service.refine_prompt_chat(
        current_prompt=req.current_prompt,
        user_message=req.user_message,
        chat_history=req.chat_history,
        provider=req.provider,
        target_model=req.target_model,
        use_rag=req.use_rag
    )
```

- [ ] **Step 5: Run unit tests**

Run: `pytest backend/tests/test_prompt_chat.py -v`  
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/prompt_chat_service.py backend/app/api/routers/ai.py backend/tests/test_prompt_chat.py
git commit -m "feat(ai): add prompt chat refinement endpoint and service"
```

---

### Task 4: Frontend Prompt Chat Drawer UI

**Files:**
- Create: `frontend/src/components/editor/PromptChatDrawer.tsx`
- Create: `frontend/src/components/editor/PromptChatDrawer.css`
- Modify: `frontend/src/components/editor/PromptEditor.tsx` or `frontend/src/App.tsx`

- [ ] **Step 1: Create `PromptChatDrawer.tsx`**

Build message history list, live prompt diff view (additions/deletions), action chips (`+ Add Cinematic Lighting`, `- Remove Rain`), and **Apply to Editor** callback.

- [ ] **Step 2: Create `PromptChatDrawer.css`**

Style chat bubbles, prompt diff containers, chip buttons, and input box using dark mode glassmorphism aesthetics.

- [ ] **Step 3: Integrate Chat Drawer into main editor layout**

Mount `PromptChatDrawer` in `PromptEditor.tsx` / `App.tsx` with toggle button in header.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/editor/PromptChatDrawer.tsx frontend/src/components/editor/PromptChatDrawer.css frontend/src/components/editor/PromptEditor.tsx
git commit -m "feat(ui): add Conversational Prompt Refinement Chat Drawer to editor"
```

---

### Task 5: ComfyUI Real-Time WebSocket Proxy Bridge

**Files:**
- Modify: `backend/app/services/comfyui_ws.py`
- Modify: `backend/app/services/comfyui_connector.py`
- Modify: `backend/app/api/routers/comfyui.py`
- Test: `backend/tests/test_comfyui_ws.py`

- [ ] **Step 1: Write unit test for ComfyUI WS manager**

Create `backend/tests/test_comfyui_ws.py` testing connection handling and message broadcasting.

- [ ] **Step 2: Implement WebSocket proxy in `comfyui_ws.py` and `comfyui.py`**

Connect backend socket to `ws://<comfyui_host>/ws?clientId=<client_id>` and pipe JSON events (`status`, `executing`, `progress`, `executed`) to connected frontend websocket clients.

- [ ] **Step 3: Run pytest**

Run: `pytest backend/tests/test_comfyui_ws.py -v`  
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/comfyui_ws.py backend/app/services/comfyui_connector.py backend/app/api/routers/comfyui.py backend/tests/test_comfyui_ws.py
git commit -m "fix(comfyui): implement real-time websocket proxy bridge for ComfyUI live stream"
```

---

### Task 6: Connect ComfyUI Live Stream UI Component

**Files:**
- Modify: `frontend/src/components/editor/ComfyUILiveStream.tsx`
- Modify: `frontend/src/components/editor/ComfyUILiveStream.css`

- [ ] **Step 1: Update `ComfyUILiveStream.tsx`**

Subscribe to WebSocket endpoint `/api/v1/comfyui/ws/{client_id}`.  
Update `currentStep`, `totalSteps`, `progress`, active node ID (`executing`), and render real-time preview images on frame arrival.

- [ ] **Step 2: Update `ComfyUILiveStream.css`**

Add animations for active execution node badge and progress bar pulse.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/editor/ComfyUILiveStream.tsx frontend/src/components/editor/ComfyUILiveStream.css
git commit -m "feat(comfyui): hook ComfyUILiveStream component to real-time websocket feed"
```

---

### Task 7: Full System Verification

- [ ] **Step 1: Run pytest suite**

Run: `pytest backend/tests -v`  
Expected: All backend unit tests pass cleanly.

- [ ] **Step 2: Build & verify frontend typescript compilation**

Run command in `frontend`: `npm run build` or `npx tsc --noEmit`  
Expected: Zero compilation errors.

- [ ] **Step 3: Commit final release verification**

```bash
git add .
git commit -m "chore(release): v1.2.0 - conversational prompt chat, RAG inspector, and comfyui live stream"
```
