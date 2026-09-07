# Matrix Sweep Custom Save Filename & Subfolder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable user-defined filename prefix and subfolders (e.g. `Prompting\MatrixSweep_Krea2`) in ComfyUI batch parameter sweeps while ensuring 100% compatibility with live results streaming, Discord delivery, and the main Gallery tab.

**Architecture:** Add a `Filename / Prefix` text input in the frontend's "ComfyUI Batch Parameters" bar backed by `localStorage` persistence. Extend `execute-sweep` and `build_default_krea_sweep_workflow` to configure ComfyUI's `SaveImage` node with the resolved prefix. Upgrade `sync-recent-outputs` history matching to be subfolder-aware across slashes/backslashes so newly completed images are immediately recognized and streamed to the UI, cached locally, and posted to Discord.

**Tech Stack:** FastAPI (Python), Pytest, React (TypeScript), ComfyUI API.

---

### Task 1: Backend Workflow & Execution Request Support for `filename_prefix`

**Files:**
- Modify: `backend/app/api/routers/comfyui.py`
- Test: `backend/tests/test_matrix_sweep_dispatcher.py`

- [ ] **Step 1: Write failing tests for `build_default_krea_sweep_workflow` and `execute_sweep` with `filename_prefix`**

Add tests to `backend/tests/test_matrix_sweep_dispatcher.py`:
```python
def test_build_default_krea_sweep_workflow_custom_prefix():
    wf = build_default_krea_sweep_workflow(
        model_name="test_model.safetensors",
        clip_name="test_clip.safetensors",
        vae_name="test_vae.safetensors",
        sampler_name="er_sde",
        scheduler="beta",
        steps=10,
        cfg=1.0,
        seed=42,
        prompt_str="a test prompt",
        filename_prefix="Prompting\\MatrixSweep_Krea2"
    )
    assert "9" in wf
    assert wf["9"]["class_type"] == "SaveImage"
    assert wf["9"]["inputs"]["filename_prefix"] == "Prompting\\MatrixSweep_Krea2"

def test_execute_sweep_with_custom_filename_prefix(client, mock_connector):
    payload = {
        "prompts": ["cyberpunk landscape"],
        "filename_prefix": "MySubfolder/MyPrefix",
        "steps": 15,
        "cfg": 2.0
    }
    response = client.post("/comfyui/execute-sweep", json=payload)
    assert response.status_code == 200
    assert response.json()["queued_count"] == 1
    # Ensure queue_prompt was called with the updated workflow prefix
    assert mock_connector.queue_prompt.called
    wf_passed = mock_connector.queue_prompt.call_args[0][0]
    assert wf_passed["9"]["inputs"]["filename_prefix"] == "MySubfolder/MyPrefix"
```

- [ ] **Step 2: Run pytest to verify the tests fail**

Run: `pytest backend/tests/test_matrix_sweep_dispatcher.py -k "test_build_default_krea_sweep_workflow_custom_prefix or test_execute_sweep_with_custom_filename_prefix" -v`
Expected: FAIL because `build_default_krea_sweep_workflow` does not accept `filename_prefix`.

- [ ] **Step 3: Implement `filename_prefix` parameter in `build_default_krea_sweep_workflow`, `SweepExecutionRequest`, and `execute_sweep`**

In `backend/app/api/routers/comfyui.py`:
1. Update `build_default_krea_sweep_workflow`:
```python
def build_default_krea_sweep_workflow(
    model_name: str,
    clip_name: str,
    vae_name: str,
    sampler_name: str,
    scheduler: str,
    steps: int,
    cfg: float,
    seed: int,
    prompt_str: str,
    is_unet: bool = True,
    width: int = 896,
    height: int = 1152,
    filename_prefix: str = "MatrixSweep_Krea2",
) -> Dict[str, Any]:
...
    wf["9"] = {
        "class_type": "SaveImage",
        "inputs": {
            "filename_prefix": filename_prefix or "MatrixSweep_Krea2",
            "images": ["8", 0]
        }
    }
```
2. Update `SweepExecutionRequest`:
```python
class SweepExecutionRequest(BaseModel):
    ...
    filename_prefix: Optional[str] = "MatrixSweep_Krea2"
```
3. Update `execute_sweep`:
```python
clean_prefix = (req.filename_prefix or "").strip()
resolved_prefix = clean_prefix if clean_prefix else "MatrixSweep_Krea2"
```
Pass `filename_prefix=resolved_prefix` to `build_default_krea_sweep_workflow`.
If `has_custom_workflow`:
```python
for n_id, n_data in wf_copy.items():
    if isinstance(n_data, dict):
        if n_data.get("class_type") in ("SaveImage", "SaveImageWebSocket", "Image Save") or "filename_prefix" in n_data.get("inputs", {}):
            if "inputs" not in n_data or not isinstance(n_data["inputs"], dict):
                n_data["inputs"] = {}
            n_data["inputs"]["filename_prefix"] = resolved_prefix
```

