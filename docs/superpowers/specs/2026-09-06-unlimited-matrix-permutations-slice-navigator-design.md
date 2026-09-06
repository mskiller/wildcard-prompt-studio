# Unlimited Matrix Permutations & Slice Navigator Design

## Problem Statement
In the **Visual AST & Matrix Studio**, wildcard permutations are currently hard-capped at 10,000 variants (e.g. `expandMatrixPrompt(prompt, 10000)` and `DEFAULT_SAFE_LIMIT = 20000` / `MAX_ALLOWED_LIMIT = 100000` with wildcard slicing in the backend). When working with rich wildcard collections or combinatorial choices (e.g. multiple wildcards with hundreds of tags each), permutations can easily reach tens of thousands or millions. Generating all permutations as a single flat array in memory risks Python memory exhaustion, network timeouts, and browser tab freezes.

Users need:
1. Complete removal of the 10,000 ceiling so templates can scale to millions of permutations.
2. The ability to see the exact total number of permutations mathematically without allocating millions of strings.
3. A flexible navigation system to choose how many prompts to see at once (e.g. 50, 100, 250, 500, 1000) and jump to any page or offset (e.g. #25,000 to #25,100).
4. Flexible batch queueing options allowing users to queue selected cards, the current view window, a custom range slice (e.g. #1,000 to #1,500), or a random sample across the full permutation space.

---

## System Architecture

```
+-----------------------------------------------------------------------------------+
|                           Visual AST & Matrix Studio                             |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | Header: Total 1,450,200 Permutations | Viewing #1,001 - #1,250 of 1,450,200 |  |
|  +-----------------------------------------------------------------------------+  |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | Slice Navigator: [Page Size: 250 v] [<<] [<] Page [5] of 5801 [>] [>>]      |  |
|  | [Jump to # 25000] | [🎲 Sample 100 Random] [Sequential View]                |  |
|  +-----------------------------------------------------------------------------+  |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | Batch Sweep: Mode [View / Selected | Range Slice | Random Sample | All]     |  |
|  | [Queue Selected (15)] / [Queue Range #1000-#1500 (500)]                     |  |
|  +-----------------------------------------------------------------------------+  |
+----------------------------------------+------------------------------------------+
                                         |
                                         | POST /generate/matrix/slice
                                         | { offset, limit, sample_size, indices }
                                         v
+-----------------------------------------------------------------------------------+
|                           Backend (MatrixEngine & AST)                           |
|                                                                                   |
|  1. count_permutations(ast) -> Exact total N (O(nodes) math product/sum)         |
|  2. get_permutation_at_index(ast, k) -> O(depth) direct mixed-radix evaluation    |
|  3. get_matrix_slice(ast, offset, limit) -> returns [offset .. offset+limit]      |
|  4. get_matrix_sample(ast, sample_size, seed) -> uniform random draw across N    |
+-----------------------------------------------------------------------------------+
```

---

## 1. Permutation Math Engine (Backend)

### 1.1 Exact Permutation Count (`count_permutations`)
Calculates the exact total number of combinations $N$ in $O(\text{AST size})$ time without instantiating any strings:
* **`TextNode`**: returns $1$.
* **`ChoiceNode`**: returns the sum of counts of its options: $\sum_{i} \text{count}(\text{option}_i)$.
* **`RootNode`**: returns the product of counts of its children: $\prod_{j} \text{count}(\text{child}_j)$.
* **`WildcardNode`**:
  * When `expand_wildcards = False`: returns $1$.
  * When `expand_wildcards = True`: resolves wildcard entries from dictionary/DB/disk.
    * If entries contain nested wildcards or choices, parses entries and computes their sum.
    * For flat text lines, returns `len(entries)` (or $1$ if empty/missing).

### 1.2 Direct-Indexed Permutation Evaluation (`get_permutation_at_index`)
Evaluates the $k$-th permutation ($k \in [0, N-1]$) in $O(\text{depth})$ without evaluating or iterating over preceding indices:
* **`TextNode`**: returns `node.text`.
* **`ChoiceNode`**:
  * Walk options with counts $C_0, C_1, \dots, C_{m-1}$.
  * Find option $i$ where $\sum_{j=0}^{i-1} C_j \le k < \sum_{j=0}^i C_j$.
  * Recurse into option $i$ with relative index $k_{rel} = k - \sum_{j=0}^{i-1} C_j$.
* **`RootNode`**:
  * Let children have counts $C_0, C_1, \dots, C_{m-1}$.
  * Compute stride for each child: $\text{stride}_i = \prod_{j=i+1}^{m-1} C_j$ (with $\text{stride}_{m-1} = 1$).
  * Coordinate for child $i$: $k_i = (k // \text{stride}_i) \pmod{C_i}$.
  * Evaluate each child at index $k_i$ and concatenate strings.
* **`WildcardNode`**:
  * If expanded, resolves target entry at index $k$ and evaluates.

### 1.3 Slice & Sample Generators
* `get_matrix_slice(prompt, offset, limit, expand_wildcards)`:
  * Computes total $N$. Clamps $\text{offset}$ to $[0, \max(0, N-1)]$ and limit to a safe single-request window (e.g. up to 2,000 items).
  * Evaluates indices $k \in [\text{offset}, \min(\text{offset} + \text{limit}, N))$ directly.
  * Returns exact total count, offset, limit, and permutation items with their original 1-based index numbers.
* `get_matrix_sample(prompt, sample_size, seed, expand_wildcards)`:
  * Computes total $N$. If $N \le \text{sample\_size}$, returns all $N$ permutations.
  * Otherwise, uses `random.Random(seed).sample(range(N), sample_size)` to pick uniformly distributed distinct indices.
  * Evaluates those exact indices directly and returns items labeled with their true index numbers.

---

## 2. API Endpoints (`backend/app/api/routers/generate.py`)

### 2.1 `POST /generate/matrix/slice`
Fetches a slice or sample of permutations with total count metadata:
* **Request (`MatrixSliceRequest`)**:
  ```python
  class MatrixSliceRequest(BaseModel):
      prompt: str
      offset: int = 0
      limit: int = 250
      expand_wildcards: bool = True
      sample_size: Optional[int] = None
      seed: Optional[int] = None
      indices: Optional[List[int]] = None
  ```
* **Response (`MatrixSliceResponse`)**:
  ```python
  class MatrixPermutationItem(BaseModel):
      index: int
      prompt: str

  class MatrixSliceResponse(BaseModel):
      total_count: int
      offset: int
      limit: int
      is_sample: bool = False
      items: List[MatrixPermutationItem]
  ```

### 2.2 `POST /generate/matrix/execute`
Handles queuing prompts for generation:
* **Request (`MatrixExecuteRequest`)**:
  ```python
  class MatrixExecuteRequest(BaseModel):
      prompt: str
      expand_wildcards: bool = True
      mode: str = "view"  # "view" | "range" | "sample" | "indices" | "all"
      offset: Optional[int] = 0
      limit: Optional[int] = 10
      sample_size: Optional[int] = None
      indices: Optional[List[int]] = None
      prompts: Optional[List[str]] = None
  ```
* **Response (`MatrixExecuteResponse`)**:
  ```python
  class MatrixExecuteResponse(BaseModel):
      total_generated: int
      prompts: List[str]
      status: str
  ```

### 2.3 Legacy `POST /generate/matrix`
Maintained for backward compatibility, internally delegating to `get_matrix_slice` with the requested limit (default 250, no arbitrary 10,000 ceiling).

---

## 3. Frontend UI (`WildcardMatrixPanel.tsx`)

### 3.1 State Management
* `totalCount: number`: exact count returned by backend.
* `currentOffset: number`: 0-based offset of current page.
* `pageSize: number`: number of prompts per page (`50`, `100`, `250`, `500`, `1000`).
* `sliceItems: MatrixPermutationItem[]`: active items with their indices and prompts.
* `isSampleMode: boolean`: true if showing a random sample rather than a sequential page.
* `selectedIndices: Set<number>`: indices of selected variants across views.
* `queueMode: 'view' | 'range' | 'sample' | 'all'`: batch sweep queueing mode.
* `queueRangeStart: number`, `queueRangeCount: number`, `queueSampleCount: number`.

### 3.2 UI Components
1. **Permutation Navigator Bar**:
   * Page size select dropdown (`50`, `100`, `250`, `500`, `1000`).
   * Paging controls: `First (<<)`, `Prev (<)`, `Page [ X ] of [ Total Pages ]`, `Next (>)`, `Last (>>)` with keyboard enter support.
   * `Jump to # [ index ]` input and go button.
   * `🎲 Sample [ N ] Random` button and `Sequential View` reset button.
2. **Matrix Cards Grid**:
   * Displays each permutation with its exact global index badge (e.g. `Variation #25,001`).
   * Checkbox to toggle selection for queuing.
   * Token score heatmap pill and prompt copy action.
3. **Batch Sweep Queue Bar**:
   * Mode switcher: `View / Selected`, `Range Slice`, `Random Sample`, `All`.
   * Clear contextual description: e.g. "Queuing 250 variants from range #1,000 to #1,250".
   * Safeguard confirmation modal when queuing > 2,000 variants.

---

## 4. Error Handling & Safeguards
* **Single Request Limit**: Max limit per slice request clamped to 2,000 to prevent payload bloat.
* **Large Numbers**: Numbers formatted with locale strings (e.g. `1,450,200`).
* **Degenerate Syntax / Missing Wildcards**: Gracefully caught, fallback to 1 permutation with literal prompt.
* **Batch Sweep Safety Confirmation**: If queuing more than 2,000 variants at once, requires explicit user confirmation.

---

## 5. Testing Plan
* **Unit Tests (`backend/tests/test_matrix_math.py`)**:
  * Verify `count_permutations` accuracy on text, choice nodes, nested wildcards, and large Cartesian spaces.
  * Verify `get_permutation_at_index` matches exhaustive iteration for small spaces.
  * Verify benchmark: direct indexing at index 1,000,000+ executes in < 1ms.
  * Verify `POST /generate/matrix/slice` with offset, limit, sampling, and explicit indices.
  * Verify `POST /generate/matrix/execute` under range, sample, and view modes.
* **Frontend Verification**:
  * Verify clean TypeScript build (`npm run build`).
  * Test page navigation, changing page sizes, jumping to high indices (#50,000+), sampling 100 random variants, and queuing to ComfyUI.
