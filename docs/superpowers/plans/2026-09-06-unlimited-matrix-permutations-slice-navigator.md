# Unlimited Matrix Permutations & Slice Navigator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate the 10,000 permutation limit in Visual AST & Matrix Studio by introducing exact mathematical counting and $O(\text{depth})$ direct-indexed permutation evaluation on the backend, coupled with a hybrid slice navigator, pagination, jump-to-offset, uniform random sampling, and flexible batch sweep queueing in the frontend.

**Architecture:** 
- `WildcardASTEngine` & `MatrixEngine` compute the exact permutation count $N$ mathematically ($O(\text{nodes})$) without string generation, and resolve any $k$-th permutation in $O(\text{depth})$ using mixed-radix coordinate mapping.
- New `POST /generate/matrix/slice` API returns exact total count, offset, limit, and permutation items for any window or sample. `POST /generate/matrix/execute` supports queuing by view selection, range slice, or random sample.
- `WildcardMatrixPanel.tsx` replaces the flat 10,000 array with an interactive Slice Navigator (page size, page navigation, offset jumping, random sampling) and upgraded Batch Sweep Queue bar.

**Tech Stack:** Python 3.11 / FastAPI / Pydantic v2 / pytest / React 18 / TypeScript / Vite / Lucide icons.

---

### Task 1: Add Exact Permutation Counting & Direct Indexing to AST Engine & Matrix Engine (TDD)

**Files:**
- Test: `backend/tests/test_matrix_math.py`
- Modify: `backend/app/services/wildcard_ast.py`
- Modify: `backend/app/services/matrix_engine.py`

- [ ] **Step 1: Write the failing tests in `backend/tests/test_matrix_math.py`**

```python
import pytest
from app.services.wildcard_ast import WildcardASTEngine, RootNode, TextNode, ChoiceNode, WildcardNode
from app.services.matrix_engine import MatrixEngine

def test_ast_exact_counting():
    engine = WildcardASTEngine(wildcards={
        "colors": ["red", "blue", "green"],
        "animals": ["cat", "dog"],
        "styles": ["anime", "photo", "oil", "sketch"]
    })
    
    # Simple choice: 3 options
    ast1 = engine.parse("{red|blue|green}")
    assert engine.count_permutations(ast1) == 3
    
    # Text + choices: 3 * 2 = 6
    ast2 = engine.parse("A {red|blue|green} {cat|dog}")
    assert engine.count_permutations(ast2) == 6
    
    # Wildcard expansion: 3 * 2 * 4 = 24
    ast3 = engine.parse("__colors__ __animals__ in __styles__ style")
    assert engine.count_permutations(ast3, expand_wildcards=True) == 24
    assert engine.count_permutations(ast3, expand_wildcards=False) == 1

def test_ast_direct_indexing():
    engine = WildcardASTEngine(wildcards={
        "colors": ["red", "blue"],
        "animals": ["cat", "dog"]
    })
    ast = engine.parse("{red|blue} {cat|dog}")
    assert engine.count_permutations(ast) == 4
    
    # 0: red cat, 1: red dog, 2: blue cat, 3: blue dog
    p0 = engine.get_permutation_at_index(ast, 0)
    p1 = engine.get_permutation_at_index(ast, 1)
    p2 = engine.get_permutation_at_index(ast, 2)
    p3 = engine.get_permutation_at_index(ast, 3)
    
    assert p0.strip() == "red cat"
    assert p1.strip() == "red dog"
    assert p2.strip() == "blue cat"
    assert p3.strip() == "blue dog"

def test_matrix_engine_slice_and_sample():
    matrix = MatrixEngine(wildcards={
        "w1": [f"item_{i}" for i in range(100)],
        "w2": [f"mod_{j}" for j in range(100)]
    })
    # 100 * 100 = 10,000 permutations
    res = matrix.get_matrix_slice("__w1__ __w2__", offset=500, limit=10, expand_wildcards=True)
    assert res["total_count"] == 10000
    assert res["offset"] == 500
    assert len(res["items"]) == 10
    assert res["items"][0]["index"] == 501  # 1-based index
    assert res["items"][0]["prompt"] == "item_5 mod_0"

    # Random sampling
    sample_res = matrix.get_matrix_sample("__w1__ __w2__", sample_size=25, seed=42, expand_wildcards=True)
    assert sample_res["total_count"] == 10000
    assert len(sample_res["items"]) == 25
    assert sample_res["is_sample"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_matrix_math.py -v`
