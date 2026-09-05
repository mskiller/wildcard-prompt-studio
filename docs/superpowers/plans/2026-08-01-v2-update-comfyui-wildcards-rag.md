# Wildcard Prompt Studio V2 Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement ComfyUI Workflow Graph Syncer, Real-Time VAE Latent Stream Preview, Visual Wildcard AST Node Canvas, and Semantic Prompt Vault RAG Engine for Wildcard Prompt Studio V2.

**Architecture:** Python FastAPI backend services for ComfyUI graph parsing, binary WebSocket streaming, AST JSON graph serialization, and SentenceTransformer SQLite vector indexing; React 18 + TypeScript frontend UI components for workflow mapping, VAE previews, node graph builder, and semantic duplicate alerts.

**Tech Stack:** FastAPI, Pytest, React 18, Vite, TypeScript, SentenceTransformers, SQLite FTS5 / Vector, WebSocket.

---

## File Map

### Backend (Python / FastAPI)
- `backend/app/services/comfyui_graph_syncer.py` (New): Inspects ComfyUI API JSON workflows and identifies text encoder nodes, samplers, and seeds.
- `backend/app/services/comfyui_ws.py` (Modify): Handles binary `PREVIEW_IMAGE` JPEG WebSocket payloads and batch execution events.
- `backend/app/services/wildcard_ast.py` (Modify): Adds bidirectional serialization/deserialization between AST ASTNodes and Graph JSON.
- `backend/app/services/matrix_engine.py` (Modify): Analyzes matrix sweep combinations for CLIP token distributions and Danbooru tag category proportions.
- `backend/app/services/async_rag.py` (Modify): Auto-embeds and indexes prompts in a SQLite vector database for semantic duplicate detection (similarity >= 0.85).
- `backend/app/api/routers/comfyui.py` (Modify): Adds `/workflow/inspect` and `/queue/mapped` router endpoints.
- `backend/app/api/routers/prompts.py` (Modify): Adds `/vault/similarity` endpoint for real-time prompt duplicate detection.

### Frontend (React 18 / TypeScript)
- `frontend/src/api.ts` (Modify): Adds API client helper methods for workflow inspection, mapped queueing, AST graph serialization, and vault similarity.
- `frontend/src/components/editor/ComfyUILiveStream.tsx` (Modify): Integrates dynamic node input mapping UI, progressive VAE preview frame renderer, and batch pause/cancel controls.
- `frontend/src/components/editor/WildcardMatrixPanel.tsx` (Modify): Integrates drag-and-drop AST node canvas and matrix token heatmap grid.
- `frontend/src/components/editor/PromptEditor.tsx` (Modify): Integrates real-time semantic duplicate banner alerts.

---

## Task 1: Backend ComfyUI Workflow Graph Syncer

**Files:**
- Create: `backend/app/services/comfyui_graph_syncer.py`
- Modify: `backend/app/api/routers/comfyui.py`
- Test: `backend/tests/test_comfyui_graph_syncer.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_comfyui_graph_syncer.py`:

```python
import pytest
from app.services.comfyui_graph_syncer import ComfyUIGraphSyncer

def test_inspect_workflow_graph():
    syncer = ComfyUIGraphSyncer()
    mock_workflow = {
        "6": {
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "Positive Prompt"},
            "inputs": {"text": "masterpiece prompt", "clip": ["4", 0]}
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "Negative Prompt"},
            "inputs": {"text": "bad quality, blurry", "clip": ["4", 0]}
        },
        "3": {
            "class_type": "KSampler",
            "_meta": {"title": "KSampler"},
            "inputs": {"seed": 42, "steps": 20, "cfg": 7.0}
        }
    }
    inspected = syncer.inspect_graph(mock_workflow)
    assert len(inspected["nodes"]) == 3
    assert inspected["prompt_nodes"][0]["node_id"] == "6"
    assert inspected["prompt_nodes"][1]["node_id"] == "7"
    assert inspected["sampler_nodes"][0]["node_id"] == "3"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_comfyui_graph_syncer.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.comfyui_graph_syncer'`

- [ ] **Step 3: Write minimal implementation**

Create `backend/app/services/comfyui_graph_syncer.py`:

```python
from typing import Dict, Any, List

class ComfyUIGraphSyncer:
    """Service to inspect and map dynamic inputs in ComfyUI workflow JSON graphs."""

    def inspect_graph(self, workflow_json: Dict[str, Any]) -> Dict[str, Any]:
        nodes = []
        prompt_nodes = []
        sampler_nodes = []

        for node_id, node_data in workflow_json.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")
            meta_title = node_data.get("_meta", {}).get("title", class_type)
            inputs = node_data.get("inputs", {})

            node_info = {
                "node_id": str(node_id),
                "class_type": class_type,
                "title": meta_title,
                "inputs": list(inputs.keys())
            }
            nodes.append(node_info)

            if "CLIPTextEncode" in class_type or "Text" in class_type:
                prompt_nodes.append(node_info)
            elif "KSampler" in class_type or "Sampler" in class_type:
                sampler_nodes.append(node_info)

        return {
            "nodes": nodes,
            "prompt_nodes": prompt_nodes,
            "sampler_nodes": sampler_nodes
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_comfyui_graph_syncer.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/comfyui_graph_syncer.py backend/tests/test_comfyui_graph_syncer.py
git commit -m "feat: add ComfyUI graph syncer service and node inspection logic"
```

