# Stability Patches & Bug Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 6 identified frontend, backend, and testing bugs to ensure clean console logs, stable ComfyUI streaming, proper error propagation, and passing test suites.

**Architecture:** Proper lifecycle and model disposal management in React/Monaco; resilient HTTP status propagation in FastAPI ComfyUI connector; WebSocket connection state safety guards; Vite static asset branding; Pytest async/respx dependencies and unit test mocking.

**Tech Stack:** FastAPI, httpx, React 18, TypeScript, Monaco Editor, Vite, Pytest, respx, Docker.

---

### Task 1: Monaco DiffEditor Disposal Fix

**Files:**
- Modify: `frontend/src/components/editor/DiffViewer.tsx:1-44`

- [ ] **Step 1: Update DiffViewer with proper model cleanup on unmount**

In `frontend/src/components/editor/DiffViewer.tsx`, acquire the `diffEditor` instance in `onMount` and safely set original and modified models to `null` on unmount to prevent Monaco's `TextModel got disposed before DiffEditorWidget model got reset` error:

```tsx
import React, { useEffect, useRef } from 'react';
import { DiffEditor, useMonaco } from '@monaco-editor/react';
import { setupMonacoEnvironment } from './monacoConfig';

interface DiffViewerProps {
  original: string;
  modified: string;
}

export const DiffViewer: React.FC<DiffViewerProps> = ({ original, modified }) => {
  const monaco = useMonaco();
  const diffEditorRef = useRef<any>(null);

  useEffect(() => {
    if (monaco) {
      setupMonacoEnvironment(monaco);
    }
  }, [monaco]);

  useEffect(() => {
    return () => {
      if (diffEditorRef.current) {
        try {
          diffEditorRef.current.setModel({ original: null, modified: null });
        } catch (e) {
          // Model already disposed
        }
      }
    };
  }, []);

  const handleDiffMount = (editor: any) => {
    diffEditorRef.current = editor;
  };

  return (
    <div className="glass-panel" style={{ width: '100%', height: '100%', minHeight: '300px', display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: '8px' }}>
      <DiffEditor
        height="100%"
        width="100%"
        language="prompt-lang"
        theme="prompt-dark"
        original={original}
        modified={modified}
        onMount={handleDiffMount}
        options={{
          automaticLayout: true,
          minimap: { enabled: false },
          fontSize: 13,
          fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
          lineHeight: 1.5,
          renderSideBySide: true,
          readOnly: true,
          wordWrap: 'on',
          scrollBeyondLastLine: false,
          padding: { top: 12 }
        }}
      />
    </div>
  );
};
```

- [ ] **Step 2: Verify TypeScript compilation**

Run: `docker exec wildcard-prompt-studio-frontend-1 npm run build`
Expected: Build passes with no TypeScript errors.

---

### Task 2: ComfyUI Image View 404 Propagation (Fix HTTP 500 on Missing Files)

**Files:**
- Modify: `backend/app/services/comfyui_connector.py:169-183`
- Modify: `backend/app/api/routers/comfyui.py:38-53`
- Test: `backend/tests/test_comfyui_connector.py`

- [x] **Step 1: Write unit test for missing image 404 handling**

In `backend/tests/test_comfyui_connector.py`, add a test verifying that `get_image` raises `FileNotFoundError` on 404 rather than generic `ConnectError`:

```python
import pytest
import respx
import httpx
from app.services.comfyui_connector import ComfyUIConnector

@pytest.mark.asyncio
@respx.mock
async def test_get_image_404_raises_filenotfound():
    connector = ComfyUIConnector(default_url="http://host.docker.internal:8188")
    respx.get("http://host.docker.internal:8188/view").respond(status_code=404)
    respx.get("http://localhost:8188/view").respond(status_code=404)
    respx.get("http://127.0.0.1:8188/view").respond(status_code=404)

    with pytest.raises(FileNotFoundError):
        await connector.get_image("nonexistent_preview.png")
```

- [x] **Step 2: Update `comfyui_connector.py` to recognize 404**