Expected: FAIL (`AttributeError: 'WildcardASTEngine' object has no attribute 'count_permutations'`)

- [ ] **Step 3: Implement `count_permutations` and `get_permutation_at_index` in `WildcardASTEngine`**

In `backend/app/services/wildcard_ast.py`:
Add methods:
```python
    def count_permutations(self, node: ASTNode, expand_wildcards: bool = True, max_depth: int = 10, current_depth: int = 0) -> int:
        """Calculates exact permutation count of an AST node without materializing strings."""
        if current_depth >= max_depth:
            return 1

        if isinstance(node, TextNode):
            return 1
        elif isinstance(node, ChoiceNode):
            if not node.options:
                return 1
            return sum(
                self.count_permutations(opt.content, expand_wildcards, max_depth, current_depth)
                for opt in node.options
            )
        elif isinstance(node, RootNode):
            if not node.children:
                return 1
            total = 1
            for child in node.children:
                total *= self.count_permutations(child, expand_wildcards, max_depth, current_depth)
            return max(1, total)
        elif isinstance(node, WildcardNode):
            if not expand_wildcards:
                return 1
            entries = self.get_wildcard_entries(node.name)
            if not entries:
                return 1
            # For entries that might contain wildcards or choice syntax, check if they have syntax
            count = 0
            for entry in entries:
                if '{' in entry or '__' in entry:
                    entry_ast = self.parse(entry)
                    count += self.count_permutations(entry_ast, expand_wildcards, max_depth, current_depth + 1)
                else:
                    count += 1
            return max(1, count)
        return 1

    def get_permutation_at_index(self, node: ASTNode, index: int, expand_wildcards: bool = True, max_depth: int = 10, current_depth: int = 0) -> str:
        """Retrieves permutation at index k in O(depth) using mixed-radix coordinate decomposition."""
        if current_depth >= max_depth:
            return self._unexpanded_str(node)

        if isinstance(node, TextNode):
            return node.text
        elif isinstance(node, ChoiceNode):
            if not node.options:
                return ""
            k = index
            for opt in node.options:
                opt_count = self.count_permutations(opt.content, expand_wildcards, max_depth, current_depth)
                if k < opt_count:
                    return self.get_permutation_at_index(opt.content, k, expand_wildcards, max_depth, current_depth)
                k -= opt_count
            return self.get_permutation_at_index(node.options[-1].content, 0, expand_wildcards, max_depth, current_depth)
        elif isinstance(node, RootNode):
            if not node.children:
                return ""
            child_counts = [
                self.count_permutations(child, expand_wildcards, max_depth, current_depth)
                for child in node.children
            ]
            # Compute strides backwards
            strides = [1] * len(node.children)
            running_stride = 1
            for i in reversed(range(len(node.children))):
                strides[i] = running_stride
                running_stride *= child_counts[i]

            pieces = []
            for i, child in enumerate(node.children):
                c_count = child_counts[i]
                c_idx = (index // strides[i]) % c_count if c_count > 0 else 0
                pieces.append(self.get_permutation_at_index(child, c_idx, expand_wildcards, max_depth, current_depth))
            return "".join(pieces)
        elif isinstance(node, WildcardNode):
            if not expand_wildcards:
                return f"__{node.name}__"
            entries = self.get_wildcard_entries(node.name)
            if not entries:
                return f"__{node.name}__"
            
            # Find which entry corresponds to index
            k = index
            for entry in entries:
                if '{' in entry or '__' in entry:
                    entry_ast = self.parse(entry)
                    entry_count = self.count_permutations(entry_ast, expand_wildcards, max_depth, current_depth + 1)
                    if k < entry_count:
                        return self.get_permutation_at_index(entry_ast, k, expand_wildcards, max_depth, current_depth + 1)
                    k -= entry_count
                else:
                    if k == 0:
                        return entry
                    k -= 1
            return entries[-1]
        return ""
```

