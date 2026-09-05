# Visual AST Wildcard Node Graph & Matrix Sweeper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an interactive Visual AST Node Graph Canvas with bi-directional prompt synchronization and an integrated Combinatorial Matrix Sweeper with multi-seed ComfyUI batch dispatch.

**Architecture:** Native SVG/HTML5 canvas with bezier curve cables and pan/zoom; bi-directional state synchronization between Monaco prompt buffer and AST canvas nodes; client/backend Cartesian permutation engine with token heatmaps; ComfyUI batch queue runner supporting Fixed, Random, and Sequential seeds.

**Tech Stack:** React 18, TypeScript, SVG, CSS Glassmorphism, FastAPI, Pydantic, ComfyUI API, Vite.

---

### Task 1: Backend Batch Sweep API & Smart Seed Strategies

**Files:**
- Modify: `backend/app/api/routers/comfyui.py:97-129`
- Create: `backend/tests/test_matrix_sweep_dispatcher.py`

- [ ] **Step 1: Write failing test for batch sweep dispatcher with seed strategies**

Create `backend/tests/test_matrix_sweep_dispatcher.py`:
```python
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_execute_sweep_with_seed_strategies():
    mock_workflow = {
        "3": {"inputs": {"seed": 0, "steps": 20, "cfg": 8.0, "sampler_name": "euler"}, "class_type": "KSampler"},
        "6": {"inputs": {"text": ""}, "class_type": "CLIPTextEncode"}
    }
    
    with patch("app.api.routers.comfyui.connector.queue_prompt", new_callable=AsyncMock) as mock_queue:
        mock_queue.return_value = {"prompt_id": "test-sweep", "number": 1}

        # 1. Test Sequential Strategy
        resp_seq = client.post(
            "/api/v1/comfyui/execute-sweep",
            json={
                "workflow": mock_workflow,
                "target_node_id": "6",
                "seed_node_id": "3",
                "prompts": ["prompt 1", "prompt 2", "prompt 3"],
                "seed_strategy": "sequential",
                "base_seed": 5000,
                "steps": 25,
                "cfg": 7.0,
                "sampler_name": "dpmpp_2m"
            }
        )
        assert resp_seq.status_code == 200
        data_seq = resp_seq.json()
        assert data_seq["queued_count"] == 3
        assert mock_queue.call_count == 3
        
        # Check first queued payload has base_seed 5000 and steps 25
        first_call_wf = mock_queue.call_args_list[0][0][0]
        assert first_call_wf["3"]["inputs"]["seed"] == 5000
        assert first_call_wf["3"]["inputs"]["steps"] == 25
        assert first_call_wf["3"]["inputs"]["cfg"] == 7.0
        assert first_call_wf["3"]["inputs"]["sampler_name"] == "dpmpp_2m"
        assert first_call_wf["6"]["inputs"]["text"] == "prompt 1"

        second_call_wf = mock_queue.call_args_list[1][0][0]
        assert second_call_wf["3"]["inputs"]["seed"] == 5001

        # 2. Test Fixed Strategy
        mock_queue.reset_mock()
        resp_fixed = client.post(
            "/api/v1/comfyui/execute-sweep",
            json={
                "workflow": mock_workflow,
                "target_node_id": "6",
                "seed_node_id": "3",
                "prompts": ["prompt A", "prompt B"],
                "seed_strategy": "fixed",
                "base_seed": 9999
            }
        )
        assert resp_fixed.status_code == 200
        assert mock_queue.call_count == 2
        call_0_wf = mock_queue.call_args_list[0][0][0]
        call_1_wf = mock_queue.call_args_list[1][0][0]
        assert call_0_wf["3"]["inputs"]["seed"] == 9999
        assert call_1_wf["3"]["inputs"]["seed"] == 9999
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker exec wildcard-prompt-studio-backend-1 pytest tests/test_matrix_sweep_dispatcher.py -v`
Expected: FAIL (missing fields / default hardcoded seeds).

- [ ] **Step 3: Update `backend/app/api/routers/comfyui.py` with seed strategies & parameter overrides**

