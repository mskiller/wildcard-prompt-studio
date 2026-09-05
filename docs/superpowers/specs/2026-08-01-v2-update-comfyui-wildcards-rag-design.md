# Design Specification: Wildcard Prompt Studio V2 Feature Update

**Date**: 2026-08-01  
**Status**: Approved  
**Target Version**: V2.1.0  

---

## 1. Executive Summary

This specification outlines the technical design for four major feature enhancements to **Wildcard Prompt Studio V2**:
1. **Bi-Directional ComfyUI Workflow Graph Syncer & Dynamic Input Remapper**
2. **Real-Time VAE Latent Stream Preview & Interactive Batch Controller**
3. **Visual Wildcard Node Graph & Matrix Heatmap Canvas**
4. **Semantic Prompt Vault & RAG Auto-Indexing Engine**

---

## 2. Architecture & Subsystem Boundaries

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React 18 + Vite)                            │
│                                                                                 │
│  ┌───────────────────────┐ ┌───────────────────────────┐ ┌───────────────────┐  │
│  │ ComfyUILiveStream     │ │ WildcardNodeCanvas        │ │ SemanticVaultUI   │  │
│  │ (Graph Sync, Input    │ │ (Visual Tree & Heatmap)   │ │ (Duplicate Alert, │  │
│  │  Mapper, VAE Stream)  │ │                           │ │  RAG Autocomplete)│  │
│  └──────────┬────────────┘ └─────────────┬─────────────┘ └─────────┬─────────┘  │
└─────────────┼────────────────────────────┼─────────────────────────┼────────────┘
              │ WebSocket / REST           │ REST API                │ REST API
              ▼                            ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            BACKEND API (FastAPI)                                │
│                                                                                 │
│  ┌───────────────────────┐ ┌───────────────────────────┐ ┌───────────────────┐  │
│  │ ComfyUIConnector       │ │ WildcardASTEngine         │ │ AsyncRAGService   │  │
│  │ - Workflow Graph Parser│ │ - AST Graph Serializer    │ │ - SentenceTrans.  │  │
│  │ - WS Binary Preview    │ │ - Token & Length Scorer   │ │ - SQLite Vector   │  │
│  │ - Batch Action Queue   │ │                           │ │   Prompt Vault    │  │
│  └──────────┬────────────┘ └───────────────────────────┘ └───────────────────┘  │
│             │ HTTP / WS                                                         │
│             ▼                                                                   │
│  ┌───────────────────────┐                                                      │
│  │   Live ComfyUI Engine  │                                                      │
│  └───────────────────────┘                                                      │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Subsystem Specifications

### Subsystem 1: Bi-Directional ComfyUI Workflow Graph Syncer & Dynamic Remapper
* **Backend Services**:
  - `app/services/comfyui_connector.py`: Add `inspect_workflow_graph(workflow_json: dict)` method that crawls nodes and identifies configurable text prompt inputs (`CLIPTextEncode`, `CLIPTextEncodeSDXL`), sampler settings, seed fields, and resolution dimensions.
  - `app/api/routers/comfyui.py`: New endpoints `/workflow/inspect` and `/queue/mapped`.
* **Frontend Components**:
  - `frontend/src/components/editor/ComfyUILiveStream.tsx`: Add node mapping drawer where users select target node IDs for positive prompt, negative prompt, seed, and batch size.

### Subsystem 2: Real-Time VAE Latent Stream Preview & Interactive Batch Controller
* **Backend Services**:
  - `app/services/comfyui_ws.py`: Upgrade WebSocket handler to identify binary message types (`PREVIEW_IMAGE` JPEG frames) from ComfyUI and relay them to frontend subscribers.
  - Provide batch control APIs: `/queue/pause`, `/queue/cancel/{job_id}`, `/queue/clone`.
* **Frontend Components**:
  - `frontend/src/components/editor/ComfyUILiveStream.tsx`: Add progressive JPEG step preview image element, execution status progress bar, and interactive action buttons (Pause, Cancel, Clone Batch).

