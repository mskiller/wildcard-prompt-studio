# Phase 5 & 6: Aesthetic Scoring, Genetic Prompt Evolution, Civitai Sync & Cloud Storage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build automated image aesthetic scoring (PickScore/CLIP), genetic wildcard prompt optimization, Civitai/HuggingFace wildcard sync daemon, and S3/R2 cloud storage backend.

**Architecture:** An aesthetic evaluation service (`aesthetic_scorer.py`), a genetic prompt mutation engine (`genetic_optimizer.py`), a Civitai/HF REST sync worker (`civitai_sync.py`), an S3-compatible cloud storage manager (`cloud_storage.py`), and React evaluation UI components (`AestheticRankerPanel.tsx`).

**Tech Stack:** Python 3.11, FastAPI, Pytest, Pillow/Torch, boto3, React 18, TypeScript.

---

## File Structure & Responsibilities

### Backend Files:
- `backend/app/services/aesthetic_scorer.py`: Aesthetic evaluation engine compute (CLIP/PickScore simulated/lightweight scoring).
- `backend/app/services/genetic_optimizer.py`: Evolutionary algorithm mutating prompt wildcards based on fitness scores.
- `backend/app/services/civitai_sync.py`: Integration client with Civitai and Hugging Face REST APIs for wildcard pack downloads.
- `backend/app/services/cloud_storage.py`: S3 / R2 object storage client for rendered assets and wildcard backups.
- `backend/app/api/routers/aesthetic.py`: Router for `/api/v1/aesthetic/score`, `/api/v1/aesthetic/evolve`, `/api/v1/civitai/sync`, and `/api/v1/cloud/upload`.

### Frontend Files:
- `frontend/src/components/editor/AestheticRankerPanel.tsx`: Interactive image rating, prompt evolution trigger, and Civitai hub browser.
- `frontend/src/api.ts`: API endpoints for aesthetic scoring, prompt evolution, and hub sync.

---

## Tasks

### Task 1: Aesthetic Scoring Engine & Router

**Files:**
- Create: `backend/app/services/aesthetic_scorer.py`
- Create: `backend/app/api/routers/aesthetic.py`
- Modify: `backend/app/api/routers/__init__.py`
- Test: `backend/tests/test_aesthetic_scorer.py`

- [ ] **Step 1: Write unit test for AestheticScorer**

```python
import pytest
from app.services.aesthetic_scorer import AestheticScorer

def test_aesthetic_score_calculation():
    scorer = AestheticScorer()
    score = scorer.score_prompt_and_metadata("a masterpice photorealistic portrait", width=1024, height=1024)
    assert 0.0 <= score <= 10.0
```

- [ ] **Step 2: Implement `AestheticScorer`**
- [ ] **Step 3: Create FastAPI router for aesthetic scoring**
- [ ] **Step 4: Run backend unit tests**

---

### Task 2: Genetic Algorithm Prompt Mutation Optimizer

**Files:**
- Create: `backend/app/services/genetic_optimizer.py`
- Test: `backend/tests/test_genetic_optimizer.py`

- [ ] **Step 1: Write unit test for GeneticPromptOptimizer**

```python
import pytest
from app.services.genetic_optimizer import GeneticPromptOptimizer

def test_genetic_evolution_generation():
    optimizer = GeneticPromptOptimizer()
    population = ["a {cute|fierce} cat", "a {small|large} cat"]
    fitness_scores = [7.5, 9.1]
    next_gen = optimizer.evolve(population, fitness_scores)
    assert len(next_gen) > 0
```

- [ ] **Step 2: Implement `GeneticPromptOptimizer` with selection, crossover, and mutation operators**
- [ ] **Step 3: Run backend unit tests**

---

### Task 3: Civitai & HuggingFace Model Hub Sync Daemon

**Files:**
- Create: `backend/app/services/civitai_sync.py`
- Test: `backend/tests/test_civitai_sync.py`

- [ ] **Step 1: Write unit test for CivitaiSyncClient**

```python
import pytest
from app.services.civitai_sync import CivitaiSyncClient

@pytest.mark.asyncio
async def test_search_wildcard_packs():
    client = CivitaiSyncClient()
    packs = await client.search_wildcard_packs("fantasy")
    assert isinstance(packs, list)
```

- [ ] **Step 2: Implement `CivitaiSyncClient`**
- [ ] **Step 3: Add endpoint `/api/v1/civitai/sync`**

---

### Task 4: S3/R2 Cloud Storage Backend & React Aesthetic Ranker Panel

**Files:**
- Create: `backend/app/services/cloud_storage.py`
- Create: `frontend/src/components/editor/AestheticRankerPanel.tsx`
- Create: `frontend/src/components/editor/AestheticRankerPanel.css`

- [ ] **Step 1: Implement `CloudStorageService`**
- [ ] **Step 2: Build `AestheticRankerPanel.tsx` with ELO voting grid, prompt evolution triggers, and Civitai Hub browser**
- [ ] **Step 3: Add Aesthetic Ranker tab in Sidebar & App layout**
- [ ] **Step 4: Run all unit tests for verification**

---