In `backend/app/api/routers/comfyui.py`:
```python
import random

class SweepExecutionRequest(BaseModel):
    workflow: Dict[str, Any]
    target_node_id: str
    prompts: List[Any]
    seed_node_id: Optional[str] = None
    seed_strategy: Optional[str] = "sequential"  # "fixed", "random", "sequential"
    base_seed: Optional[int] = 42
    base_url: Optional[str] = None
    client_id: Optional[str] = None
    steps: Optional[int] = None
    cfg: Optional[float] = None
    sampler_name: Optional[str] = None

@router.post("/execute-sweep")
async def execute_sweep(req: SweepExecutionRequest):
    try:
        results = []
        base_seed = req.base_seed if req.base_seed is not None else random.randint(1, 1000000)
        
        for idx, prompt_str in enumerate(req.prompts):
            wf_copy = copy.deepcopy(req.workflow)
            
            # 1. Map prompt text into target CLIPTextEncode node
            if req.target_node_id in wf_copy:
                node = wf_copy.get(req.target_node_id, {})
                if isinstance(node, dict):
                    if "inputs" not in node or not isinstance(node["inputs"], dict):
                        node["inputs"] = {}
                    wf_copy[req.target_node_id]["inputs"]["text"] = str(prompt_str)
                    
            # 2. Map seed, steps, cfg, sampler into target KSampler node
            if req.seed_node_id and req.seed_node_id in wf_copy:
                sampler_node = wf_copy.get(req.seed_node_id, {})
                if isinstance(sampler_node, dict):
                    if "inputs" not in sampler_node or not isinstance(sampler_node["inputs"], dict):
                        sampler_node["inputs"] = {}
                    inputs = sampler_node["inputs"]
                    
                    # Calculate seed based on chosen strategy
                    if req.seed_strategy == "fixed":
                        inputs["seed"] = base_seed
                    elif req.seed_strategy == "random":
                        inputs["seed"] = random.randint(1, 2147483647)
                    else:  # sequential
                        inputs["seed"] = base_seed + idx
                        
                    if req.steps is not None:
                        inputs["steps"] = int(req.steps)
                    if req.cfg is not None:
                        inputs["cfg"] = float(req.cfg)
                    if req.sampler_name:
                        inputs["sampler_name"] = str(req.sampler_name)
                        
            res = await connector.queue_prompt(wf_copy, base_url=req.base_url, client_id=req.client_id)
            results.append(res)
            
        return {"queued_count": len(results), "job_results": results}
    except Exception as e:
        logger.error(f"Error executing sweep: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `docker exec wildcard-prompt-studio-backend-1 pytest tests/test_matrix_sweep_dispatcher.py -v`
Expected: PASS (all seed strategies and parameter overrides verified).

---

### Task 2: Frontend API Client Extension

**Files:**
- Modify: `frontend/src/api.ts:80-125`

- [ ] **Step 1: Add AST serialization & sweep execution helper functions in `frontend/src/api.ts`**

Add typed methods in `frontend/src/api.ts`:
```typescript
export interface SweepExecuteOptions {
  workflow?: Record<string, any>;
  targetNodeId?: string;
  seedNodeId?: string;
  prompts: string[];
  seedStrategy?: 'fixed' | 'random' | 'sequential';
  baseSeed?: number;
  steps?: number;
  cfg?: number;
  samplerName?: string;
}

