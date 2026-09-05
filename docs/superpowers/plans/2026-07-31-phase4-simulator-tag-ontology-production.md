# Phase 4: Prompt AST Visual Simulator, Tag Ontology Graph & Production Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build token-by-token prompt AST visual simulation, automated tag co-occurrence recommendation graph, and production multi-stage Docker orchestration.

**Architecture:** An AST graph evaluator router (`simulator.py`), a co-occurrence recommendation engine (`wildcard_graph.py`), a React visual tree component (`PromptGraphViewer.tsx`), and production Docker Nginx build configurations.

**Tech Stack:** Python 3.11, FastAPI, Pytest, React 18, SVG/D3 layout, Docker multi-stage, Nginx.

---

## File Structure & Responsibilities

### Backend Files:
- `backend/app/services/simulator.py`: Token-by-token AST evaluation state simulator.
- `backend/app/services/wildcard_graph.py`: Tag and wildcard co-occurrence association graph builder.
- `backend/app/api/routers/simulator.py`: Endpoints `/api/v1/simulator/tree` and `/api/v1/simulator/recommendations`.

### Frontend Files:
- `frontend/src/components/editor/PromptGraphViewer.tsx`: Interactive SVG rendering of AST nodes and wildcard substitution branches.
- `frontend/src/api.ts`: API endpoints for AST simulation tree and tag recommendations.

---

## Tasks

### Task 1: Prompt AST Visual Simulator & Router

**Files:**
- Modify: `backend/app/services/simulator.py`
- Modify: `backend/app/api/routers/simulator.py`
- Test: `backend/tests/test_simulator.py`

- [ ] **Step 1: Write failing unit test for simulator AST tree structure**

```python
import pytest
from app.services.simulator import SimulatorService

def test_ast_simulation_tree():
    service = SimulatorService()
    tree = service.build_ast_tree("a {cute|fierce} __animal__")
    assert "nodes" in tree
    assert len(tree["nodes"]) > 0
```

- [ ] **Step 2: Implement `SimulatorService` AST tree generator**

Convert WildcardASTEngine nodes into a JSON hierarchy formatted for frontend UI graphing.

- [ ] **Step 3: Run backend unit tests**

---

### Task 2: Tag Co-occurrence Graph Recommendation Engine

**Files:**
- Modify: `backend/app/services/wildcard_graph.py`
- Test: `backend/tests/test_wildcard_graph.py`

- [ ] **Step 1: Write unit tests for tag recommendations**

```python
import pytest
from app.services.wildcard_graph import TagGraphService

def test_tag_recommendations():
    graph = TagGraphService()
    graph.add_cooccurrence(["cyberpunk", "neon", "city"])
    recs = graph.recommend(["cyberpunk"])
    assert "neon" in recs or "city" in recs
```

- [ ] **Step 2: Implement `TagGraphService`**
- [ ] **Step 3: Expose recommendation endpoint in `/api/v1/simulator/recommendations`**

---

### Task 3: Interactive Visual AST Node Graph Component

**Files:**
- Create: `frontend/src/components/editor/PromptGraphViewer.tsx`
- Create: `frontend/src/components/editor/PromptGraphViewer.css`

- [ ] **Step 1: Build `PromptGraphViewer.tsx` rendering SVG node trees for choices and wildcards**
- [ ] **Step 2: Add Visual Simulator view tab in Sidebar & App layout**

---

### Task 4: Production Multi-Stage Docker & Nginx Setup

**Files:**
- Create: `docker-compose.prod.yml`
- Create: `frontend/nginx.conf`
- Modify: `frontend/Dockerfile`

- [ ] **Step 1: Create production Docker multi-stage build configuration and Nginx proxy**
- [ ] **Step 2: Verify build and test suite pass clean**

---