In `backend/app/services/comfyui_connector.py:169-183`:

```python
    async def get_image(self, filename: str, folder_type: str = "output", subfolder: str = "", base_url: Optional[str] = None) -> bytes:
        target_url = base_url or self.default_url
        candidates = get_url_candidates(target_url, default_port=8188)
        last_exc = None
        for candidate in candidates:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{candidate}/view", params={"filename": filename, "subfolder": subfolder, "type": folder_type})
                    if response.status_code == 404:
                        raise FileNotFoundError(f"Image '{filename}' not found in ComfyUI ({candidate})")
                    response.raise_for_status()
                    return response.content
            except FileNotFoundError:
                raise
            except Exception as e:
                last_exc = e
                continue
        raise httpx.ConnectError(f"Failed to fetch image from ComfyUI at {target_url}: {str(last_exc)}")
```

- [x] **Step 3: Update `backend/app/api/routers/comfyui.py` to return 404 for missing image**

In `backend/app/api/routers/comfyui.py:38-53`:

```python
@router.get("/image/{filename}")
async def get_image(filename: str, folder_type: str = "output", subfolder: str = "", base_url: Optional[str] = None):
    try:
        content = await connector.get_image(filename, folder_type=folder_type, subfolder=subfolder, base_url=base_url)
        return Response(content=content, media_type="image/png")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/view")
async def view_image(filename: str, type: str = "output", subfolder: str = "", base_url: Optional[str] = None):
    try:
        content = await connector.get_image(filename, folder_type=type, subfolder=subfolder, base_url=base_url)
        return Response(content=content, media_type="image/png")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

- [x] **Step 4: Run test to verify it passes**

Run: `docker exec wildcard-prompt-studio-backend-1 pytest tests/test_comfyui_connector.py -k test_get_image_404_raises_filenotfound -v`
Expected: PASS.

---

### Task 3: ComfyUI Live WebSocket Premature Termination Loop Fix

**Files:**
- Modify: `frontend/src/components/editor/ComfyUILiveStream.tsx:204-354`

- [ ] **Step 1: Decouple `gallery` from connection effect & guard WebSocket unmount state**

In `frontend/src/components/editor/ComfyUILiveStream.tsx`:
1. Keep a `galleryRef` updated so `gallery` is not in the `useEffect` dependency array:
```tsx
  const galleryRef = useRef(gallery);
  useEffect(() => {
    galleryRef.current = gallery;
  }, [gallery]);
```
2. Replace lines 303-305:
```tsx
  if (!galleryRef.current.includes(finalImgUrl)) {
    updateSetting('gallery', [finalImgUrl, ...galleryRef.current]);
  }
```
3. Update cleanup in `useEffect` (lines 341-353):
```tsx
    return () => {
      isMounted = false;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (ws) {
        ws.onopen = null;
        ws.onclose = null;
        ws.onerror = null;
        ws.onmessage = null;
        if (ws.readyState === WebSocket.OPEN) {
          ws.close();
        } else if (ws.readyState === WebSocket.CONNECTING) {
          ws.onopen = () => {
            try { ws.close(); } catch (_) {}
          };
        }
        ws = null;
      }
    };
  }, [comfyUIUrl]); // Removed gallery from dependencies
```

- [ ] **Step 2: Verify frontend build**

Run: `docker exec wildcard-prompt-studio-frontend-1 npm run build`
Expected: Clean build without errors.

---

### Task 4: Favicon & Static Asset Creation

**Files:**
- Create: `frontend/public/favicon.svg`
- Modify: `frontend/index.html:1-13`

- [ ] **Step 1: Create modern SVG favicon**

Create `frontend/public/favicon.svg` with a vibrant prompt/sparkle icon matching the app theme:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#6366f1" />
      <stop offset="100%" stop-color="#a855f7" />
    </linearGradient>
  </defs>
  <rect width="32" height="32" rx="8" fill="#0e1118" />
  <path d="M16 4L18.5 11.5L26 14L18.5 16.5L16 24L13.5 16.5L6 14L13.5 11.5Z" fill="url(#grad)" />
  <circle cx="23" cy="8" r="2" fill="#38bdf8" />
</svg>
```

