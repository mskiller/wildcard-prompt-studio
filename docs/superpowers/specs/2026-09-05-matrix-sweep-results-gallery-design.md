# Matrix Sweep Results Space & Gallery Auto-Save Design Specification

**Date:** 2026-09-05  
**Topic:** Visual AST & Matrix Studio Sweep Results Space and Persistent Gallery Archival

## 1. Executive Summary
During matrix permutation sweeps (e.g. 18 variants generated via Krea 2), images were dispatched to ComfyUI and rendered to disk, but the application lacked an in-studio visual space to display and inspect them with their generating prompts. Furthermore, generated images were not automatically persisted into the application's gallery database, and the existing gallery suffered from broken image serving paths due to missing `/static` proxy configuration and uncoordinated static directories.

This specification details:
1. An integrated **Sweep Results Space** within the Visual AST & Matrix Studio (`WildcardMatrixPanel.tsx`) with interactive thumbnail cards, live status indicators, and an enlarged modal lightbox that prominently displays the image and the exact generating prompt underneath it.
2. An automated **Background Sweeper Archiver** in the backend that monitors queued ComfyUI jobs, downloads finished image bytes, saves them to persistent static storage (`app/static/images/`), and records their metadata and full prompt strings in the `images` database table.
3. A retroactive **ComfyUI History Sync** endpoint (`/comfyui/sync-recent-outputs`) that immediately imports recent `MatrixSweep` generations (including the user's recent 18 images) into the gallery.
4. Robust **Static Image Serving & Vite Proxy Fixes** ensuring `/static/images/` loads flawlessly across both the in-studio results space and the main Generated Images Gallery.

---

## 2. Architecture & Components

```
┌─────────────────────────────────────────────────────────────┐
│                 Frontend (React + Vite)                     │
│                                                             │
│  WildcardMatrixPanel.tsx                                    │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ AST Canvas & Permutations Grid                        │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ ComfyUI Batch Parameters Bar                          │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ ★ Generated Sweep Results Space                       │  │
│  │   - Thumbnail grid (18 images)                        │  │
│  │   - Status badges (Generating / Complete)             │  │
│  │   - Sync from ComfyUI button                          │  │
│  │   - Lightbox Modal: Enlarged Image + Prompt Below     │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  GalleryView.tsx                                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Fixed /static proxy, thumbnail grid, enlarged lightbox│  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP / WS (/api/v1/comfyui/...)
┌─────────────────────────▼───────────────────────────────────┐
│                 Backend (FastAPI + SQLAlchemy)              │
│                                                             │
│  comfyui.py                                                 │
│  - POST /execute-sweep: Queues jobs, tracks prompt_ids      │
│  - Background Task: Polls ComfyUI /history, downloads PNGs, │
│    saves to app/static/images/, inserts into DB images      │
│  - POST /sync-recent-outputs: Scans ComfyUI history to      │
│    import existing matrix sweep images retroactive to DB    │
│                                                             │
│  images.py                                                  │
│  - GET /file/{filename}: Direct binary image stream fallback│
│  - Consistent STATIC_IMAGES_DIR path matching main.py       │
│                                                             │
│  SQLite/Postgres DB (images table)                          │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP (:8188)
┌─────────────────────────▼───────────────────────────────────┐
│                 Live ComfyUI Instance                       │
│  - /prompt (Queue)                                          │
│  - /history (Job status & output filenames)                 │
│  - /view (Image binary download)                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Data Models & API Contracts

### 3.1 Backend Router: `/api/v1/comfyui/sync-recent-outputs`
- **Method:** `POST`
- **Query / Body Params:** `prefix: Optional[str] = "MatrixSweep"`, `limit: int = 50`, `base_url: Optional[str] = None`
- **Response:**
  ```json
  {
    "imported_count": 18,
    "items": [
      {
        "id": 19,
        "filename": "MatrixSweep_Krea2_00003_.png",
        "prompt_content": "a cyberpunk cat in a neon city",
        "seed": 42,
        "steps": 10,
        "cfg_scale": 1.0,
        "sampler_name": "er_sde"
      }
    ]
  }
  ```

### 3.2 Backend Router: `/api/v1/images/file/{filename}`
- Direct fallback streaming endpoint: checks local static storage; if missing, requests from ComfyUI via connector, caches locally, and returns `image/png` Response.

### 3.3 Frontend Component State (`WildcardMatrixPanel.tsx`)
- `sweepResults: Array<{ id?: number; filename: string; prompt: string; seed?: number; status: 'queued' | 'rendering' | 'completed' | 'error'; url: string }>`
- `isSyncingOutputs: boolean`
- `activeLightboxResult: SweepResultItem | null`

---

## 4. UI/UX Specifications

### 4.1 In-Studio Sweep Results Space
- Renders directly below the batch parameters / permutations area.
- Header contains:
  - Title: `Generated Sweep Results ({count})`
  - Subtitle or progress indicator (e.g. `18 / 18 completed`)
  - `Sync from ComfyUI` button with refresh icon
  - `Clear Results` button
- Grid layout: responsive CSS grid (`repeat(auto-fill, minmax(180px, 1fr))`) with 1:1 square preview tiles.
- Card contents:
  - Rendered image thumbnail with hover zoom.
  - Overlay gradient with seed pill (`#42`), step pill (`10`), and prompt snippet.
  - Status indicator (pulse animation while generating, checkmark when done).

### 4.2 Enlarged Modal Lightbox
- Triggered by clicking any result card or gallery card.
- Modal overlay covering viewport with darkened backdrop blur.
- Centered container:
  - Top: Close button (`X`), image title/filename.
  - Middle: High-resolution enlarged image display (`max-height: 70vh`, preserved aspect ratio).
  - Bottom: Prompt display box with syntax highlighting/styling:
    - Complete prompt text in a readable font.
    - Quick Action Bar:
      - `Copy Prompt` button with copied checkmark feedback.
      - `Download Image` button saving the PNG locally.
      - `Use in Prompt Editor` button setting prompt in global store.
  - Left / Right chevron buttons to navigate between batch items.

### 4.3 Main Gallery View Improvements
- `/static` route added to `vite.config.ts` proxy.
- `STATIC_IMAGES_DIR` path unified between `main.py` and `images.py`.
- Lightbox updated to include prompt text below enlarged image.