- [ ] **Step 4: Run pytest to verify passing**

Run: `pytest backend/tests/test_matrix_sweep_dispatcher.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/routers/comfyui.py backend/tests/test_matrix_sweep_dispatcher.py
git commit -m "feat(comfyui): add filename_prefix support to sweep workflow builder and execute-sweep"
```

---

### Task 2: Backend Subfolder-Aware History Matcher in `sync_recent_outputs`

**Files:**
- Modify: `backend/app/api/routers/comfyui.py`
- Test: `backend/tests/test_matrix_sweep_dispatcher.py`

- [ ] **Step 1: Write failing test for subfolder-aware history matching**

Add to `backend/tests/test_matrix_sweep_dispatcher.py`:
```python
@pytest.mark.asyncio
async def test_sync_recent_outputs_with_subfolder_prefix(client):
    history_with_subfolder = {
        "prompt-sub-1": {
            "outputs": {
                "9": {
                    "images": [
                        {"filename": "MatrixSweep_Krea2_00001_.png", "subfolder": "Prompting", "type": "output"}
                    ]
                }
            },
            "prompt": [None, None, {
                "4": {"inputs": {"text": "prompt inside prompting subfolder"}},
                "7": {"class_type": "KSampler", "inputs": {"seed": 111, "steps": 10, "cfg": 1.0}}
            }]
        }
    }
    with patch("app.api.routers.comfyui.connector.get_all_history", new_callable=AsyncMock) as mock_hist, \
         patch("app.api.routers.comfyui.connector.get_image", new_callable=AsyncMock) as mock_get_img:
        mock_hist.return_value = history_with_subfolder
        mock_get_img.return_value = b"FAKE_SUBFOLDER_IMAGE_BYTES"

        # Case 1: Match by full prefix with backslash
        res1 = client.post("/comfyui/sync-recent-outputs", json={"prefix": "Prompting\\MatrixSweep_Krea2"})
        assert res1.status_code == 200
        assert res1.json()["imported_count"] == 1
        assert res1.json()["items"][0]["filename"] == "MatrixSweep_Krea2_00001_.png"

        # Case 2: Match by default "MatrixSweep"
        res2 = client.post("/comfyui/sync-recent-outputs", json={"prefix": "MatrixSweep"})
        assert res2.status_code == 200
        assert res2.json()["imported_count"] == 1

        # Case 3: Match by subfolder alone
        res3 = client.post("/comfyui/sync-recent-outputs", json={"prefix": "Prompting"})
        assert res3.status_code == 200
        assert res3.json()["imported_count"] == 1
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest backend/tests/test_matrix_sweep_dispatcher.py -k "test_sync_recent_outputs_with_subfolder_prefix" -v`
Expected: FAIL because `"Prompting\\MatrixSweep_Krea2" in "MatrixSweep_Krea2_00001_.png"` is False.

- [ ] **Step 3: Implement normalized multi-segment matching in `sync_recent_outputs`**

In `backend/app/api/routers/comfyui.py`, replace lines 855-867 with:
```python
    norm_prefix = (prefix or "").replace("\\", "/").strip().lower()
    leaf_prefix = norm_prefix.split("/")[-1] if "/" in norm_prefix else norm_prefix

    all_saved = []
    for pid, data in history.items():
        outputs = data.get("outputs", {})
        has_match = False
        for nid, out in outputs.items():
            if isinstance(out, dict) and "images" in out:
                for im in out["images"]:
                    fn = im.get("filename", "")
                    subfolder = (im.get("subfolder") or "").replace("\\", "/").strip().lower()
                    norm_full = f"{subfolder}/{fn.lower()}" if subfolder else fn.lower()

                    if not norm_prefix:
                        has_match = True
                        break

                    if (
                        norm_prefix in norm_full
                        or leaf_prefix in fn.lower()
                        or (subfolder and norm_prefix in subfolder)
                        or (norm_prefix == "matrixsweep" and "matrixsweep" in fn.lower())
                    ):
                        has_match = True
                        break
        if has_match:
            saved = await process_and_save_comfy_output(pid, data, db, base_url=base_url)
            all_saved.extend(saved)
```

