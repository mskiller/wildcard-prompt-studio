# Design Specification: Conversational Prompt Chat, RAG Inspector, & ComfyUI Live Stream

**Date:** 2026-07-31  
**Status:** Approved  
**Target Version:** Next Version (v1.2.0)

---

## 1. Executive Summary

This feature set upgrades **Wildcard Prompt Studio** with three core capabilities:
1. **Interactive Conversational Prompt Chat Drawer**: Enables users to converse directly with an LLM (KoboldCpp, Ollama, Gemini) to iteratively refine prompts, add/remove objects, modify style/lighting/color, and see live side-by-side prompt diffs with one-click editor application.
2. **Comprehensive RAG Inspector & Health System**: Fixes the underlying vector store initialization bug in `async_rag.py`, exposes full document CRUD and search sandbox APIs, and provides a visual RAG status & browsing interface.
3. **Fixed ComfyUI Live Stream & WebSocket Proxy**: Establishes a real-time WebSocket bridge to ComfyUI's native WebSocket API, streaming active node execution, step progress, latency, and live preview frames directly into the UI.

---

## 2. Component Specifications

### 2.1 Conversational Prompt Refinement Chat

#### User Story
As a prompt engineer, I want to chat with an AI assistant while viewing my prompt so I can tell it "add glowing neon signs", "remove the car", or "make color scheme teal and gold", review the resulting prompt diff, and apply it directly to my prompt editor.

#### Architecture
- **Frontend Panel (`frontend/src/components/editor/PromptChatDrawer.tsx`)**:
  - Mounted as a collapsible side-drawer adjacent to `PromptEditor.tsx`.
  - Maintains conversation history (`user` and `assistant` messages).
  - Displays prompt diff container with additions highlighted in green and deletions in red.
  - Buttons: **Apply to Editor**, **Copy Prompt**, **Revert Step**, **Index Prompt to RAG**.
  - Quick Suggestion Chips: `+ Cinematic Lighting`, `- Clean Noise`, `🎨 Cyberpunk Palette`, `⚡ Max Quality Tokens`.

- **Backend Endpoint (`POST /api/v1/ai/chat-refine`)**:
  - Request Payload:
    ```json
    {
      "current_prompt": "a portrait of a cyberpunk hacker in rain",
      "chat_history": [
        {"role": "user", "content": "add neon signs and remove rain"}
      ],
      "user_message": "add neon signs and remove rain",
      "provider": "auto",
      "target_model": "krea2",
      "use_rag": true
    }
    ```
  - Prompt Engineering logic instructs LLM to analyze the request and return JSON:
    ```json
    {
      "updated_prompt": "a portrait of a cyberpunk hacker, glowing neon signs, vibrant urban background",
      "explanation": "Added glowing neon signs and urban background elements; removed rain and wet surfaces.",
      "changes": {
        "added": ["glowing neon signs", "vibrant urban background"],
        "removed": ["rain"]
      }
    }
    ```

---

### 2.2 RAG Verification, Inspection, & Management

#### Bug Fix
- **`backend/app/services/async_rag.py`**:
  - Fix misplaced `return self._model` statement inside `_get_model()` that was preventing `self._knowledge_store` from being initialized in `__init__`.
  - Ensure fallback mock embedding logic works robustly without dependency errors.

#### API Endpoints (`backend/app/api/routers/ai.py`)
- `GET /api/v1/ai/rag/stats`: Returns store status (`status`, `doc_count`, `vector_dim`, `model_name`).
- `GET /api/v1/ai/rag/documents`: Returns list of indexed documents with optional query search & tag filter.
- `POST /api/v1/ai/rag/documents`: Adds a new document (`title`, `content`, `tags`).
- `DELETE /api/v1/ai/rag/documents/{doc_id}`: Deletes document by ID.
- `POST /api/v1/ai/rag/search`: Executes vector similarity query returning matched chunks with similarity percentages (0-100%).

#### Frontend UI (`frontend/src/components/editor/RAGKnowledgeInspector.tsx`)
- Status header: `🟢 RAG Engine Active — X Knowledge Docs Indexed`.
- Search & Tag filter input box.
- Document cards with title, tags, content snippet, and delete button.
- "Add Document" modal/form for indexing custom prompt guides.
- "Query Sandbox": Live search query input displaying similarity score bars.

---

### 2.3 Fixed ComfyUI Live Stream & WebSocket Proxy

#### Problem Statement
Currently, `ComfyUILiveStream.tsx` displays static mock values and does not connect to ComfyUI's native WebSocket (`ws://<comfy_url>/ws?clientId=<client_id>`).

#### Backend Solution (`comfyui_ws.py` & `comfyui_connector.py`)
- Standardize WebSocket proxy endpoint: `/api/v1/comfyui/ws/{client_id}`.
- Backend establishes a background client connection to ComfyUI's WebSocket server using `websockets`.
- Listens for:
  - `status`: Execution queue counts.
  - `executing`: Current node ID being processed.
  - `progress`: Current step value and total max steps.
  - `executed`: Node outputs including output image filenames/subfolders.
  - Binary frames (previews).
- Forwards parsed event JSON and Base64 preview frames to connected frontend client sockets.

#### Frontend UI (`ComfyUILiveStream.tsx`)
- Establishes WebSocket connection on component mount.
- Real-time Progress Bar: `Step X / Total (Y%)`.
- Current executing node display (`KSampler #3`).
- Live Frame Viewer: Renders binary preview frames or fetched PNGs as they complete.
- Auto-save: Completed output images automatically append to session history gallery.

---

## 3. Data Flow Diagrams

```
[User Input in Chat Drawer] ---> [POST /api/v1/ai/chat-refine]
                                       |
                                       v
                               [Async RAG Search]
                                       |
                                       v
                            [LLM Provider Manager]
                                       |
                                       v
                             [Structured Prompt Diff]
                                       |
                                       v
                        [Render Diff & Apply to Monaco]
```

```
[ComfyUI Server] <---(WS)---> [Backend Proxy websocket] <---(WS)---> [ComfyUILiveStream UI]
                                                                             |
                                                                             v
                                                                   [Step Bar & Live Frame]
```

---

## 4. Verification Plan

1. **Automated Unit Tests**:
   - Test `AsyncRAGEngine` document indexing, retrieval, stats, and deletion.
   - Test `/api/v1/ai/chat-refine` with mock LLM provider.
   - Test `/api/v1/comfyui/ws/{client_id}` WebSocket connection handshake and message forwarding.
2. **Manual Verification**:
   - Open Chat Drawer in UI, send prompt editing instructions ("add glowing sword"), verify diff and click "Apply to Editor".
   - Open RAG Inspector, verify status badge, add custom doc, search query, and check similarity scores.
   - Trigger ComfyUI generation sweep, verify live step progress bar updates and preview images stream correctly.
