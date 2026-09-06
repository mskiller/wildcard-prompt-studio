# Wildcard Prompt Studio V2 — User Guide

Welcome to the **Wildcard Prompt Studio V2 User Guide**. This document provides an in-depth walkthrough of all user interface panels, AI features, wildcard engines, and settings in the studio.

---

## Table of Contents

1. [Introduction & Interface Overview](#1-introduction--interface-overview)
2. [Krea 2 Prompt Optimization Studio](#2-krea-2-prompt-optimization-studio)
   - [Model Variant Presets](#model-variant-presets)
   - [1-Click Optimization Actions](#1-click-optimization-actions)
   - [Side-by-Side Diff Viewer](#side-by-side-diff-viewer)
3. [AST Wildcard Engine & Matrix Sweeps](#3-ast-wildcard-engine--matrix-sweeps)
   - [Wildcard Syntax Reference](#wildcard-syntax-reference)
   - [Nested & Weighted Choices](#nested--weighted-choices)
   - [Combinatorial Matrix Sweeps](#combinatorial-matrix-sweeps)
4. [AI Provider Engine & Fallback Chains](#4-ai-provider-engine--fallback-chains)
   - [Configuring Local LLMs (Ollama / KoboldCpp)](#configuring-local-llms-ollama--koboldcpp)
   - [Configuring Cloud Provider APIs (Gemini, OpenAI, Anthropic)](#configuring-cloud-provider-apis-gemini-openai-anthropic)
   - [Provider Priority Fallback Logic](#provider-priority-fallback-logic)
5. [Persistent Unified RAG Knowledge Base](#5-persistent-unified-rag-knowledge-base)
6. [Aesthetic Ranker & Genetic Optimizer](#6-aesthetic-ranker--genetic-optimizer)
7. [ComfyUI Integration & Generation Simulator](#7-comfyui-integration--generation-simulator)
8. [Civitai Cloud Sync & Dynamic Import](#8-civitai-cloud-sync--dynamic-import)
9. [Settings, Custom Themes & Internationalization (i18n)](#9-settings-custom-themes--internationalization-i18n)
10. [Tag Studio & Danbooru Lexicon Explorer](#10-tag-studio--danbooru-lexicon-explorer)
11. [Collapsible Context Panel & Smart Synergy Recommendations](#11-collapsible-context-panel--smart-synergy-recommendations)
12. [Wildcard Deletion & Management](#12-wildcard-deletion--management)
13. [Database Administration & System Reset in Settings](#13-database-administration--system-reset-in-settings)
14. [Overhauled Gallery Studio & Roundtrip Production Flow](#14-overhauled-gallery-studio--roundtrip-production-flow)
15. [Cross-Tab RAG Controls & Vision Integration](#15-cross-tab-rag-controls--vision-integration)
16. [Matrix Studio Resolution & Permutation Controls](#16-matrix-studio-resolution--permutation-controls)

---

## 1. Introduction & Interface Overview

Wildcard Prompt Studio V2 is structured as a single-page reactive application with a tri-column workflow:

- **Left Sidebar**: Mode navigation (**Prompts**, **Wildcards**, **Krea 2 Studio**, **Matrix Generator**, **RAG Inspector**, **Aesthetic Ranker**, **ComfyUI**, **Settings**).
- **Center Canvas**: Main active workspace panel (e.g., Monaco Prompt Editor with syntax highlighting, visual diff, or matrix sweep grid).
- **Right Context Panel**: Real-time prompt stats, AST tree inspector, tag ontology palette, and live provider status.

---

## 2. Krea 2 Prompt Optimization Studio

Access the **Krea 2 Studio** via the sidebar tab or the action bar inside the Prompt Editor.

### Model Variant Presets

Select the appropriate model variant target to tune AI prompt optimization:

| Variant Preset | Recommended Use Case | Optimization Characteristics |
|---|---|---|
| **Turbo** | Fast, high-impact generations | Direct natural language, conciseness, optimal for rapid 2K rendering. |
| **Medium** | Illustrations & Digital Art | Stylized artistic descriptors (anime, painting, watercolor, concept art). |
| **Large** | Ultra-photorealism & Cinema | Deep camera optics, aperture settings, realistic texture fidelity, natural lighting. |

### 1-Click Optimization Actions

- **Krea 2 Expand**: Sends the active prompt to the AI provider engine with Krea 2 system prompt rules to generate a structured, natural language prompt.
- **Strip Buzzwords**: Scans and removes legacy quality buzzwords (`masterpiece`, `8k`, `trending on artstation`, `hyperdetailed`, `award winning`) that degrade modern diffusion models.
- **Quote Text Helper**: Scans prompt for text rendering targets (e.g. `a neon sign reading open late`) and converts them into explicit quoted format (`a neon sign reading "OPEN LATE"`).

### Side-by-Side Diff Viewer

When prompt optimization completes, the **Diff Viewer** highlights added, deleted, and modified phrases side-by-side:
- **Green Highlights**: Phrases added by Krea 2 optimization.
- **Red Strikethrough**: Removed anti-patterns or redundant terms.
- Click **"Apply to Editor"** to accept changes into your prompt buffer.

---

## 3. AST Wildcard Engine & Matrix Sweeps

### Wildcard Syntax Reference

The V2 engine features a full Abstract Syntax Tree (AST) parser capable of evaluating complex prompt expressions.

#### Basic Wildcards
Reference external text files or database wildcards using double underscores:
```text
A portrait of a __character/fantasy_hero__ in a __places/enchanted_forest__
```

#### Choice Expressions
Generate a random option from a pipe-separated list:
```text
A {red|blue|emerald green|golden} dragon sitting on a cliff
```

#### Weighted Choices
Assign probability weights to choices using the `weight$$` syntax:
```text
A dragon with {5$$golden|3$$silver|1$$obsidian} scales
```
*(Option `golden` is 5x more likely to be selected than `obsidian`)*.

#### Recursive Nested Choices
Combine nested options seamlessly:
```text
A warrior holding a {{silver|golden} sword|{iron|glowing crystal} battleaxe}
```

---

### Combinatorial Matrix Sweeps

Open the **Wildcard Matrix Panel** to perform Cartesian product matrix expansions:
1. Enter a template prompt containing wildcard choices (e.g., `A __style__ painting of a {cat|dog|fox} in {spring|winter}`).
2. Click **"Generate Matrix Sweep"**.
3. View the generated prompt table, export combinations as CSV/JSON, or send the batch directly to ComfyUI for execution.

---

## 4. AI Provider Engine & Fallback Chains

### Configuring Local LLMs (Ollama / KoboldCpp)

In **Settings > AI Providers**:
- **Ollama**: Set Base URL (default: `http://localhost:11434`) and select model (e.g. `llama3`, `mistral`, `qwen2`).
- **KoboldCpp**: Set Base URL (default: `http://localhost:5001/v1`) and optional API key.

### Configuring Cloud Provider APIs (Gemini, OpenAI, Anthropic)

- **Google Gemini**: Enter your Gemini API key and select model (`gemini-1.5-flash` or `gemini-1.5-pro`).
- **OpenAI**: Enter OpenAI API key (`gpt-4o`, `gpt-4o-mini`).
- **Anthropic**: Enter Anthropic API key (`claude-3-5-sonnet`).

### Provider Priority Fallback Logic

Enable **Auto Fallback Chain** in settings. If the primary provider (e.g. local Ollama) is offline or times out, the backend automatically fails over to secondary endpoints (e.g. Gemini API) without interrupting user requests.

---

## 5. RAG Knowledge Base & Inspector

The **RAG Knowledge Inspector** allows semantic grounding for prompt generation:
- **Vector Search**: Search your library of prompt styles, lighting techniques, and artist references using natural language semantic queries.
- **Background Embeddings**: Vector embedding computation runs asynchronously in worker threads (`SentenceTransformer`), keeping response times fast.
- **Context Injection**: Select relevant knowledge nodes to inject directly into Krea 2 optimization prompts.

---

## 6. Aesthetic Ranker & Genetic Optimizer

- **Aesthetic Scoring**: Evaluates prompt compositions against aesthetic quality distributions.
- **Genetic Prompt Optimizer**: Run evolutionary algorithms on prompt populations to discover high-scoring aesthetic variations automatically.

---

## 7. ComfyUI Integration & Generation Simulator

- **WebSocket Connection**: Real-time status reporting for ComfyUI instances (`ws://localhost:8188/ws`).
- **Batch Dispatch**: Send matrix-generated prompt lists directly into your ComfyUI workflow text input nodes.
- **Workflow Simulator**: Step-by-step simulation preview of node workflows for diagnostic verification.

---

## 8. Civitai Cloud Sync & Dynamic Import

- **Civitai Importer**: Browse and import wildcard text files, model trigger words, and prompt presets directly from Civitai.
- **Auto Sync**: Keep wildcard libraries up to date with cloud sources.

---

## 9. Settings, Custom Themes & Internationalization (i18n)

- **UI Themes**: Switch between **Dark (Default)**, **Cyberpunk (Vibrant)**, and **Slate (Light)** color themes.
- **i18n Languages**: Built-in support for **English (EN)**, **Chinese (ZH)**, and **Japanese (JP)**.
- **API Base URL**: Dynamically adjust backend API endpoints (`http://localhost:8000/api/v1` or custom remote server host).
- **Discord Integration**: Configure Discord Webhook URLs for automatic sweep image and prompt dispatch.

---

## 10. Tag Studio & Danbooru Lexicon Explorer

Access the **Tag Studio** by clicking the tag icon on the left navigation sidebar.

### Browsing & Filtering
- **Category Tabs**: Filter between **All**, **Character**, **Clothing**, **Lighting**, **Style**, **Camera**, **Quality / Score**, and **General**, with live counts per category.
- **Fast Search**: Search in real-time across 48,000+ local tags and 31,000+ Danbooru tags.
- **Tag Cards**: Each tag card displays its category badge and usage count.

### Co-occurrence Relationships ("Frequently Paired With")
- Click any tag to open its **Frequently Paired With** relationship drawer.
- View top related Danbooru tags ranked by empirical co-occurrence frequency across millions of anime/art generations.
- Click **"Add to Prompt"** on any card or related tag to append it cleanly to your active Monaco editor buffer.

### Database Tag Sanitizer & Ingestion
- **Sanitize Database**: Strips syntax noise (`{4::`, `:1.3)`, brackets), deduplicates tags, and re-classifies them into semantic categories.
- **Import Danbooru**: Import top Danbooru tags (e.g. top 5,000) directly into your local PostgreSQL tag ontology.
- **Resync Wildcard Tags**: Scans all wildcards and extracts new atomic tags via the AST engine.

---

## 11. Collapsible Context Panel & Smart Synergy Recommendations

### Collapsible Layout
- Click the collapse toggle button (`ChevronRight` / `ChevronLeft`) on the top-right of the **Context Panel** to minimize it, giving maximum screen width to the Monaco Editor or Matrix Sweep grid.
- State is automatically remembered and persisted in your local workspace settings.

### Danbooru Smart Synergy Feed
- When editing prompts in the Monaco editor, the Context Panel automatically analyzes active prompt tokens in real time.
- Displays recommended complementary Danbooru tags ranked by synergy (e.g., typing `1girl, glowing` suggests `solo`, `looking_at_viewer`, `neon`, and `cyberpunk`).
- Click any recommended tag chip to instantly append it to the prompt.

---

## 12. Wildcard Deletion & Management

- **Sidebar Hover-to-Delete**: Hover over any wildcard entry in the sidebar to reveal the delete button. A confirmation modal prevents accidental deletions.
- **Editor Delete Action**: When a wildcard file is open in the Prompt Editor, click the red **Delete Wildcard** button in the top toolbar to remove it from disk and database.
- **Batch Deletion**: Automated support for batch-deleting multiple wildcards via the REST API.

---

## 13. Database Administration & System Reset in Settings

Navigate to **Settings** and scroll down to the **Database Management & Maintenance** section:

### Live Entity Statistics
- Real-time status cards show the count of:
  - **Tags** (active ontology count)
  - **Wildcards** (registered files)
  - **Prompts & Versions**
  - **Gallery Images** (generated outputs)
  - **Danbooru Status** (ready state, total tags, co-occurrences, SQLite DB size)

### Selective Section Reset
- **Reset Tags**: Cleans all user tags while safely removing association links.
- **Reset Wildcards**: Deletes all wildcard records from the database.
- **Reset Prompts**: Deletes saved prompts and version history while preserving all generated gallery images by detaching foreign keys (`SET NULL`).
- **Clear Gallery**: Purges generated image records from the database.

### Protected Factory Reset
- Click **"Factory Reset Database"** to reset all application data back to a clean state.
- **Safety Safeguard**: Requires typing `"RESET"` in uppercase before the action can be executed.

---

## 14. Overhauled Gallery Studio & Roundtrip Production Flow

Access the **Gallery Studio** from the left navigation bar to manage, inspect, and evaluate generated image outputs.

### Filtering, Searching & Sorting
- **Real-Time Search**: Search by full or partial prompt text and image filenames.
- **Sampler Filtering**: Drill down into generations created with specific samplers (e.g. `er_sde`, `euler`, `dpmpp_2m`).
- **Favorites & Star Ratings**: Filter exclusively for favorited images or generations meeting a minimum star rating threshold (1–5 stars).
- **Multi-Mode Sorting**: Sort your collection by **Newest**, **Oldest**, **Rating (Highest First)**, or **Aesthetic Score (Highest First)**.

### Interactive Generation Cards
- Each card provides instant visual feedback with parameter badges:
  - **Seed** chip (e.g., `420815`)
  - **Resolution** chip (e.g., `896×1152`)
  - **Steps & CFG** badges (e.g., `10 steps`, `1.0 cfg`)
  - **Sampler** badge (e.g., `er_sde`)
  - **Aesthetic Quality** rating badge
  - **Interactive 1–5 Star Rating** control
  - **Favorite Bookmark** toggle button

### Floating Batch Actions Bar
- Select multiple images using card checkboxes to reveal the floating action toolbar:
  - **Batch Favorite / Unfavorite**: Bookmark collections in bulk.
  - **Batch Delete**: Safely purges database records and removes corresponding PNG files from local disk storage.
  - **Batch Index to RAG**: Converts image prompts and metadata into structured documents inside the Unified RAG knowledge base.

### Roundtrip Lightbox Modal
- Click any image card to open the **Roundtrip Lightbox**:
  - **High-Resolution Inspection**: View original renders in pristine detail with zoom controls.
  - **Full Metadata Breakdown**: Inspect prompt text, seed, dimensions, sampler, scheduler, and model checkpoints.
  - **1-Click Copy Prompt**: Copy clean prompt text to clipboard.
  - **1-Click Send to Editor**: Loads the exact prompt into the Monaco Prompt Editor buffer to iterate immediately.
  - **1-Click Send to ComfyUI**: Populates ComfyUI dispatch parameters with the image's original settings.
  - **Find Similar Generations**: Queries `pgvector` for other images created with semantically related prompt concepts.

### Side-by-Side A/B Comparison Modal
- Select two images and click **"Compare"** to launch the side-by-side A/B evaluator:
  - Synchronized zoom and pan controls to inspect micro-details and textures.
  - Parameter diff table highlighting differences in seed, steps, sampler, resolution, and prompt wording.

### Automatic Metadata Auto-Healing
- When loading gallery records or creating images, the studio automatically scans local PNG chunks on disk for embedded ComfyUI workflows and generation prompts.
- If database associations were lost or broken, the studio automatically heals prompt linkages and backfills parameter fields without manual user intervention.

---

## 15. Cross-Tab RAG Controls & Vision Integration

The **Persistent Unified RAG System** grounds your prompt engineering across all studio panels.

### Cross-Tab RAG Toggles
- **Krea 2 Studio**: Enable **Use RAG Knowledge** to ground prompt expansions in official Krea 2 model guidelines, optical camera techniques, and composition rules.
- **ANIMA Studio**: Toggle RAG to ground anime prompts in Danbooru synergy pairings, artist stylizations, and Qwen text encoder guidelines.
- **Tags Studio**: Utilize RAG semantic similarity to discover conceptually related tags beyond direct text keyword matching.

### Vision Inspector & Style Extraction
- Upload reference images to the **Vision Inspector** panel.
- **Image Description**: Generates natural language prompts matching the uploaded image.
- **Style Descriptor Extraction**: Automatically isolates camera angle, lighting setup, color palette, and artistic medium.
- **1-Click Index to RAG**: Embed extracted style descriptors directly into your persistent RAG knowledge base for future prompt grounding.

---

## 16. Matrix Studio Resolution & Permutation Controls

The **Wildcard Matrix Panel** provides systematic prompt sweep capabilities with modern defaults and safety guards.

### Modern Resolution Controls
- Defaults to modern **896×1152** resolution (standard for SDXL and Kea2 portrait rendering).
- Explicit **Width** and **Height** number steppers allow customizing aspect ratios before dispatching sweeps.

### Queue Limits & Permutation Picker
- **Queue Limits**: Set safety caps on the maximum number of prompts queued to prevent overwhelming ComfyUI.
- **Permutation Checklist**: Preview generated Cartesian combinations in a table and selectively check or uncheck individual prompts to queue only desired variations.

### OOM Freeze Prevention & High-Performance Listing
- Built-in combinatorial safety limits prevent browser freezes and server out-of-memory errors on massive wildcard combinations.
- Wildcard listings query with `include_content=false` by default, ensuring fast rendering and low latency even with thousands of wildcard files.
- Clicking any wildcard in the sidebar Explorer automatically populates the Monaco Prompt Editor.