export async function executeComfyUISweep(options: SweepExecuteOptions): Promise<{ queued_count: number; job_results: any[] }> {
  const payload = {
    workflow: options.workflow || {
      '3': { inputs: { seed: options.baseSeed || 42, steps: options.steps || 20, cfg: options.cfg || 8.0, sampler_name: options.samplerName || 'euler' }, class_type: 'KSampler' },
      '6': { inputs: { text: '' }, class_type: 'CLIPTextEncode' }
    },
    target_node_id: options.targetNodeId || '6',
    seed_node_id: options.seedNodeId || '3',
    prompts: options.prompts,
    seed_strategy: options.seedStrategy || 'sequential',
    base_seed: options.baseSeed ?? 42,
    steps: options.steps,
    cfg: options.cfg,
    sampler_name: options.samplerName
  };

  const res = await fetch(`${API_BASE}/comfyui/execute-sweep`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  if (!res.ok) throw new Error(`Failed to execute ComfyUI sweep: ${res.statusText}`);
  return res.json();
}

export async function serializeASTToGraph(prompt: string): Promise<any> {
  const res = await fetch(`${API_BASE}/simulator/ast/serialize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt })
  });
  if (!res.ok) throw new Error(`Failed to serialize AST: ${res.statusText}`);
  return res.json();
}
```

- [ ] **Step 2: Verify type checks**

Run: `docker exec wildcard-prompt-studio-frontend-1 npx tsc --noEmit`
Expected: Clean pass for `api.ts`.

---

### Task 3: Interactive SVG/HTML5 Node Canvas Component

**Files:**
- Create: `frontend/src/components/editor/VisualASTCanvas.tsx`
- Create: `frontend/src/components/editor/VisualASTCanvas.css`

- [ ] **Step 1: Create `VisualASTCanvas.tsx`**

Implement smooth pan, zoom, draggable nodes, cubic bezier curve rendering, node selection, and cycle detection:
```tsx
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { ZoomIn, ZoomOut, Maximize2, RefreshCw, Plus, AlertTriangle, Layers } from 'lucide-react';
import './VisualASTCanvas.css';

export interface ASTCanvasNodeData {
  id: string;
  type: 'root' | 'text' | 'wildcard' | 'choice' | 'variable';
  x: number;
  y: number;
  title: string;
  value: string;
  options?: Array<{ id: string; text: string; weight: number }>;
  outputs: string[]; // Connected child node IDs
}

interface VisualASTCanvasProps {
  nodes: ASTCanvasNodeData[];
  onNodesChange: (nodes: ASTCanvasNodeData[]) => void;
  onNodeSelect?: (nodeId: string) => void;
  onAutoLayout?: () => void;
  hasCycle?: boolean;
}

export const VisualASTCanvas: React.FC<VisualASTCanvasProps> = ({
  nodes,
  onNodesChange,
  onNodeSelect,
  onAutoLayout,
  hasCycle = false
}) => {
  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 40, y: 40 });
  const [isPanning, setIsPanning] = useState<boolean>(false);
  const [draggedNodeId, setDraggedNodeId] = useState<string | null>(null);
  const dragStartRef = useRef<{ mouseX: number; mouseY: number; initialNodeX: number; initialNodeY: number }>({ mouseX: 0, mouseY: 0, initialNodeX: 0, initialNodeY: 0 });
  const panStartRef = useRef<{ mouseX: number; mouseY: number; initialPanX: number; initialPanY: number }>({ mouseX: 0, mouseY: 0, initialPanX: 0, initialPanY: 0 });
  const containerRef = useRef<HTMLDivElement>(null);

  // Wheel zoom
  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    setZoom(prev => Math.min(Math.max(0.3, prev * zoomFactor), 2.5));
  };

  // Pan handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('.canvas-node')) return; // Ignore if clicking a node
    setIsPanning(true);
    panStartRef.current = { mouseX: e.clientX, mouseY: e.clientY, initialPanX: pan.x, initialPanY: pan.y };
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isPanning) {
      const dx = e.clientX - panStartRef.current.mouseX;
      const dy = e.clientY - panStartRef.current.mouseY;
      setPan({ x: panStartRef.current.initialPanX + dx, y: panStartRef.current.initialPanY + dy });
    } else if (draggedNodeId) {
      const dx = (e.clientX - dragStartRef.current.mouseX) / zoom;
      const dy = (e.clientY - dragStartRef.current.mouseY) / zoom;
      onNodesChange(
        nodes.map(n =>
          n.id === draggedNodeId
            ? { ...n, x: dragStartRef.current.initialNodeX + dx, y: dragStartRef.current.initialNodeY + dy }
            : n
        )
      );
    }
  };

  const handleMouseUp = () => {
    setIsPanning(false);
    setDraggedNodeId(null);
  };

  const startDragNode = (e: React.MouseEvent, node: ASTCanvasNodeData) => {
    e.stopPropagation();
    setDraggedNodeId(node.id);
    dragStartRef.current = { mouseX: e.clientX, mouseY: e.clientY, initialNodeX: node.x, initialNodeY: node.y };
    onNodeSelect?.(node.id);
  };

  // Render SVG Cubic Bezier Curves between connected nodes
  const renderConnections = () => {
    const nodeMap = new Map(nodes.map(n => [n.id, n]));
    const curves: JSX.Element[] = [];

    nodes.forEach(source => {
      source.outputs.forEach(targetId => {
        const target = nodeMap.get(targetId);
        if (!target) return;

        // Card width ~ 240, height ~ 110
        const startX = source.x + 240;
        const startY = source.y + 55;
        const endX = target.x;
        const endY = target.y + 55;
        const dx = Math.max(40, (endX - startX) * 0.5);

        const d = `M ${startX} ${startY} C ${startX + dx} ${startY}, ${endX - dx} ${endY}, ${endX} ${endY}`;
        curves.push(
          <path
            key={`${source.id}-${targetId}`}
            d={d}
            className={`canvas-bezier-cable ${hasCycle ? 'cable-cycle-warning' : ''}`}
          />
        );
      });
    });

    return curves;
  };

  return (
    <div
      className="visual-ast-canvas-container"
      ref={containerRef}
      onWheel={handleWheel}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      <div className="canvas-control-toolbar">
        <button className="canvas-tool-btn" onClick={() => setZoom(z => Math.min(2.5, z + 0.15))} title="Zoom In">
          <ZoomIn size={15} />
        </button>
        <span className="canvas-zoom-badge">{Math.round(zoom * 100)}%</span>
        <button className="canvas-tool-btn" onClick={() => setZoom(z => Math.max(0.3, z - 0.15))} title="Zoom Out">
          <ZoomOut size={15} />
        </button>
        <button className="canvas-tool-btn" onClick={() => { setZoom(1); setPan({ x: 40, y: 40 }); }} title="Reset View">
          <Maximize2 size={15} />
        </button>
        {onAutoLayout && (
          <button className="canvas-tool-btn primary" onClick={onAutoLayout} title="Auto-Arrange Layout">
            <RefreshCw size={14} /> Auto-Arrange
          </button>
        )}
        {hasCycle && (
          <span className="canvas-cycle-alert" title="Circular wildcard recursion detected!">
            <AlertTriangle size={14} /> Circular Loop Detected
          </span>
        )}
      </div>

      <div
        className="canvas-stage"
        style={{
          transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
          transformOrigin: '0 0'
        }}
      >
        <svg className="canvas-svg-layer">
          <defs>
            <linearGradient id="cableGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#818cf8" />
              <stop offset="100%" stopColor="#ec4899" />
            </linearGradient>
          </defs>
          {renderConnections()}
        </svg>

        {nodes.map(node => (
          <div
            key={node.id}
            className={`canvas-node canvas-node-${node.type}`}
            style={{ left: `${node.x}px`, top: `${node.y}px` }}
            onMouseDown={e => startDragNode(e, node)}
          >
            <div className="canvas-node-port port-in" />
            <div className="canvas-node-header">
              <span className="node-type-pill">{node.type.toUpperCase()}</span>
              <span className="node-title">{node.title}</span>
            </div>
            <div className="canvas-node-body">
              {node.type === 'choice' && node.options ? (
                <div className="choice-options-summary">
                  {node.options.map(opt => (
                    <div key={opt.id} className="choice-summary-pill">
                      <span className="opt-weight">{opt.weight}×</span>
                      <span className="opt-text">{opt.text}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="node-value-preview">{node.value}</div>
              )}
            </div>
            <div className="canvas-node-port port-out" />
          </div>
        ))}
      </div>
    </div>
  );
};
```

- [ ] **Step 2: Create `VisualASTCanvas.css`**

Add sleek glassmorphism styles, animated cable gradients, drag glow, and cycle alerts.

---

### Task 4: Specialized AST Node Interactive Subcomponents

**Files:**
- Create: `frontend/src/components/editor/nodes/CanvasTextNode.tsx`
- Create: `frontend/src/components/editor/nodes/CanvasWildcardNode.tsx`
- Create: `frontend/src/components/editor/nodes/CanvasChoiceNode.tsx`

- [ ] **Step 1: Create `CanvasChoiceNode.tsx` with live weight sliders and option add/remove**
- [ ] **Step 2: Create `CanvasWildcardNode.tsx` with searchable picker and sample pills**
- [ ] **Step 3: Create `CanvasTextNode.tsx` with live editing**

---

### Task 5: Bi-Directional Synchronization Hook (`useASTGraphSync.ts`)

**Files:**
- Create: `frontend/src/components/editor/useASTGraphSync.ts`

- [ ] **Step 1: Implement AST-to-Canvas parser and Canvas-to-Prompt compiler**
- [ ] **Step 2: Add cycle detection depth-first search**
- [ ] **Step 3: Add Sugiyama-style topological auto-layout**

---

### Task 6: Consolidated Visual AST & Matrix Studio Workspace Panel

**Files:**
- Modify: `frontend/src/components/editor/WildcardMatrixPanel.tsx`
- Modify: `frontend/src/components/editor/WildcardMatrixPanel.css`

- [ ] **Step 1: Embed `VisualASTCanvas` into the split-pane workspace**
- [ ] **Step 2: Connect ComfyUI Batch Parameter Bar (Fixed, Random, Sequential seed strategies)**
- [ ] **Step 3: Wire one-click "Queue Batch Sweep to ComfyUI" action with progress toast**

---

### Task 7: End-to-End System Verification

- [ ] **Step 1: Execute full backend test suite: `docker exec wildcard-prompt-studio-backend-1 pytest -v`**
- [ ] **Step 2: Build frontend: `docker exec wildcard-prompt-studio-frontend-1 npx vite build`**
- [ ] **Step 3: Browser QA inspection of AST Node Canvas & Matrix Sweep**
