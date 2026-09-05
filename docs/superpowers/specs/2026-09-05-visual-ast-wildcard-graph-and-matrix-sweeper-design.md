# Visual AST Wildcard Node Graph & Matrix Sweeper Design Specification

**Date:** 2026-09-05  
**Topic:** Visual AST Wildcard Node Graph & Matrix Sweeper  
**Status:** Approved by User  
**Target:** Wildcard Prompt Studio v3.2

---

## 1. Executive Summary & Goals

Wildcard Prompt Studio currently supports textual prompt engineering, wildcard replacement, AST linting, and basic matrix expansions. This design introduces an **interactive Visual AST Node Graph Canvas with Bi-Directional Live Synchronization** connected to an **Integrated Combinatorial Matrix Sweeper**.

Key goals:
1. **Bi-Directional Live Sync**: Edits made in the prompt editor update the visual node canvas in real-time, and node manipulation (dragging, weight tuning, adding wildcard slots) immediately compiles back into the prompt buffer.
2. **Native SVG/HTML5 Node Canvas**: High-performance, dependency-light interactive canvas with pan/zoom, bezier connection curves, and glassmorphism styling matching the studio theme.
3. **Interactive Choice & Wildcard Nodes**: Direct on-canvas sliders for option weights (`{1.5::cinematic | 0.8::anime}`), drag-reordering, and searchable wildcard pickers.
4. **Reactive Split-Pane Permutation Matrix**: Live computation of all Cartesian prompt combinations with token count heatmaps, category distribution metrics, and multi-seed ComfyUI batch sweep dispatching.

---

## 2. Architecture & Data Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│                        DATA FLOW ARCHITECTURE                          │
└────────────────────────────────────────────────────────────────────────┘
                                 
     [Text Prompt / Monaco] 
              │ ▲
   Parse AST  │ │  Compile AST
              ▼ │
   ┌───────────────────────┐         ┌────────────────────────┐
   │ AST Node Graph Canvas │ ──────> │ Live Permutation Grid  │
   │ - Drag & pan/zoom     │         │ - Cartesian products   │
   │ - Dynamic weights     │         │ - Token heatmaps       │
   │ - Wildcard slots      │         └───────────┬────────────┘
   └───────────────────────┘                     │
                                                 │ Queue Batch
                                                 ▼
                                     ┌────────────────────────┐
                                     │ ComfyUI Connector      │
                                     │ - Fixed/Random/Seq seed│
                                     │ - Steps / CFG override │
                                     └────────────────────────┘
```

### 2.1 AST ⇄ Graph Model Transformation

The system uses the established AST schema from `backend/app/services/wildcard_ast.py`:
- `RootNode`: Top-level sequence of prompt tokens.
- `TextNode`: Static phrases (`"masterpiece, 8k, cinematic portrait"`).
- `WildcardNode`: References to wildcard dictionaries (`__lighting/studio__`).
- `ChoiceNode`: Branching permutations with weights (`[ChoiceOption(weight=1.5, content=RootNode), ...]`).
- `VarAssignmentNode` / `VarRefNode`: Variable definitions and references (`$hero = ...`).

**Canvas Node Model (`CanvasNode`)**:
```typescript
export interface CanvasNode {
  id: string;
  type: 'root' | 'text' | 'wildcard' | 'choice' | 'variable';
  x: number;
  y: number;
  data: {
    text?: string;
    wildcardName?: string;
    options?: Array<{ id: string; text: string; weight: number }>;
    varName?: string;
    tokenCount?: number;
  };
  inputs: string[];
  outputs: string[];
}

