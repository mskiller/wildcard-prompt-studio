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
5. [RAG Knowledge Base & Inspector](#5-rag-knowledge-base--inspector)
6. [Aesthetic Ranker & Genetic Optimizer](#6-aesthetic-ranker--genetic-optimizer)
7. [ComfyUI Integration & Generation Simulator](#7-comfyui-integration--generation-simulator)
8. [Civitai Cloud Sync & Dynamic Import](#8-civitai-cloud-sync--dynamic-import)
9. [Settings, Custom Themes & Internationalization (i18n)](#9-settings-custom-themes--internationalization-i18n)

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
