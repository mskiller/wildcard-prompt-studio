# Changelog

All notable changes to Wildcard Prompt Studio V2 are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2026-09-05

### Added

#### Backend
- Krea 2 Optimizer Service - model variant presets (Turbo/Medium/Large), buzzword stripping, and text quote formatting
- ANIMA Optimizer Service - hybrid prompting engine with SD weight stripping and quality score injection
- AST Wildcard Engine - full recursive lexer, parser, and evaluator with nested choices, weighted sampling, and matrix sweeps
- AI Provider Manager - unified fallback chain across Ollama, KoboldCpp, Gemini, OpenAI, and Anthropic
- Async RAG Knowledge Base - non-blocking SentenceTransformer vector embeddings with pgvector storage
- ComfyUI Connector - real-time WebSocket bridge for job tracking and batch prompt dispatch
- Aesthetic Ranker - quality scoring with genetic mutation optimizer
- Celery Worker - async background task processing for heavy generation workloads
- Watchdog Service - file system watching for automatic wildcard library updates
- Civitai Sync - cloud wildcard and preset import from Civitai
- Vision Service - image understanding integration
- Full FastAPI REST API with 10 router modules: ai, wildcards, generate, prompts, profiles, comfyui, simulator, aesthetic, images, tags
- PostgreSQL + pgvector database with SQLAlchemy ORM and Alembic migrations
- Docker Compose stack with db, redis, backend, worker, and frontend services

#### Frontend
- Monaco Prompt Editor with syntax-highlighted prompt editing and wildcard autocompletion
- Krea 2 Studio Panel with model variant selection, diff viewer, buzzword stripper, quote helper
- ANIMA Studio Panel with hybrid prompting workflow and quality score injector
- Wildcard Matrix Panel with AST preview and combinatorial sweep grid
- RAG Knowledge Inspector with semantic search over prompt library
- Aesthetic Ranker Panel with genetic prompt optimizer UI
- ComfyUI Panel with real-time WebSocket status and batch dispatch
- Settings Panel with AI provider configuration, theme switching (Dark/Cyberpunk/Slate), i18n
- Internationalization - English, Chinese (ZH), and Japanese (JP) locale support
- Zustand state management with usePromptStore and useSettingsStore
- Framer Motion animations
- Lucide React icon set

---

## [1.0.0] - Initial Release

- Basic wildcard text expansion with string-replacement engine
- Simple React frontend with plain text editor
- FastAPI backend with SQLite storage