- [ ] **Step 2: Add favicon link to `frontend/index.html`**

In `frontend/index.html`:
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <title>Wildcard Management Studio</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

---

### Task 5: Backend Test Dependencies & Unit Test Mocking

**Files:**
- Modify: `backend/requirements.txt:1-17`
- Modify: `backend/pytest.ini`
- Modify: `backend/tests/test_ai_endpoints.py:1-20`

- [ ] **Step 1: Add missing test dependencies to `backend/requirements.txt`**

Append:
```text
pytest-asyncio>=0.23.0
respx>=0.21.1
```

- [ ] **Step 2: Configure `backend/pytest.ini` with auto asyncio mode**

In `backend/pytest.ini`:
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
```

- [ ] **Step 3: Update `backend/tests/test_ai_endpoints.py` to mock `improve_prompt`**

```python
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@patch("app.api.routers.ai.improve_prompt", new_callable=AsyncMock)
def test_improve_prompt(mock_improve):
    mock_improve.return_value = "A cute cat, cinematic lighting, 8k resolution, photorealistic"
    response = client.post(
        "/api/v1/ai/improve",
        json={"prompt": "A cute cat", "target_model": "stable-diffusion-xl"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "improved_prompt" in data
    assert data["improved_prompt"] == "A cute cat, cinematic lighting, 8k resolution, photorealistic"
    mock_improve.assert_called_once()
```

- [ ] **Step 4: Install dependencies in backend container and execute pytest**

Run:
```bash
docker exec wildcard-prompt-studio-backend-1 pip install pytest-asyncio respx
docker exec wildcard-prompt-studio-backend-1 pytest tests/test_ai_endpoints.py tests/test_ai_providers.py -v
```
Expected: All tests pass synchronously and quickly.

---

### Task 6: UI Responsiveness & Explorer Polish

**Files:**
- Modify: `frontend/src/components/editor/PromptChatDrawer.css:477-505`
- Modify: `frontend/src/components/layout/Sidebar.tsx:175-185, 235-245`

- [ ] **Step 1: Fix select text clipping in `PromptChatDrawer.css`**

In `frontend/src/components/editor/PromptChatDrawer.css`:
```css
.controls-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px 12px;
  font-size: 11px;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.control-group label {
  color: var(--fg-secondary);
  font-weight: 500;
  white-space: nowrap;
}

.control-group select {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 5px;
  background: rgba(30, 35, 48, 0.8);
  border: 1px solid var(--glass-border);
  color: var(--fg-primary);
  outline: none;
  min-width: 95px;
}
```

- [ ] **Step 2: Add fallback prompt display label in `Sidebar.tsx`**

In `frontend/src/components/layout/Sidebar.tsx`:
Change `<span>{p.name}</span>` in both prompt lists to:
```tsx
<span>{p.name?.trim() || p.filename?.trim() || (p.content ? p.content.slice(0, 24) + '...' : 'Untitled Prompt')}</span>
```

- [ ] **Step 3: Collapse secondary sidebar for full-screen tool views**

In `frontend/src/components/layout/Sidebar.tsx`:
```tsx
const SIDEBAR_VIEWS: ViewType[] = ['explorer', 'prompts', 'wildcards', 'tags'];
const showSubSidebar = SIDEBAR_VIEWS.includes(activeView);

return (
  <div className="sidebar-container">
    <div className="activity-bar">
      {/* ... activity items ... */}
    </div>
    {showSubSidebar && (
      <div className="sidebar">
        {renderSidebarContent()}
      </div>
    )}
  </div>
);
```

- [ ] **Step 4: Verify UI in browser**

Reload `http://localhost:5173/` and verify:
- No console errors on navigation.
- Favicon renders in browser tab.
- Prompt selector shows `"KoboldCPP"` fully.
- Switching to ComfyUI / Matrix Sweep / AST Simulator gives full canvas width without empty column.