- [ ] **Step 4: Run pytest to verify passing**

Run: `pytest backend/tests/test_matrix_sweep_dispatcher.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/routers/comfyui.py backend/tests/test_matrix_sweep_dispatcher.py
git commit -m "feat(comfyui): support subfolder-aware history matching in sync_recent_outputs"
```

---

### Task 3: Frontend API Contract & Parameter Integration

**Files:**
- Modify: `frontend/src/api.ts`

- [ ] **Step 1: Update `SweepExecuteOptions` and `executeComfyUISweep`**

In `frontend/src/api.ts`:
1. Add `filenamePrefix?: string;` to `SweepExecuteOptions`.
2. In `executeComfyUISweep`, include `filename_prefix: options.filenamePrefix || 'MatrixSweep_Krea2'`:
```ts
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
  scheduler?: string;
  model?: string;
  clip?: string;
  vae?: string;
  width?: number;
  height?: number;
  sendToDiscord?: boolean;
  discordWebhookUrl?: string;
  filenamePrefix?: string;
}
```
And inside `executeComfyUISweep`:
```ts
const payload = {
  ...
  filename_prefix: options.filenamePrefix || 'MatrixSweep_Krea2',
};
```

- [ ] **Step 2: Verify TypeScript compilation**

Run: `npm run build` in `frontend` (or `npx tsc --noEmit`)
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api.ts
git commit -m "feat(frontend): add filenamePrefix to SweepExecuteOptions and executeComfyUISweep"
```

---

### Task 4: Frontend UI in "ComfyUI Batch Parameters" & Real-Time Sync Polling

**Files:**
- Modify: `frontend/src/components/editor/WildcardMatrixPanel.tsx`

- [ ] **Step 1: Add state and `localStorage` persistence**

In `WildcardMatrixPanel.tsx`:
```tsx
const [filenamePrefix, setFilenamePrefix] = useState<string>(
  () => localStorage.getItem('wps_matrix_comfy_filename_prefix') || 'MatrixSweep_Krea2'
);

const handleFilenamePrefixChange = (val: string) => {
  setFilenamePrefix(val);
  localStorage.setItem('wps_matrix_comfy_filename_prefix', val);
};
```

- [ ] **Step 2: Add `Filename / Prefix` input field to `renderComfyUIBatchBar`**

In `renderComfyUIBatchBar` (inside `<div className="batch-controls-row">`, right after Base Seed and before Resolution):
```tsx
{/* Output Filename Prefix / Subfolder */}
<div className="batch-field">
  <label>Filename / Prefix</label>
  <input
    type="text"
    className="batch-input batch-input-text"
    value={filenamePrefix}
    onChange={(e) => handleFilenamePrefixChange(e.target.value)}
    placeholder="e.g. Prompting\MatrixSweep_Krea2"
    title="Choose output filename and optional subfolder (e.g. Prompting\MatrixSweep_Krea2)"
    aria-label="Output filename and subfolder"
  />
</div>
```

- [ ] **Step 3: Update `handleExecuteBatchSweep` to pass `filenamePrefix`**

In `handleExecuteBatchSweep`:
```tsx
const res = await executeComfyUISweep({
  prompts: promptsToSend,
  seedStrategy,
  baseSeed,
  steps,
  cfg,
  samplerName,
  scheduler,
  model,
  clip,
  vae,
  width,
  height,
  sendToDiscord,
  discordWebhookUrl: sendToDiscord ? discordWebhookUrl : undefined,
  filenamePrefix: filenamePrefix.trim() || 'MatrixSweep_Krea2',
});
```
And in the polling interval:
```tsx
const syncRes = await syncRecentComfyOutputs(filenamePrefix.trim() || 'MatrixSweep', 50);
```

- [ ] **Step 4: Run frontend build and type check**

Run: `npm run build` in `frontend`
Expected: Build succeeds with 0 errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/editor/WildcardMatrixPanel.tsx
git commit -m "feat(matrix-ui): add filename and subfolder input to ComfyUI batch parameters bar"
```

---

### Task 5: End-to-End Test Suite Verification

**Files:**
- Test all backend tests: `pytest backend/tests`
- Test all frontend tests / build: `npm test` or `npm run build`

- [ ] **Step 1: Run complete backend test suite**

Run: `pytest backend/tests -v`
Expected: All backend tests pass.

- [ ] **Step 2: Run complete frontend build**

Run: `npm run build` in `frontend`
Expected: Build succeeds cleanly.

- [ ] **Step 3: Final git status check and verification**

Run: `git status`
Confirm clean working tree.