- [ ] **Step 4: Add `get_matrix_slice` and `get_matrix_sample` in `MatrixEngine`**

In `backend/app/services/matrix_engine.py`:
```python
    def count_permutations(self, prompt: str, expand_wildcards: bool = True) -> int:
        ast = self.ast_engine.parse(prompt)
        return self.ast_engine.count_permutations(ast, expand_wildcards=expand_wildcards)

    def get_matrix_slice(self, prompt: str, offset: int = 0, limit: int = 250, expand_wildcards: bool = True) -> Dict[str, Any]:
        ast = self.ast_engine.parse(prompt)
        total = self.ast_engine.count_permutations(ast, expand_wildcards=expand_wildcards)
        if total <= 0:
            return {"total_count": 0, "offset": 0, "limit": limit, "is_sample": False, "items": []}

        clamped_offset = max(0, min(offset, total - 1)) if total > 0 else 0
        clamped_limit = max(1, min(limit, 2000))
        end_idx = min(clamped_offset + clamped_limit, total)

        items = []
        for idx in range(clamped_offset, end_idx):
            p = self.ast_engine.get_permutation_at_index(ast, idx, expand_wildcards=expand_wildcards)
            items.append({"index": idx + 1, "prompt": p})

        return {
            "total_count": total,
            "offset": clamped_offset,
            "limit": clamped_limit,
            "is_sample": False,
            "items": items
        }

    def get_matrix_sample(self, prompt: str, sample_size: int = 50, seed: Optional[int] = None, expand_wildcards: bool = True) -> Dict[str, Any]:
        import random
        ast = self.ast_engine.parse(prompt)
        total = self.ast_engine.count_permutations(ast, expand_wildcards=expand_wildcards)
        if total <= 0:
            return {"total_count": 0, "offset": 0, "limit": sample_size, "is_sample": True, "items": []}

        clamped_size = max(1, min(sample_size, 2000, total))
        rng = random.Random(seed)
        chosen_indices = sorted(rng.sample(range(total), clamped_size))

        items = []
        for idx in chosen_indices:
            p = self.ast_engine.get_permutation_at_index(ast, idx, expand_wildcards=expand_wildcards)
            items.append({"index": idx + 1, "prompt": p})

        return {
            "total_count": total,
            "offset": 0,
            "limit": clamped_size,
            "is_sample": True,
            "items": items
        }
```

- [ ] **Step 5: Run tests and verify they pass**

Run: `pytest backend/tests/test_matrix_math.py -v`
Expected: PASS (all 3 tests pass)

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/wildcard_ast.py backend/app/services/matrix_engine.py backend/tests/test_matrix_math.py
git commit -m "feat(matrix): implement exact permutation counting and direct indexing engine"
```

---

### Task 2: Add `/generate/matrix/slice` and update `/generate/matrix/execute` Endpoints (TDD)

**Files:**
- Test: `backend/tests/test_matrix_slice_api.py`
- Modify: `backend/app/api/routers/generate.py`

- [ ] **Step 1: Write API tests in `backend/tests/test_matrix_slice_api.py`**

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_matrix_slice_endpoint():
    res = client.post("/generate/matrix/slice", json={
        "prompt": "photo of {cat|dog} with {hat|sunglasses}",
        "offset": 0,
        "limit": 2,
        "expand_wildcards": True
    })
    assert res.status_code == 200
    data = res.json()
    assert data["total_count"] == 4
    assert len(data["items"]) == 2
    assert data["items"][0]["index"] == 1
    assert data["items"][0]["prompt"] == "photo of cat with hat"
    assert data["items"][1]["index"] == 2
    assert data["items"][1]["prompt"] == "photo of cat with sunglasses"

def test_matrix_slice_sample_mode():
    res = client.post("/generate/matrix/slice", json={
        "prompt": "photo of {cat|dog} with {hat|sunglasses}",
        "sample_size": 2,
        "seed": 123,
        "expand_wildcards": True
    })
    assert res.status_code == 200
    data = res.json()
    assert data["total_count"] == 4
    assert data["is_sample"] is True
    assert len(data["items"]) == 2

def test_matrix_execute_range_and_sample():
    # Test range mode execution
    res = client.post("/generate/matrix/execute", json={
        "prompt": "{a|b|c} {1|2|3}",
        "mode": "range",
        "offset": 2,
        "limit": 3
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "queued"
    assert data["total_generated"] == 3
    assert len(data["prompts"]) == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_matrix_slice_api.py -v`