### Subsystem 3: Visual Wildcard Node Graph & Matrix Heatmap Canvas
* **Backend Services**:
  - `app/services/wildcard_ast.py`: Add `serialize_ast_to_graph(ast_root: RootNode) -> dict` and `deserialize_graph_to_ast(graph_json: dict) -> RootNode`.
  - `app/services/matrix_engine.py`: Add `analyze_matrix_heatmap(prompt_list: list) -> dict` calculating CLIP token distributions and Danbooru tag category proportions.
* **Frontend Components**:
  - `frontend/src/components/editor/WildcardMatrixPanel.tsx`: Interactive drag-and-drop visual node canvas for AST composition and matrix heatmap chart visualization.

### Subsystem 4: Semantic Prompt Vault & RAG Auto-Indexing Engine
* **Backend Services**:
  - `app/services/async_rag.py`: Maintain a background queue auto-embedding all created and saved prompts using `SentenceTransformer`. Store embeddings in SQLite table with cosine similarity query support.
  - `app/api/routers/prompts.py`: Add `/vault/similarity` endpoint to detect duplicates before saving or executing prompts (threshold >= 0.85).
* **Frontend Components**:
  - `frontend/src/components/editor/RAGKnowledgeInspector.tsx`: Display duplicate alert banners in the editor header and live semantic recommendations based on cursor focus.

---

## 4. API Contracts

### ComfyUI Sync & Queue
- `GET /api/v1/comfyui/workflow/inspect?server_url=...`: Returns list of inspectable nodes and their dynamic input schemas.
- `POST /api/v1/comfyui/queue/mapped`: Accepts prompt matrix array + node mapping dictionary and enqueues workflow jobs.
- `WS /api/v1/comfyui/ws/stream`: Bi-directional status, node highlight events, and binary VAE preview frames.

### Wildcard AST & Matrix
- `POST /api/v1/wildcards/ast/serialize`: Text prompt -> JSON AST Node Graph.
- `POST /api/v1/wildcards/ast/deserialize`: JSON AST Node Graph -> Text prompt.
- `POST /api/v1/generate/matrix/analyze`: Matrix prompt array -> Token count heatmap & tag balance.

### Semantic Vault
- `POST /api/v1/prompts/vault/similarity`: Prompt text -> List of semantic matches with similarity scores.
- `GET /api/v1/prompts/vault/recommendations?query=...`: Contextual semantic completions.

---

## 5. Error Handling & Edge Cases

1. **ComfyUI Unreachable**: Automatic fallback to simulated rendering engine with UI notification banner; WebSocket connection retries with exponential backoff.
2. **Invalid Workflow JSON**: JSON Schema validator rejects invalid workflows prior to queue submission and highlights bad nodes in red.
3. **AST Roundtrip Mismatches**: Deserialization validator verifies AST syntax before saving; reverts to raw string if graph structure is invalid.
4. **VRAM Resource Limits for SentenceTransformer**: Vector engine falls back to SQLite `FTS5` text search if embedding model initialization fails.

---

## 6. Testing & Verification Plan

### Backend Automated Tests (`backend/tests/`)
- `test_comfyui_graph_syncer.py`: Validate node detection and input binding for SD1.5, SDXL, and Flux workflows.
- `test_comfyui_ws_preview.py`: Mock WebSocket binary JPEG frame reception and relaying.
- `test_wildcard_ast_canvas.py`: Validate AST <-> Graph JSON bidirectional conversions.
- `test_semantic_prompt_vault.py`: Test embedding generation, similarity search scores, and duplicate thresholds.

### Frontend Unit Tests
- `ComfyUILiveStream.test.tsx`: Test dynamic mapping select elements and VAE preview image rendering.
- `WildcardNodeCanvas.test.tsx`: Test node connections and matrix heatmap updates.