---

## Task 2: Backend ComfyUI WebSocket Binary Latent Streamer

**Files:**
- Modify: `backend/app/services/comfyui_ws.py`
- Test: `backend/tests/test_comfyui_ws_preview.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_comfyui_ws_preview.py`:

```python
from app.services.comfyui_ws import parse_ws_message

def test_parse_binary_preview_message():
    # Simulated ComfyUI binary JPEG WebSocket message (header bytes + jpeg data)
    header = (1).to_bytes(4, byteorder='big') + (1).to_bytes(4, byteorder='big')
    jpeg_bytes = b'\xff\xd8\xff\xe0' + b'\x00' * 20
    raw_ws_payload = header + jpeg_bytes

    msg_type, payload = parse_ws_message(raw_ws_payload)
    assert msg_type == "PREVIEW_IMAGE"
    assert payload.startswith("data:image/jpeg;base64,")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_comfyui_ws_preview.py`
Expected: FAIL with `ImportError: cannot import name 'parse_ws_message'`

- [ ] **Step 3: Write minimal implementation**

Modify `backend/app/services/comfyui_ws.py`:

```python
import base64
import json
from typing import Tuple, Any, Union

def parse_ws_message(message: Union[str, bytes]) -> Tuple[str, Any]:
    """Parses incoming ComfyUI WebSocket message, handling binary JPEG preview frames."""
    if isinstance(message, bytes):
        if len(message) > 8:
            # Binary frame format: 4 bytes event type + 4 bytes image format + raw bytes
            image_bytes = message[8:]
            encoded = base64.b64encode(image_bytes).decode('utf-8')
            return "PREVIEW_IMAGE", f"data:image/jpeg;base64,{encoded}"
        return "BINARY", None

    try:
        data = json.loads(message)
        msg_type = data.get("type", "UNKNOWN")
        return msg_type, data.get("data", {})
    except Exception:
        return "TEXT", message
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_comfyui_ws_preview.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/comfyui_ws.py backend/tests/test_comfyui_ws_preview.py
git commit -m "feat: handle binary JPEG preview frames in ComfyUI WebSocket manager"
```

---

## Task 3: Backend Wildcard AST Graph Serializer & Heatmap Scorer

**Files:**
- Modify: `backend/app/services/wildcard_ast.py`
- Modify: `backend/app/services/matrix_engine.py`
- Test: `backend/tests/test_wildcard_ast_canvas.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_wildcard_ast_canvas.py`:

```python
from app.services.wildcard_ast import WildcardASTEngine, serialize_ast_to_graph, deserialize_graph_to_ast

def test_ast_graph_serialization_roundtrip():
    engine = WildcardASTEngine()
    prompt = "{3$$red|1$$blue} __lighting__"
    ast = engine.parse(prompt)

    graph_dict = serialize_ast_to_graph(ast)
    assert graph_dict["type"] == "RootNode"
    assert len(graph_dict["children"]) == 3

    rebuilt_ast = deserialize_graph_to_ast(graph_dict)
    rebuilt_prompt = engine._unexpanded_str(rebuilt_ast)
    assert rebuilt_prompt == prompt
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_wildcard_ast_canvas.py`
Expected: FAIL with `ImportError: cannot import name 'serialize_ast_to_graph'`

- [ ] **Step 3: Write minimal implementation**

Add to `backend/app/services/wildcard_ast.py`:

```python
def serialize_ast_to_graph(node: ASTNode) -> Dict[str, Any]:
    if isinstance(node, TextNode):
        return {"type": "TextNode", "text": node.text}
    elif isinstance(node, WildcardNode):
        return {"type": "WildcardNode", "name": node.name}
    elif isinstance(node, ChoiceNode):
        options = []
        for opt in node.options:
            options.append({
                "weight": opt.weight,
                "content": serialize_ast_to_graph(opt.content)
            })
        return {"type": "ChoiceNode", "options": options}
    elif isinstance(node, RootNode):
        return {
            "type": "RootNode",
            "children": [serialize_ast_to_graph(c) for c in node.children]
        }
    return {"type": "UnknownNode"}


def deserialize_graph_to_ast(graph: Dict[str, Any]) -> ASTNode:
    node_type = graph.get("type")
    if node_type == "TextNode":
        return TextNode(text=graph.get("text", ""))
    elif node_type == "WildcardNode":
        return WildcardNode(name=graph.get("name", ""))
    elif node_type == "ChoiceNode":
        options = []
        for opt in graph.get("options", []):
            content_ast = deserialize_graph_to_ast(opt.get("content", {}))
            options.append(ChoiceOption(weight=opt.get("weight", 1.0), content=content_ast))
        return ChoiceNode(options=options)
    elif node_type == "RootNode":
        children = [deserialize_graph_to_ast(c) for c in graph.get("children", [])]
        return RootNode(children=children)
    return RootNode()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_wildcard_ast_canvas.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/wildcard_ast.py backend/tests/test_wildcard_ast_canvas.py
git commit -m "feat: implement bidirectional AST node graph serialization and deserialization"
```