Expected: FAIL (404 or 422 on `/generate/matrix/slice`)

- [ ] **Step 3: Implement endpoint handlers in `backend/app/api/routers/generate.py`**

Define `MatrixPermutationItem`, `MatrixSliceRequest`, `MatrixSliceResponse`, and update `MatrixExecuteRequest`.
Implement `@router.post("/matrix/slice", response_model=MatrixSliceResponse)` and upgrade `@router.post("/matrix/execute")`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest backend/tests/test_matrix_slice_api.py -v`
Expected: PASS

- [ ] **Step 5: Run full backend test suite to ensure no regressions**

Run: `pytest backend/tests/test_api_endpoints.py backend/tests/test_matrix_safety.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/routers/generate.py backend/tests/test_matrix_slice_api.py
git commit -m "feat(api): add matrix slice and sample endpoints with execution modes"
```

---

### Task 3: Update API Client in Frontend

**Files:**
- Modify: `frontend/src/api.ts`

- [ ] **Step 1: Add types and methods in `frontend/src/api.ts`**

```typescript
export interface MatrixPermutationItem {
  index: number;
  prompt: string;
}

export interface MatrixSliceResponse {
  total_count: number;
  offset: number;
  limit: number;
  is_sample: boolean;
  items: MatrixPermutationItem[];
}

export interface MatrixSliceParams {
  prompt: string;
  offset?: number;
  limit?: number;
  expandWildcards?: boolean;
  sampleSize?: number;
  seed?: number;
  indices?: number[];
}

export async function fetchMatrixSlice(params: MatrixSliceParams): Promise<MatrixSliceResponse> {
  const res = await fetch(`${API_BASE}/generate/matrix/slice`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      prompt: params.prompt,
      offset: params.offset ?? 0,
      limit: params.limit ?? 250,
      expand_wildcards: params.expandWildcards ?? true,
      sample_size: params.sampleSize ?? null,
      seed: params.seed ?? null,
      indices: params.indices ?? null,
    }),
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch matrix slice: ${res.statusText}`);
  }
  return res.json();
}
```

- [ ] **Step 2: Update `executeMatrixSweep` signature to accept execution options**

Support passing `mode`, `offset`, `limit`, `sampleSize`, `indices`, or `prompts`.

- [ ] **Step 3: Verify TypeScript compilation**

