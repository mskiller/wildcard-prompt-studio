# Wildcard Prompt Studio V2

<div align="center">

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%2B%20Vite-61DAFB?style=flat-square&logo=react)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/Language-TypeScript-3178C6?style=flat-square&logo=typescript)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Language-Python%203.10%2B-3776AB?style=flat-square&logo=python)](https://python.org/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL%20%2B%20pgvector-336791?style=flat-square&logo=postgresql)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Deploy-Docker%20Compose-2496ED?style=flat-square&logo=docker)](https://docs.docker.com/compose/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

**An advanced, production-grade AI prompt engineering studio for text-to-image workflows.**

[🚀 Quick Start](#-quick-start) · [📚 Documentation](#-documentation) · [✨ Features](#-features) · [🏗 Architecture](#-architecture)

</div>

---

## Overview

**Wildcard Prompt Studio V2** is a full-stack web application designed for high-throughput AI image generation workflows. It combines a Monaco-based prompt editor, an AST-powered wildcard engine, multi-provider AI optimization, and direct ComfyUI integration into a single coherent studio environment.

Built for power users who need:
- **Systematic prompt exploration** via combinatorial matrix sweeps
- **Model-specific optimization** for Krea 2, ANIMA, and other modern diffusion engines
- **Local-first AI** with seamless cloud fallback (Ollama → KoboldCpp → Gemini → OpenAI)
- **Production workflows** with a full Docker stack including Celery workers and Redis

---

## ✨ Features

### 🎨 Krea 2 Prompt Optimization Studio
- **Faithfulness-First Prompting** — system prompt injection based on official Krea 2 guidelines
- **Model Variant Presets** — specialized optimization for Turbo (speed), Medium (artistic), and Large (photorealistic) variants
- **Buzzword Stripper** — eliminates legacy SD anti-patterns (`8k`, `masterpiece`, `trending on artstation`)
- **Quote Text Helper** — auto-formats text elements for accurate text rendering (e.g., `"OPEN 24 HOURS"`)
- **Side-by-Side Diff Viewer** — compare original vs. optimized prompts with one-click apply

### 🌀 ANIMA Prompt Engineering Studio
- **Hybrid Prompting Engine** — combines Danbooru anime tags with natural language narrative
- **SD Weight Stripper** — removes legacy `(tag:1.3)` syntax incompatible with Qwen encoders
- **Quality Score Injector** — prepends `score_9, score_8, score_7` quality anchors automatically
- **Artist Syntax Formatter** — converts artist references to `@artist_name` format

### 🌳 AST-Based Wildcard & Matrix Engine
- **Full AST Parser** — recursive lexer and parser for complex wildcard syntax
- **Nested & Weighted Choices** — `{a|{b|c}}` nesting and `{3$$optionA|1$$optionB}` probability weights
- **Subdirectory Wildcards** — hierarchical references like `__lighting/studio_lights__`
- **Combinatorial Matrix Sweeps** — Cartesian product generation across all prompt parameters

### ⚡ Hybrid AI Provider Engine
- **Unified Provider Interface** — single API surface over Ollama, KoboldCpp, Gemini, OpenAI, and Anthropic
- **Automatic Fallback Chain** — intelligent priority failover across providers without interrupting requests
- **Local-First Design** — prefers local LLMs (Ollama, KoboldCpp) with cloud APIs as fallback

### 🧠 Async RAG Knowledge Base
- **Vector Embeddings** — `SentenceTransformer`-powered semantic search over your prompt library
- **Non-Blocking Processing** — background thread offloading prevents event loop blocking
- **Knowledge Inspector UI** — browse, query, and inject domain knowledge into generation pipelines

### 🎯 Aesthetic Ranker & Genetic Optimizer
- **Aesthetic Scoring** — rate and rank prompts against target style distributions
- **Genetic Evolution** — evolve high-scoring prompts across generations with mutation and crossover

#### ⛩️ Danbooru Lexicon & Co-occurrence Synergy Engine
- **31,000+ Curated Tags** — categorized into `General`, `Character`, `Copyright`, `Artist`, and `Meta`
- **3.23M Co-Occurrence Graph** — dedicated SQLite B-tree index delivering sub-millisecond (0.22ms) relation lookups
- **Smart Prompt Synergy** — analyzes current prompt text to recommend complementary tags ranked by co-occurrence synergy (e.g., `1girl` → `solo`, `long_hair`, `looking_at_viewer`, `blush`, `smile`)
- **Interactive Co-Occurrence Explorer** — click-to-expand "Frequently Paired With" relationship drawers
- **Direct Prompt Injection** — 1-click append into the Monaco prompt editor buffer
- **PostgreSQL Tag Ingestion** — bulk-import top Danbooru tags directly into the local PostgreSQL ontology

### 🏷️ Intelligent Tag Studio & AST Sanitizer
- **Categorized Tag Palette** — explore 48,000+ active tags filtered by Character, Clothing, Lighting, Style, Camera, Quality/Score, and General
- **Automated AST Tag Extraction** — extracts atomic tags from wildcards on creation, update, and batch import
- **Database Tag Sanitizer** — strips syntax leftovers (`{4::`, `:1.3)`, brackets), deduplicates, and re-classifies categories
- **Tag Resync Tool** — re-parses all registered wildcards via AST to backfill tags and category taxonomies

### 🛡️ System Administration & Database Maintenance Suite
- **Granular Database Cleanup** — selective reset targets for Tags, Wildcards, Prompts, and Gallery
- **Factory Reset Safeguard** — protected full reset requiring explicit `"RESET"` confirmation keyword
- **Foreign Key Integrity** — `ondelete="CASCADE"` on prompt tags and `SET NULL` on gallery images to prevent broken links
- **System Health & Stats** — unified API overview of entity counts across all tables and Danbooru ready state

### 🔌 Real-Time ComfyUI Integration & Discord Sweeps
- **Live WebSocket Bridge** — real-time job status, queue progress, and node execution tracking
- **Batch Dispatch** — send matrix-generated prompt lists directly to ComfyUI workflows
- **Generation Simulator** — debug complex multi-node workflows before submitting heavy render batches
- **Automated Discord Webhooks** — automatically dispatch downloaded sweep images and prompt text to Discord channels upon completion

### 🔄 Civitai Cloud Sync
- **Model Import** — browse and import wildcard files, trigger words, and presets from Civitai
- **Auto Sync** — keep wildcard libraries synchronized with cloud sources

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FRONTEND  (React 18 + Vite + TypeScript)                 │
│                                                                             │
│  ┌─────────────────┐ ┌──────────────────┐ ┌───────────────────────────────┐ │
│  │  Krea2 / ANIMA  │ │ Wildcard Matrix  │ │ Monaco Editor + Tags Studio   │ │
│  │  Studio Panels  │ │ Panel (AST/Sweep)│ │ & Danbooru Co-Occurrence Graph│ │
│  └────────┬────────┘ └────────┬─────────┘ └───────────────┬───────────────┘ │
│           │  Zustand State    │                           │                 │
│           └───────────────────┴───────────────────────────┘                 │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │  REST + WebSocket
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       BACKEND API  (FastAPI)                                │
│                                                                             │
│   /api/v1/ai · /api/v1/wildcards · /api/v1/generate · /api/v1/danbooru      │
│   /api/v1/prompts · /api/v1/tags · /api/v1/comfyui · /api/v1/system         │
│                                                                             │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────────────────┐ │
│  │ Krea2/ANIMA      │ │ Wildcard AST     │ │ Danbooru SQLite Lexicon      │ │
│  │ Optimizer        │ │ Engine + Matrix  │ │ (31k tags, 3.2M co-occurs)   │ │
│  └────────┬─────────┘ └────────┬─────────┘ └──────────────────────────────┘ │
│           │                    │                                            │
│           ▼                    ▼                                            │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │               AI Provider Manager (Fallback Chain)                     │ │
│  │   [Ollama] ──► [KoboldCpp] ──► [Gemini] ──► [OpenAI/Anthropic]        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌──────────────┐ ┌───────────┐ ┌─────────────────────────────────────────┐ │
│  │ Celery Worker│ │  Redis    │ │ PostgreSQL + pgvector                   │ │
│  │ (async tasks)│ │  (broker) │ │ (prompts, embeddings, tags, models)     │ │
│  └──────────────┘ └───────────┘ └─────────────────────────────────────────┘ │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │ WebSocket / HTTP / Webhook
                               ▼
                 ┌───────────────────────────┐
                 │ ComfyUI (ws:8188)         │
                 │ └──► Discord Webhook Bot  │
                 └───────────────────────────┘
```

### Tech Stack

| Layer | Technology |
|---|---|
| Frontend Framework | React 18 + Vite + TypeScript |
| Code Editor | Monaco Editor (`@monaco-editor/react`) |
| State Management | Zustand |
| Animations | Framer Motion |
| Backend Framework | FastAPI (Python 3.10+) |
| Task Queue | Celery + Redis |
| Database | PostgreSQL with pgvector extension |
| Lexicon & Co-occurrence Index | SQLite3 B-tree (sub-millisecond queries) |
| ORM / Migrations | SQLAlchemy + Alembic |
| AI Embeddings | `sentence-transformers` |
| Notifications / Sweeps | Discord Webhook (`httpx`) |
| Deployment | Docker Compose |
| File Watching | Watchdog |


---

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

Run the full stack with a single command:

```bash
git clone https://github.com/mskiller/wildcard-prompt-studio.git
cd wildcard-prompt-studio
docker-compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000/api/v1 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

### Option 2: Local Development

#### Prerequisites
- **Python** 3.10+
- **Node.js** 18+
- **PostgreSQL** with `pgvector` extension (or use Docker for DB only)
- **Redis** (or `redis:alpine` via Docker)

#### Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# Windows:   .\venv\Scripts\Activate.ps1
# Linux/Mac: source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## ⚙️ Environment Variables

Create a `backend/.env` file (see [Setup Guide](docs/SETUP_GUIDE.md) for the full reference):

```ini
# Database
DATABASE_URL=postgresql://wildcard:wildcardpassword@localhost:5432/wildcard_db

# AI Providers (all optional — configure what you have)
OLLAMA_HOST=http://localhost:11434
KOBOLDCPP_HOST=http://localhost:5001/v1
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# ComfyUI
COMFYUI_WS_URL=ws://localhost:8188/ws
COMFYUI_HTTP_URL=http://localhost:8188

# Discord Sweep Webhook (optional)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

---

## 🌿 Wildcard Syntax

The AST-based engine supports the full prompt composition syntax:

```text
# File wildcards
A portrait of a __character/fantasy_hero__ in __places/enchanted_forest__

# Choice expressions
A {red|blue|emerald green|golden} dragon

# Weighted choices  (golden is 5× more likely than obsidian)
A dragon with {5$$golden|3$$silver|1$$obsidian} scales

# Nested choices
A warrior holding a {{silver|golden} sword|{iron|glowing crystal} battleaxe}

# Combining it all
A {2$$dramatic|1$$subtle} portrait of a __character__ in {golden hour|blue hour} light
```

---

## 🧪 Testing

```bash
# Run all backend tests
pytest backend/tests -v

# Run specific test suites
pytest backend/tests/test_krea2_optimizer.py
pytest backend/tests/test_wildcard_ast.py
pytest backend/tests/test_ai_providers.py
```

---

## 📚 Documentation

| Document | Description |
|---|---|
| [User Guide](docs/USER_GUIDE.md) | Complete walkthrough of all studio panels and features |
| [API Documentation](docs/API_DOCUMENTATION.md) | Full reference for all REST API endpoints |
| [Architecture](docs/ARCHITECTURE.md) | Technical deep-dive into backend services and data flow |
| [Setup & Deployment](docs/SETUP_GUIDE.md) | Installation, environment variables, Docker deployment |
| [Krea 2 Guide](docs/KREA2_PROMPTING_GUIDE.md) | Krea 2 prompt optimization best practices |
| [ANIMA Guide](docs/ANIMA_PROMPTING_GUIDE.md) | ANIMA model prompting strategy and syntax rules |
| [Contributing](CONTRIBUTING.md) | Development workflow and contribution guidelines |
| [Changelog](CHANGELOG.md) | Version history and release notes |

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting pull requests.

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/your-feature`)
3. Commit your changes using [Conventional Commits](https://www.conventionalcommits.org/)
4. Push to the branch and open a Pull Request

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
