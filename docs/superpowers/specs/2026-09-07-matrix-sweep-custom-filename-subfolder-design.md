# Design Specification: Matrix Sweep Custom Save Filename & Subfolder

## Context & Overview
In the **Visual AST & Matrix Studio** page under the **ComfyUI Batch Parameters** section, users can configure parameters (model, clip, vae, sampler, scheduler, steps, cfg, seed, resolution) and dispatch batch sweeps into ComfyUI.

Previously, the SaveImage node prefix was hardcoded to `"MatrixSweep_Krea2"`. This document specifies the addition of a user-configurable **Filename / Prefix** input field that allows users to specify both a custom filename prefix and an optional subfolder (e.g. `Prompting\MatrixSweep_Krea2` or `Subfolder/CustomPrefix`).

The design ensures that all existing downstream processes—specifically the **Live Results Gallery** in Matrix Studio, **Discord Webhook dispatch**, and the main **Gallery Tab**—remain fully operational and synchronized.

---

## Requirements & Success Criteria

1. **User Configurable**:
   - Provide a dedicated `Filename / Prefix` text input in the ComfyUI Batch Parameters bar.
   - Default value: `"MatrixSweep_Krea2"`.
   - Placeholder: `e.g. Prompting\MatrixSweep_Krea2`.
   - If the user enters a subfolder path (e.g. `Prompting\MatrixSweep_Krea2` or `Prompting/MatrixSweep_Krea2`), ComfyUI automatically saves outputs into `<output_dir>/Prompting/`.
2. **Session Persistence**:
   - Persist user input in `localStorage` under `wps_matrix_comfy_filename_prefix`.
   - Gracefully fallback to `"MatrixSweep_Krea2"` if empty, whitespace, or unset.
3. **ComfyUI Workflow Integration**:
   - In `build_default_krea_sweep_workflow`, inject the resolved `filename_prefix` into node `"9"` (`SaveImage`).
   - If a custom workflow graph is executed, dynamically update the `filename_prefix` input on any `SaveImage` node.
4. **Live Gallery & History Synchronization**:
   - In `sync_recent_outputs`, support subfolder-aware matching: match against the combined normalized path (`f"{subfolder}/{fn}"`), leaf prefix (`os.path.basename(prefix)`), or fallback `"MatrixSweep"`.
   - In `WildcardMatrixPanel`, pass the active `filenamePrefix` during periodic polling so newly generated images appear in real-time in the Results workspace.
5. **Discord & Gallery Tab Compatibility**:
   - Images downloaded from ComfyUI (via `connector.get_image(fn, subfolder=subfolder)`) are cached in `STATIC_IMAGES_DIR` and linked to the SQLite DB `Image` table.
   - Discord webhook posts continue using the locally cached image file without interruption.
   - Main Gallery tab (`GalleryView.tsx`) continues to display all generated images and syncs recent outputs without regression.

---

## Architectural Details & Data Flow

### 1. Frontend: UI & State (`WildcardMatrixPanel.tsx`)
- **State Initialization**:
  ```ts
  const [filenamePrefix, setFilenamePrefix] = useState<string>(
    () => localStorage.getItem('wps_matrix_comfy_filename_prefix') || 'MatrixSweep_Krea2'
  );
  ```
- **Change Handler**:
  ```ts
  const handleFilenamePrefixChange = (val: string) => {
    setFilenamePrefix(val);
    localStorage.setItem('wps_matrix_comfy_filename_prefix', val);
  };
  ```