Run: `npm --prefix frontend run build` (or `npx tsc --noEmit`)
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/api.ts
git commit -m "feat(frontend): add fetchMatrixSlice and updated executeMatrixSweep in api.ts"
```

---

### Task 4: Build Slice Navigator & Permutation Pagination in Matrix Studio UI

**Files:**
- Modify: `frontend/src/components/editor/WildcardMatrixPanel.tsx`
- Modify: `frontend/src/components/editor/WildcardMatrixPanel.css` (if styling adjustments needed)

- [ ] **Step 1: Replace flat 10,000 array state with Slice state**

Replace:
```typescript
const [combinations, setCombinations] = useState<string[]>([]);
```
With:
```typescript
const [sliceItems, setSliceItems] = useState<MatrixPermutationItem[]>([]);
const [totalCount, setTotalCount] = useState<number>(0);
const [currentOffset, setCurrentOffset] = useState<number>(0);
const [pageSize, setPageSize] = useState<number>(250);
const [isSampleMode, setIsSampleMode] = useState<boolean>(false);
const [sampleCount, setSampleCount] = useState<number>(100);
const [jumpIndexInput, setJumpIndexInput] = useState<string>('');
const [pageInput, setPageInput] = useState<string>('1');
```

- [ ] **Step 2: Implement loadSlice and debounced prompt trigger**

Create a clean `loadSlice(offset, limit, sampleSize)` function that calls `fetchMatrixSlice`.
Replace the old 10,000 call in `handlePreview` and debounced expansion with `loadSlice(0, pageSize)`.

- [ ] **Step 3: Build the Slice Navigator Bar UI**

Render:
- Status display: `Total: ${totalCount.toLocaleString()} Permutations | Viewing #${start} - #${end} of ${totalCount.toLocaleString()}`.
- Page size dropdown: `<select value={pageSize} onChange={...}> <option value="50">50</option> ... </select>`.
- Navigation buttons: `<< First`, `< Prev`, `Page [ input ] of [ totalPages ]`, `Next >`, `Last >>`.
- Direct jump: `Jump to # [ input ] [ Go ]`.
- Sampling controls: `🎲 Sample [ N ] Random [ Sample ]` and `Reset to Sequential`.

- [ ] **Step 4: Update Matrix Cards Grid to render `sliceItems`**

Each card displays `sliceItem.index` (e.g. `Variation #${sliceItem.index}`), score, copy button, and checkbox for selection.

- [ ] **Step 5: Verify build**

Run: `npm --prefix frontend run build`
Expected: PASS with no errors

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/editor/WildcardMatrixPanel.tsx frontend/src/components/editor/WildcardMatrixPanel.css
git commit -m "feat(matrix-ui): integrate slice navigator, pagination, jumping, and random sampling"
```

---

### Task 5: Upgrade Batch Sweep Queue Controls with Range Slice and Sample Modes

**Files:**
- Modify: `frontend/src/components/editor/WildcardMatrixPanel.tsx`

- [ ] **Step 1: Add Queue Mode state and inputs**

Add state:
```typescript
const [queueMode, setQueueMode] = useState<'view' | 'range' | 'sample' | 'all'>('view');
const [queueRangeStart, setQueueRangeStart] = useState<number>(1);
const [queueRangeCount, setQueueRangeCount] = useState<number>(10);
const [queueSampleCount, setQueueSampleCount] = useState<number>(10);
```

- [ ] **Step 2: Update `handleExecuteBatchSweep` to support modes**

If mode is `view`: sends selected cards if any, or visible slice items.
If mode is `range`: calls `executeMatrixSweep` with `mode: 'range', offset: queueRangeStart - 1, limit: queueRangeCount`.
If mode is `sample`: calls `executeMatrixSweep` with `mode: 'sample', sample_size: queueSampleCount`.
If mode is `all`: if `totalCount > 2000`, prompts confirmation dialog before proceeding.

- [ ] **Step 3: Update Queue Bar UI controls in `WildcardMatrixPanel.tsx`**

Provide clean segmented mode buttons (`Current View`, `Range Slice`, `Random Sample`, `All`) and corresponding number inputs.

- [ ] **Step 4: Verify build**

Run: `npm --prefix frontend run build`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/editor/WildcardMatrixPanel.tsx
git commit -m "feat(matrix-queue): add flexible range slice and sample modes to batch queue"
```

---

### Task 6: Verification & End-to-End Testing

**Files:**
- Backend tests: `backend/tests/`
- Frontend build

- [ ] **Step 1: Run all backend tests**

Run: `pytest backend/tests/ -v`
Expected: All tests pass.

- [ ] **Step 2: Verify frontend compilation**

Run: `npm --prefix frontend run build`
Expected: Build succeeds with 0 errors.

- [ ] **Step 3: Test large combinatorial space execution in Python**

Run a verification script testing a template with 1,000,000 permutations to verify count is exact and slice offset 500,000 returns instantaneously.

- [ ] **Step 4: Commit any final polish**

```bash
git commit -m "chore(matrix): finalize verification and cleanups for unlimited matrix studio"
```
