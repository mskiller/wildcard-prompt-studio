# Matrix Sweep Results Space & Gallery Auto-Save Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide an interactive "Generated Sweep Results" section within the Visual AST & Matrix Studio that shows thumbnails for each generated image, opens an enlarged modal lightbox with the prompt displayed below it on click, automatically saves completed images into the application's persistent gallery database, and fixes image serving so images never appear blank.

**Architecture:** 
- Backend background task and sync endpoints in FastAPI track ComfyUI prompt executions, fetch completed output images, save them to disk in `app/static/images/`, and insert them into the `images` table.
- Direct image stream endpoint (`/images/file/{filename}`) and unified `STATIC_IMAGES_DIR` path with Vite `/static` proxy ensure instant, reliable image delivery.
- Frontend `WildcardMatrixPanel.tsx` is equipped with a dedicated results grid, real-time generation polling, and an enlarged modal lightbox with full prompt inspection, download, and copy actions.
- `GalleryView.tsx` is upgraded with the prompt-inclusive lightbox and retroactively populated with the user's 18 test images.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy, SQLite/PostgreSQL, React 18, Vite, TypeScript, Lucide icons.

---

### Task 1: Fix Static Image Directory & Vite Proxy Configuration
- [ ] Unify `STATIC_IMAGES_DIR` in `backend/main.py` and `backend/app/api/routers/images.py` to point to `/app/app/static/images` consistently.
- [ ] Add `/static` proxy configuration in `frontend/vite.config.ts`.
- [ ] Add streaming fallback endpoint in `backend/app/api/routers/images.py` (`GET /file/{filename}`) to serve local images or pull from ComfyUI on-demand if not yet cached.
- [ ] Write unit test for image file serving and fallback in `backend/tests/test_images_api.py`.

### Task 2: Backend Background Sweep Archiver & Retroactive Sync Endpoint
- [ ] Implement `sync_recent_comfy_outputs` function in `backend/app/api/routers/comfyui.py` to scan ComfyUI history (`/history`), extract output image metadata and prompt text, download image bytes, and save to DB `images`.
- [ ] Add `POST /api/v1/comfyui/sync-recent-outputs` endpoint in `comfyui.py`.
- [ ] Update `execute_sweep` in `comfyui.py` to launch background task tracking the queued `prompt_ids` and archiving results automatically as they complete.
- [ ] Write unit tests for `sync-recent-outputs` and sweep archiving in `backend/tests/test_matrix_sweep_dispatcher.py`.

### Task 3: Frontend API Client & Retroactive Sync Integration
- [ ] In `frontend/src/api.ts`:
  - Add `syncRecentComfyOutputs(prefix?: string, limit?: number, baseUrl?: string)` API call.
  - Add typed interface for `SweepResultItem`.
- [ ] Verify build / type definitions with `npx tsc --noEmit`.

### Task 4: In-Studio "Sweep Results Space" in Visual AST & Matrix Studio
- [ ] In `frontend/src/components/editor/WildcardMatrixPanel.tsx`:
  - Add state for `sweepResults` and `selectedLightboxImage`.
  - Add "Generated Sweep Results" section below the batch parameters and permutation grid.
  - Add "Sync from ComfyUI" button to instantly import completed images.
  - Render responsive thumbnail grid showing image preview, seed pill, and prompt snippet.
  - Implement enlarged modal lightbox:
    - High-res image display.
    - Full prompt displayed prominently below the image with syntax styling.
    - Action buttons: Copy Prompt, Download Image, Use in Prompt Editor.
- [ ] Style the results space and enlarged lightbox in `frontend/src/components/editor/WildcardMatrixPanel.css`.

### Task 5: Enhance Main Gallery Lightbox with Full Prompt Display
- [ ] In `frontend/src/components/gallery/GalleryView.tsx`:
  - Update `lightbox-modal` to display the complete prompt content prominently below the enlarged image.
  - Add "Sync from ComfyUI" button to header so users can pull recent runs on demand.
  - Use `/api/v1/images/file/{filename}` or resilient direct src to eliminate blank rectangles.
- [ ] Update `GalleryView.css` for consistent styling with the studio lightbox.

### Task 6: End-to-End Verification & Image Import
- [ ] Run automated backend test suite (`pytest tests/ -v`).
- [ ] Run full frontend build (`npm run build`).
- [ ] Trigger retroactive sync to import the user's 18 generated test images into the database.
- [ ] Verify images render correctly with their exact prompts in both the Matrix Studio results space and the Gallery.