- **UI Element**:
  Placed in `renderComfyUIBatchBar` alongside generation parameters:
  ```tsx
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
- **Execution & Polling**:
  - `handleExecuteBatchSweep` passes `filenamePrefix: filenamePrefix.trim() || 'MatrixSweep_Krea2'` to `executeComfyUISweep`.
  - During interval polling:
    ```ts
    const syncRes = await syncRecentComfyOutputs(filenamePrefix.trim() || 'MatrixSweep', 50);
    ```

### 2. API Contract (`frontend/src/api.ts`)
- Add `filenamePrefix?: string;` to `SweepExecuteOptions`.
- Include `filename_prefix: options.filenamePrefix || 'MatrixSweep_Krea2'` in the `POST /comfyui/execute-sweep` payload.

### 3. Backend: Workflow Generation (`backend/app/api/routers/comfyui.py`)
- **Request Model**:
  ```python
  class SweepExecutionRequest(BaseModel):
      ...
      filename_prefix: Optional[str] = "MatrixSweep_Krea2"
  ```
- **Resolution**:
  ```python
  clean_prefix = (req.filename_prefix or "").strip()
  resolved_prefix = clean_prefix if clean_prefix else "MatrixSweep_Krea2"
  ```
- **Default Workflow**:
  `build_default_krea_sweep_workflow` accepts `filename_prefix: str = "MatrixSweep_Krea2"` and configures:
  ```python
  wf["9"] = {
      "class_type": "SaveImage",
      "inputs": {
          "filename_prefix": filename_prefix,
          "images": ["8", 0]
      }
  }
  ```
- **Custom Workflow**:
  When `has_custom_workflow` is True:
  ```python
  for n_id, n_data in wf_copy.items():
      if isinstance(n_data, dict):
          if n_data.get("class_type") == "SaveImage" or "filename_prefix" in n_data.get("inputs", {}):
              n_data["inputs"]["filename_prefix"] = resolved_prefix
  ```

### 4. Backend: History Sync & Matching (`sync_recent_outputs`)
In ComfyUI output history, an image saved with `filename_prefix="Prompting\MatrixSweep_Krea2"` yields:
```json
{
  "filename": "MatrixSweep_Krea2_00001_.png",
  "subfolder": "Prompting",
  "type": "output"
}
```
`sync_recent_outputs` checks matches across path components:
```python
norm_prefix = (prefix or "").replace("\\", "/").strip().lower()
leaf_prefix = norm_prefix.split("/")[-1] if "/" in norm_prefix else norm_prefix

for nid, out in outputs.items():
    if isinstance(out, dict) and "images" in out:
        for im in out["images"]:
            fn = im.get("filename", "")
            subfolder = (im.get("subfolder") or "").replace("\\", "/").strip().lower()
            norm_full = f"{subfolder}/{fn.lower()}" if subfolder else fn.lower()
            
            has_match = (
                not norm_prefix
                or norm_prefix in norm_full
                or leaf_prefix in fn.lower()
                or (subfolder and norm_prefix in subfolder)
                or (norm_prefix == "matrixsweep" and "matrixsweep" in fn.lower())
            )
            if has_match:
                ...
```

### 5. Downstream Compatibility Verification

| Feature | Mechanism | Impact / Compatibility |
| :--- | :--- | :--- |
| **ComfyUI Subfolder Creation** | ComfyUI standard `folder_paths.get_save_image_path` | Works automatically when given `Subfolder\Prefix` or `Subfolder/Prefix`. |
| **Live Gallery (Matrix Studio)** | Polling `syncRecentComfyOutputs` with active prefix | Full path and leaf matching ensures newly completed items stream in immediately. |
| **Discord Webhook** | `_send_image_to_discord` sends `STATIC_IMAGES_DIR / fn` | Unaffected because files are cached locally by filename. |
| **Gallery Tab** | Fetches via `GET /api/v1/images/gallery` and `/file/{filename}` | Unaffected because SQLite records and local static caches use the image filename. |
| **Manual Sync (Gallery Tab)** | Calls `syncRecentComfyOutputs('MatrixSweep', 50)` | Matches both legacy and new sweep outputs. |

---

## Testing & Verification Plan

1. **Unit Tests (`backend/tests/test_matrix_sweep_dispatcher.py`)**:
   - Test default workflow construction with custom prefix (e.g. `Prompting\MatrixSweep_Krea2`).
   - Test `POST /comfyui/execute-sweep` with `filename_prefix`.
   - Test `POST /comfyui/sync-recent-outputs` with subfolders in ComfyUI history items.
2. **Frontend Type Check & Build**:
   - Verify TypeScript compilation without any errors or warnings.
3. **Manual Verification Check**:
   - Verify input field rendering, persistence in `localStorage`, and graceful fallback.
