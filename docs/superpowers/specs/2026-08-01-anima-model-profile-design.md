# Design Specification: ANIMA Model Profile & Anima Studio Panel

## Overview
This document specifies the design for adding **ANIMA** (CircleStone Labs / Comfy Org text-to-image model) support to Wildcard Prompt Studio V2. ANIMA uses a Qwen-based text encoder that thrives on a hybrid prompt structure combining Danbooru tags (for quality, meta, and character attributes) with natural language descriptions (for scene composition, mood, pose, and lighting).

## Architectural Requirements

### 1. Backend Service (`backend/app/services/anima_optimizer.py`)
- **SD Weight Cleaner**: Automatically strips SD weight syntax `(tag:weight)` and `((tag))` $\rightarrow$ `tag`.
- **Quality Score Injector**: Manages standard Anima quality and safety tags (`masterpiece, best quality, score_7, safe`).
- **Artist Syntax Formatter**: Preserves and formats `@artist_name` syntax.
- **3 Style Presets**:
  - `hybrid`: Combines Danbooru tags block with descriptive natural language sentences.
  - `tag_focused`: Structured Danbooru tags for precise metadata and features.
  - `natural_language`: Fluid prose for scene composition and storytelling.
- **Negative Prompt Helper**: Provides standard Anima negative prompt defaults (`worst quality, low quality, score_1, score_2, score_3, artist name, blurry, bad anatomy, extra fingers`).

### 2. Backend Router & Integration
- **Schemas (`backend/app/schemas/ai.py`)**: `AnimaImproveRequest` (prompt, style_preset, add_quality_tags, clean_weights, negative_prompt).
- **Router (`backend/app/api/routers/ai.py`)**: `/api/ai/anima-improve` POST endpoint.
- **Dependency (`backend/app/dependencies.py`)**: `get_anima_optimizer()` singleton.
- **Prompt Chat & Seeds (`backend/app/services/prompt_chat_service.py` & `backend/scripts/seed.py`)**: Includes `'anima'` in model profile registry.

### 3. Frontend Anima Studio Panel (`frontend/src/components/editor/AnimaStudioPanel.tsx` & `.css`)
- **Panel UI**:
  - Raw Prompt Input & Output Preview.
  - Controls: Style Mode Selector (`Hybrid`, `Tag-Heavy`, `Natural Language`), Quality Score Toggle, Weight Cleaning Toggle, Negative Prompt Generator.
  - Quick Actions: Copy, Send to Editor, Send to ComfyUI.
- **Navigation & Store**:
  - `ActiveView` in `useAppStore.ts` includes `'anima'`.
  - Icon & Tab in `Sidebar.tsx`, `App.tsx`, `PromptEditor.tsx`, `ContextPanel.tsx`.
  - `PromptChatDrawer.tsx`: Includes Anima in AI Provider dropdown.
  - `api.ts`: Helper `animaImprovePrompt()`.

## Verification Strategy
- **Unit Tests (`backend/tests/test_anima_optimizer.py`)**: Tests weight cleaning, quality tag injection, style presets, and AI prompt improvement fallback.
- **API Tests (`backend/tests/test_api_endpoints.py`)**: Tests endpoint `/api/ai/anima-improve`.
- **End-to-End Build**: Verify backend pytest and frontend TypeScript build.
