# Changelog

All notable changes to Wildcard Prompt Studio V2 are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.1.0] - 2026-09-06

### Added

#### Danbooru Lexicon & Co-occurrence Recommendation Engine
- High-performance SQLite B-tree database index (`danbooru_lexicon.db`) mapping 31,060 authentic, high-traffic Danbooru tags and 3,236,959 co-occurrence pairs.
- Sub-millisecond (0.22ms) query engine for finding co-occurring tag pairs and synergistic combinations.
- Real-time Smart Prompt Synergy endpoint (`POST /api/v1/danbooru/recommend`) that parses active prompt tokens and scores complementary Danbooru tags.
- Tag Ingestion endpoint (`POST /api/v1/danbooru/import-to-tags`) with category mapping (`artist`, `character`, `copyright`, `meta`, `general`) to easily import curated vocabularies into PostgreSQL.
- Danbooru Lexicon stats endpoint (`GET /api/v1/danbooru/stats`) and tag search (`GET /api/v1/danbooru/tags`).
- CLI builder script `backend/scripts/build_danbooru_db.py` to compile the co-occurrence CSV into an optimized SQLite index.

#### Intelligent Tag Studio & AST Sanitization
- Tag categorization ontology (`Character`, `Clothing`, `Lighting`, `Style`, `Camera`, `Quality / Score`, `General`) with category counts endpoint (`GET /api/v1/tags/categories`).
- Automated AST Tag Extraction pipeline (`extract_atomic_tags_from_text`): automatically parses wildcards on create, update, and upload to extract clean atomic tags with categories into the database.
- Tag Sanitizer (`POST /api/v1/tags/sanitize`): strips syntax noise, removes dynamic choice prefixes (`{4::`), SD weights (`:1.3)`), control characters, and sentence fragments, deduplicating the library.
- Wildcard Tag Resync (`POST /api/v1/wildcards/resync-tags`): scans all registered wildcards and backfills tags.

#### Database Maintenance & System Administration Suite
- System stats endpoint (`GET /api/v1/system/stats`) reporting live entity counts for tags, wildcards, prompts, versions, images, and model profiles.
- Granular database reset endpoint (`POST /api/v1/system/reset`) supporting selective target clearing: `tags`, `wildcards`, `prompts`, `gallery`, or `all`.
- Protected Factory Reset guarded by explicit `"RESET"` confirmation keyword.
- Database foreign key safeguards: Alembic migration `7b9e11fc3421_fix_prompt_and_image_foreign_keys.py` adding `CASCADE` on `prompt_tags` and `ondelete="SET NULL"` on `images.prompt_id` so deleting prompts preserves gallery images.
- Batch wildcard deletion endpoint (`POST /api/v1/wildcards/batch-delete`).

#### ComfyUI Sweeps & Discord Webhook Integration
- Added Discord Webhook dispatch (`send_to_discord`, `discord_webhook_url`) to `/api/v1/comfyui/execute-sweep`.
- Background task polling automatically forwards rendered images and prompt text to Discord channels upon completion.
- Support for auto-reading webhook URLs from local ComfyUI custom node configs (`ComfyUI-SendToDiscord/config.ini`).

#### Frontend UI Overhauls
- **Redesigned Tag Studio**: Interactive category tabs with live tag counts, instant tag search, co-occurrence drawer ("Frequently Paired With"), and 1-click "Add to Prompt" button.
- **Collapsible Context Panel**: Persistent collapse/expand toggle on the right panel with integrated Danbooru Smart Synergy recommendation feed.
- **Enhanced Settings View**: Dedicated System Maintenance & Database Management card with live entity badges, granular cleanups, and Discord webhook configuration.
- **Wildcard Management**: Hover-to-delete in Sidebar and active wildcard deletion in the Prompt Editor.

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