export interface CanvasConnection {
  id: string;
  fromNodeId: string;
  toNodeId: string;
  type: 'sequence' | 'choice-branch';
}
```

### 2.2 Bi-Directional Synchronization Loop
1. **Editor &rarr; Canvas**:
   - Keystrokes in the prompt editor trigger a debounced (150ms) AST parse call.
   - The AST is converted into `CanvasNode[]` layout using topological layer positioning.
   - Existing node positions are preserved when possible to avoid layout jarring.
2. **Canvas &rarr; Editor**:
   - When a node's text, wildcard name, or weight slider changes on the canvas, the client AST compiler reconstructs the formatted prompt string.
   - The updated prompt is emitted to `usePromptStore`, updating the editor without resetting cursor positions.

---

## 3. UI/UX Layout & Component Hierarchy

### 3.1 Split-Pane Layout
The `WildcardMatrixPanel.tsx` and `PromptGraphViewer.tsx` are consolidated into a unified **Visual AST & Matrix Studio**:
- **Top Toolbar**:
  - Pan / Zoom controls (`Zoom In`, `Zoom Out`, `Reset 100%`).
  - Auto-Layout button (Sugiyama topological re-alignment).
  - Add Node dropdown: `+ Text`, `+ Wildcard`, `+ Choice Group`, `+ Variable`.
  - Permutation Counter badge (`24 Variations`).
  - Resizer handle between Canvas and Matrix grid.
- **Top/Left Pane — Interactive Node Canvas**:
  - Viewport with grid pattern background.
  - Infinite pan (middle click or spacebar+drag) and mouse-wheel zoom.
  - SVG bezier curve connections (`M x1 y1 C cx1 cy1, cx2 cy2, x2 y2`).
  - Glassmorphic card nodes with glowing drag handles.
- **Bottom/Right Pane — Combinatorial Permutations & Batch Queue**:
  - Live permutation cards showing variation text and token heat badges.
  - Category tags distribution bar (*artist*, *character*, *style*, *general*).
  - ComfyUI Batch Parameter Bar:
    - **Seed Strategy**: `Fixed` (same seed for all), `Random` (unique random per card), `Sequential` (`base_seed + index`).
    - **Parameters**: Steps slider, CFG slider, Sampler dropdown.
    - **Action**: `Queue Batch Sweep to ComfyUI` with real-time progress indicators.

---

## 4. Edge Cases & Safeguards

1. **Cycle Detection**:
   - Before evaluating or compiling canvas edges, depth-first search identifies any circular connections.
   - If a cycle is detected, the offending connection cable pulses in warning red (`#ef4444`), an alert badge appears, and permutation expansion is safely paused.
2. **Permutation Explosion**:
   - If user choices generate >250 permutations (e.g. 5 nested choice nodes with 4 options each), an optimization banner warns the user and offers a "Sample First 50" cap to keep UI and ComfyUI responsive.
3. **Offline / Busy ComfyUI**:
   - The batch dispatch button detects ComfyUI status (`/api/v1/comfyui/history/test` or WebSocket state) and clearly displays connection warnings if the local instance is offline.

---

## 5. Testing & Verification Plan

### 5.1 Automated Tests
- **Backend Unit Tests**:
  - Add `backend/tests/test_matrix_sweep_dispatcher.py` verifying batch sweep payload generation with fixed, random, and sequential seed calculations.
  - Verify AST graph serialization with `tests/test_wildcard_ast_canvas.py`.
- **Frontend Verification**:
  - Type-check with `npx tsc --noEmit` and build with `npx vite build`.
  - Verify smooth pan, zoom, and node dragging in browser.
  - Verify live prompt text updates when modifying node weights on the canvas.

### 5.2 Manual Verification
- Open `http://localhost:5173/` &rarr; Navigate to AST Graph / Matrix View.
- Connect 3 nodes: Text (`a portrait of`) &rarr; Choice (`{1.5::cyberpunk cat | 0.8::steampunk fox}`) &rarr; Wildcard (`__lighting/cinematic__`).
- Confirm text editor updates with `{1.5::cyberpunk cat | 0.8::steampunk fox}`.
- Trigger ComfyUI batch sweep with `Fixed` seed and verify execution in ComfyUI Live Stream.