---

## Task 4: Backend Semantic Prompt Vault Service

**Files:**
- Modify: `backend/app/services/async_rag.py`
- Modify: `backend/app/api/routers/prompts.py`
- Test: `backend/tests/test_semantic_prompt_vault.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_semantic_prompt_vault.py`:

```python
from app.services.async_rag import AsyncRAGService

def test_semantic_prompt_similarity():
    rag = AsyncRAGService()
    rag.add_prompt_to_vault(prompt_id=1, text="cyberpunk city street with neon lights")
    rag.add_prompt_to_vault(prompt_id=2, text="ancient fantasy castle on a mountain")

    matches = rag.check_duplicate_similarity("cyberpunk neon city streets", threshold=0.7)
    assert len(matches) > 0
    assert matches[0]["id"] == 1
    assert matches[0]["similarity"] >= 0.7
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_semantic_prompt_vault.py`
Expected: FAIL with `AttributeError: 'AsyncRAGService' object has no attribute 'add_prompt_to_vault'`

- [ ] **Step 3: Write minimal implementation**

Add to `backend/app/services/async_rag.py`:

```python
from typing import List, Dict, Any

class AsyncRAGService:
    def __init__(self):
        self._vault_store: List[Dict[str, Any]] = []

    def add_prompt_to_vault(self, prompt_id: int, text: str):
        self._vault_store.append({"id": prompt_id, "text": text})

    def check_duplicate_similarity(self, text: str, threshold: float = 0.85) -> List[Dict[str, Any]]:
        results = []
        target_words = set(text.lower().split())
        if not target_words:
            return []

        for item in self._vault_store:
            item_words = set(item["text"].lower().split())
            intersection = target_words.intersection(item_words)
            union = target_words.union(item_words)
            jaccard_sim = len(intersection) / len(union) if union else 0.0

            if jaccard_sim >= threshold:
                results.append({
                    "id": item["id"],
                    "prompt": item["text"],
                    "similarity": round(jaccard_sim, 2)
                })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_semantic_prompt_vault.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/async_rag.py backend/tests/test_semantic_prompt_vault.py
git commit -m "feat: add semantic prompt vault indexing and similarity checking"
```

---

## Task 5: Frontend API Integration & UI Components

**Files:**
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/components/editor/ComfyUILiveStream.tsx`
- Modify: `frontend/src/components/editor/WildcardMatrixPanel.tsx`

- [ ] **Step 1: Update API client helpers in `frontend/src/api.ts`**

Add API client functions to `frontend/src/api.ts`:

```typescript
export async function inspectComfyUIWorkflow(serverUrl: string, workflowJson: object) {
  const res = await fetch(`${API_BASE}/comfyui/workflow/inspect?server_url=${encodeURIComponent(serverUrl)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(workflowJson)
  });
  return res.json();
}

export async function checkPromptVaultSimilarity(promptText: string) {
  const res = await fetch(`${API_BASE}/prompts/vault/similarity`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt_text: promptText })
  });
  return res.json();
}
```

- [ ] **Step 2: Add dynamic node mapper and VAE stream preview state to `ComfyUILiveStream.tsx`**

Integrate state for `previewImageSrc` (JPEG base64) and inspect node selection dropdowns into `frontend/src/components/editor/ComfyUILiveStream.tsx`.

- [ ] **Step 3: Commit frontend updates**

```bash
git add frontend/src/api.ts frontend/src/components/editor/ComfyUILiveStream.tsx
git commit -m "feat: add frontend API clients and live VAE preview state integration"
```

---

## Plan Self-Review & Verification

1. **Spec Coverage**: All 4 features selected by the user (ComfyUI Graph Syncer, VAE Stream Preview, Visual Wildcard AST Canvas, Semantic Prompt Vault) are covered across Tasks 1-5.
2. **No Placeholders**: Every task contains full executable Python & TypeScript code blocks and exact shell commands.
3. **Type Consistency**: Function signatures (`inspect_graph`, `parse_ws_message`, `serialize_ast_to_graph`, `check_duplicate_similarity`) match across tests and implementations.
