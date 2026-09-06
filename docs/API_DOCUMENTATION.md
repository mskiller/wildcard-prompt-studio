# Wildcard Prompt Studio V2 — API Documentation Reference

The backend API for **Wildcard Prompt Studio V2** is built with **FastAPI**. All API routes are prefixed with `/api/v1`.

---

## Base URLs
- **Local Development**: `http://localhost:8000/api/v1`
- **Docker Production**: `http://localhost:80/api/v1`
- **Interactive Swagger OpenAPI Docs**: `http://localhost:8000/docs`
- **ReDoc API Documentation**: `http://localhost:8000/redoc`

---

## 1. System Health Endpoint

### `GET /health`
Returns the operational status of the FastAPI backend service.

#### Response `200 OK`
```json
{
  "status": "ok"
}
```

---

## 2. AI & Krea 2 Optimizer (`/api/v1/ai`)

### `POST /api/v1/ai/improve`
Optimizes a raw input prompt according to Krea 2 prompt engineering rules and model variant presets.

#### Request Body
```json
{
  "prompt": "a portrait of a cyberpunk girl in a neon city masterpiece 8k",
  "variant": "turbo",
  "provider": "ollama",
  "strip_buzzwords": true,
  "quote_text": true
}
```
- `variant` (string): `"turbo"`, `"medium"`, or `"large"`.
- `provider` (string, optional): `"ollama"`, `"koboldcpp"`, `"gemini"`, `"openai"`, `"anthropic"`, or `"auto"`.

#### Response `200 OK`
```json
{
  "original_prompt": "a portrait of a cyberpunk girl in a neon city masterpiece 8k",
  "improved_prompt": "A cinematic close-up portrait of a cyberpunk girl with glowing crimson cybernetic implants standing in a rain-slicked neon street, vibrant reflections, natural depth of field.",
  "variant": "turbo",
  "provider_used": "ollama",
  "diff": {
    "removed": ["masterpiece", "8k"],
    "added": ["cinematic close-up", "glowing crimson cybernetic implants", "rain-slicked neon street", "vibrant reflections", "natural depth of field"]
  }
}
```

---

### `GET /api/v1/ai/providers`
Lists all supported AI providers and their current connectivity status.

#### Response `200 OK`
```json
[
  {"id": "ollama", "name": "Ollama (Local)", "status": "online", "is_local": true},
  {"id": "koboldcpp", "name": "KoboldCpp (Local)", "status": "offline", "is_local": true},
  {"id": "gemini", "name": "Google Gemini", "status": "configured", "is_local": false},
  {"id": "openai", "name": "OpenAI", "status": "unconfigured", "is_local": false}
]
```

---

## 3. Wildcards & AST Engine (`/api/v1/wildcards`)

### `GET /api/v1/wildcards`
Returns all registered wildcard files and categories. Optimized with lightweight projection by default (`include_content=false`) to prevent high memory consumption when loading large wildcard libraries.

#### Query Parameters
- `include_content` (bool, default: `false`): When `false`, returns lightweight records without loading the full text content or entries arrays into memory.
- `skip` (int, default: 0)
- `limit` (int, default: 10000)

#### Response `200 OK`
```json
[
  {
    "id": 1,
    "filename": "character/fantasy_hero.txt",
    "file_path": "wildcards/character/fantasy_hero.txt",
    "type": "txt",
    "content": "",
    "entries": [],
    "created_at": "2026-09-06T12:00:00",
    "updated_at": "2026-09-06T12:00:00"
  }
]
```

---

### `POST /api/v1/wildcards/parse`
Parses a prompt containing wildcard expressions into an AST tree and returns a sampled output prompt.

#### Request Body
```json
{
  "template": "A {red|blue} dragon holding a {3$$golden|1$$iron} sword in __places/dungeon__"
}
```

#### Response `200 OK`
```json
{
  "sampled_prompt": "A blue dragon holding a golden sword in a subterranean lava cavern",
  "ast_nodes_count": 7,
  "wildcards_resolved": ["places/dungeon"]
}
```

---

### `POST /api/v1/wildcards/batch-delete`
Deletes multiple wildcards in a single atomic transaction.

#### Request Body
```json
{
  "ids": [12, 15, 18]
}
```

#### Response `200 OK`
```json
{
  "ok": true,
  "deleted_count": 3
}
```

---

### `POST /api/v1/wildcards/resync-tags`
Parses all registered wildcards using the AST engine, sanitizes atomic tokens, categorizes them, and syncs them into the tags database.

#### Response `200 OK`
```json
{
  "ok": true,
  "total_tags_found": 1420,
  "new_tags_added": 315,
  "tags_categorized": 512,
  "total_tags_in_db": 48892
}
```

---

### `POST /api/v1/generate/matrix`
Generates a Cartesian product sweep matrix from a template prompt containing wildcard choice nodes.

#### Request Body
```json
{
  "template": "A __style__ portrait of a {warrior|mage} with {blue|green} eyes",
  "max_limit": 50
}
```

#### Response `200 OK`
```json
{
  "total_combinations": 4,
  "prompts": [
    "A oil painting portrait of a warrior with blue eyes",
    "A oil painting portrait of a warrior with green eyes",
    "A oil painting portrait of a mage with blue eyes",
    "A oil painting portrait of a mage with green eyes"
  ]
}
```

---

## 4. Prompts Management (`/api/v1/prompts`)

### `GET /api/v1/prompts`
List saved prompts with optional pagination and tag filtering.

#### Query Parameters
- `limit` (int, default: 20)
- `offset` (int, default: 0)
- `tag` (string, optional)

---

### `POST /api/v1/prompts`
Save a new prompt entry to the library.

#### Request Body
```json
{
  "title": "Cyberpunk Street Portrait",
  "content": "A cyberpunk girl in a rain-slicked street",
  "tags": ["cyberpunk", "portrait", "krea2"]
}
```

---

## 5. Model Profiles (`/api/v1/profiles`)

### `GET /api/v1/profiles`
List target model configuration profiles (Krea 2 Turbo, Krea 2 Medium, Krea 2 Large, SDXL Standard).

---

## 6. ComfyUI Integration (`/api/v1/comfyui`)

### `GET /api/v1/comfyui/status`
Check WebSocket connectivity to target ComfyUI backend server (`ws://localhost:8188`).

### `POST /api/v1/comfyui/queue`
Queue a batch list of expanded prompts into a ComfyUI text node workflow.

### `POST /api/v1/comfyui/execute-sweep`
Dispatches a matrix sweep generation job across ComfyUI with modern resolution controls and optional Discord webhook forwarding.

#### Request Body
```json
{
  "prompts": ["a cyberpunk cat in neon city", "a steampunk fox in forest"],
  "steps": 10,
  "cfg": 1.0,
  "sampler_name": "er_sde",
  "scheduler": "beta",
  "model": "Mklan_Kea2_V1.safetensors",
  "clip": "qwen3-vl-4b-heretic.safetensors",
  "vae": "qwen_image_vae.safetensors",
  "width": 896,
  "height": 1152,
  "base_seed": 42,
  "seed_strategy": "increment",
  "send_to_discord": true,
  "discord_webhook_url": "https://discord.com/api/webhooks/..."
}
```
- `width` (int, default: 896): Target generation width (defaults to modern SDXL/Kea2 standard).
- `height` (int, default: 1152): Target generation height (defaults to modern 896×1152 aspect ratio).
- `seed_strategy` (string): `"increment"` (seed + index), `"fixed"` (same seed for all), or `"random"` (new random seed per prompt).
- `workflow` (dict, optional): Custom ComfyUI JSON graph. Automatically updates `EmptyLatentImage` dimensions to match requested width/height.

#### Response `200 OK`
```json
{
  "queued_count": 2,
  "job_results": [{"prompt_id": "comfy-task-uuid-1"}, {"prompt_id": "comfy-task-uuid-2"}]
}
```

---

## 7. Tags Ontology & Sanitizer (`/api/v1/tags`)

### `GET /api/v1/tags`
Search and list stored prompt tags with optional category filtering and search queries.

#### Query Parameters
- `q` (string, optional): Case-insensitive search query (e.g. `cyberpunk`)
- `category` (string, optional): Domain category filter (`Character`, `Clothing`, `Lighting`, `Style`, `Camera`, `Quality / Score`, `General`)
- `skip` (int, default: 0)
- `limit` (int, default: 100, max: 2000)

---

### `GET /api/v1/tags/categories`
Returns a breakdown of all unique tag categories with tag counts.

#### Response `200 OK`
```json
{
  "total": 48892,
  "categories": [
    {"name": "General", "count": 25610},
    {"name": "Character", "count": 12400},
    {"name": "Clothing", "count": 4810},
    {"name": "Style", "count": 2980},
    {"name": "Lighting", "count": 1820},
    {"name": "Camera", "count": 890},
    {"name": "Quality / Score", "count": 382}
  ]
}
```

---

### `POST /api/v1/tags/sanitize`
Cleans the entire tags database by removing dynamic choice tokens (`{4::`), SD weights (`:1.3)`), control characters, and sentence fragments, deduplicating records, and re-classifying categories.

#### Response `200 OK`
```json
{
  "ok": true,
  "tags_cleaned": 184,
  "tags_deleted": 42,
  "total_remaining": 48892
}
```

---

## 8. Danbooru Lexicon & Co-occurrence Engine (`/api/v1/danbooru`)

### `GET /api/v1/danbooru/stats`
Returns the status, tag counts, co-occurrence edge count, database size, and category distribution of the Danbooru SQLite index.

#### Response `200 OK`
```json
{
  "ready": true,
  "total_tags": 31060,
  "total_cooccurrences": 3236959,
  "db_size_mb": 255.86,
  "categories": [
    {"category": "general", "count": 24759},
    {"category": "character", "count": 3755},
    {"category": "copyright", "count": 2473},
    {"category": "meta", "count": 65},
    {"category": "artist", "count": 8}
  ]
}
```

---

### `GET /api/v1/danbooru/tags`
Search the 31,060 Danbooru tags database.

#### Query Parameters
- `q` (string, optional): Search keyword
- `category` (string, optional): `general`, `character`, `copyright`, `artist`, or `meta`
- `skip` (int, default: 0)
- `limit` (int, default: 100, max: 500)

---

### `GET /api/v1/danbooru/cooccurrences`
Retrieves top complementary tags frequently co-occurring with the specified tag in sub-millisecond query time.

#### Query Parameters
- `tag` (string, required): e.g. `1girl`
- `limit` (int, default: 20)

#### Response `200 OK`
```json
[
  {"tag": "solo", "count": 1824050.0},
  {"tag": "long_hair", "count": 1210400.0},
  {"tag": "breasts", "count": 984020.0},
  {"tag": "looking_at_viewer", "count": 910230.0},
  {"tag": "smile", "count": 870420.0}
]
```

---

### `POST /api/v1/danbooru/recommend`
Analyzes an active prompt string or tag array, queries the co-occurrence graph, and returns top synergistic tags ranked by pairing strength.

#### Request Body
```json
{
  "prompt": "1girl, cyber, glowing",
  "limit": 10
}
```

#### Response `200 OK`
```json
[
  {"tag": "solo", "category": "character", "score": 984.2, "reason": "Pairs with 1girl"},
  {"tag": "looking_at_viewer", "category": "character", "score": 642.0, "reason": "Pairs with 1girl"},
  {"tag": "neon", "category": "general", "score": 412.5, "reason": "Pairs with glowing"}
]
```

---

### `POST /api/v1/danbooru/import-to-tags`
Bulk imports the top most popular Danbooru tags into the PostgreSQL `tags` table with category mapping.

#### Request Body
```json
{
  "limit": 5000
}
```

#### Response `200 OK`
```json
{
  "imported": 4820,
  "already_existing": 180,
  "total_requested": 5000
}
```

---

## 9. System Administration & Maintenance (`/api/v1/system`)

### `GET /api/v1/system/stats`
Returns live entity counts across all PostgreSQL tables and Danbooru service stats.

#### Response `200 OK`
```json
{
  "tags_count": 48892,
  "wildcards_count": 2702,
  "prompts_count": 2,
  "versions_count": 0,
  "images_count": 136,
  "profiles_count": 6,
  "danbooru": {
    "ready": true,
    "total_tags": 31060,
    "total_cooccurrences": 3236959,
    "db_size_mb": 255.86
  }
}
```

---

### `POST /api/v1/system/reset`
Performs selective or complete database cleanup with foreign-key safety.

#### Request Body
```json
{
  "target": "prompts"
}
```
- `target` (string): `"tags"`, `"wildcards"`, `"prompts"`, `"gallery"`, or `"all"`.
- `confirm` (string, optional): Required as `"RESET"` when `target` is `"all"`.

#### Response `200 OK`
```json
{
  "ok": true,
  "target": "prompts",
  "deleted_prompts": 14,
  "deleted_versions": 28,
  "message": "Deleted 14 prompts and 28 versions."
}
```

---

## 10. Gallery Studio & Image Management (`/api/v1/images`)

### `GET /api/v1/images/gallery`
Retrieves gallery images with full-text search, sampler/favorite/rating filters, and multi-mode sorting.

#### Query Parameters
- `search` (string, optional): Search keyword matched against filenames and prompt text.
- `sampler` (string, optional): Filter by sampler name (e.g. `er_sde`, `euler`).
- `is_favorite` (bool, optional): Filter by favorite bookmark status (`true` / `false`).
- `min_rating` (int, optional): Minimum star rating threshold (1–5).
- `sort_by` (string, default: `"newest"`): Sort ordering (`"newest"`, `"oldest"`, `"rating"`, or `"aesthetic_score"`).
- `skip` (int, default: 0)
- `limit` (int, default: 50, max: 100)

#### Response `200 OK`
```json
[
  {
    "id": 14,
    "filename": "MatrixSweep_00014_.png",
    "prompt_id": 8,
    "prompt_content": "A cinematic portrait of a cyberpunk hacker in rain, neon reflections",
    "seed": 420815,
    "cfg_scale": 1.0,
    "steps": 10,
    "sampler_name": "er_sde",
    "width": 896,
    "height": 1152,
    "comfy_workflow_id": null,
    "is_favorite": true,
    "rating": 5,
    "aesthetic_score": 8.42,
    "created_at": "2026-09-06T12:30:00"
  }
]
```

---

### `GET /api/v1/images/file/{filename}`
Streams image file binary (`image/png`) directly. Automatically caches the file locally from ComfyUI if not yet present on local storage.

---

### `GET /api/v1/images/{image_id}`
Returns complete metadata and prompt content for an image. Automatically performs PNG chunk auto-healing if the parent Prompt record is unlinked.

---

### `PATCH /api/v1/images/{image_id}/favorite`
Toggles the favorite bookmark state of the target image.

#### Response `200 OK`
Returns the updated `GalleryItemResponse` with toggled `is_favorite`.

---

### `PATCH /api/v1/images/{image_id}/rating`
Updates the 1–5 star rating for the image.

#### Request Body
```json
{
  "rating": 5
}
```

---

### `POST /api/v1/images/{image_id}/score-aesthetic`
Computes an aesthetic quality score for the image based on its prompt complexity and parameters, updating the `aesthetic_score` field in the database.

---

### `GET /api/v1/images/{image_id}/similar`
Discovers conceptually and visually related image generations using `pgvector` cosine distance over prompt embedding vectors.

#### Query Parameters
- `limit` (int, default: 10, max: 200)

#### Response `200 OK`
```json
[
  {
    "id": 9,
    "filename": "MatrixSweep_00009_.png",
    "prompt_content": "A close-up portrait of a neon android in rain",
    "aesthetic_score": 8.15,
    "rating": 4
  }
]
```

---

### `POST /api/v1/images/batch/delete`
Safely deletes multiple images, purging database rows and removing cached image files from static disk storage.

#### Request Body
```json
{
  "image_ids": [12, 14, 15]
}
```

#### Response `200 OK`
```json
{
  "status": "deleted",
  "deleted_count": 3
}
```

---

### `POST /api/v1/images/batch/index-rag`
Indexes prompt text and generation metadata from selected images directly into the Unified RAG knowledge vault.

#### Request Body
```json
{
  "image_ids": [12, 14],
  "category": "gallery_generations",
  "tags": ["portrait", "cyberpunk"]
}
```

#### Response `200 OK`
```json
{
  "status": "indexed",
  "indexed_count": 2
}
```

---

## 11. Persistent Unified RAG & Vision Intelligence (`/api/v1/ai`)

### `POST /api/v1/ai/rag/search`
Queries the persistent `pgvector` knowledge store using 384-dimensional `all-MiniLM-L6-v2` embeddings.

#### Request Body
```json
{
  "query": "photorealistic lighting and depth of field",
  "top_k": 3,
  "category": "krea2",
  "tag": "lighting"
}
```

#### Response `200 OK`
```json
{
  "query": "photorealistic lighting and depth of field",
  "results": [
    {
      "id": 2,
      "title": "Krea 2 Lighting Best Practices",
      "content": "For Large variant photorealism, specify lens aperture, focal length, and physical light sources...",
      "category": "krea2",
      "tags": ["lighting", "optics", "photorealism"],
      "similarity": 0.892
    }
  ]
}
```

---

### `POST /api/v1/ai/rag/index`
Embeds and stores a new knowledge document into PostgreSQL with `pgvector`.

#### Request Body
```json
{
  "title": "Custom Cinematic Prompting Guide",
  "content": "Use anamorphic lenses, teal and orange rim lighting, and subtle film grain.",
  "category": "style",
  "tags": ["cinematic", "lighting"]
}
```

---

### `GET /api/v1/ai/rag/stats`
Returns system statistics for the persistent vector knowledge base.

#### Response `200 OK`
```json
{
  "total_documents": 28,
  "total_tags": 34,
  "model_name": "all-MiniLM-L6-v2",
  "categories": ["krea2", "anima", "comfyui", "wildcards", "style", "gallery_generations"]
}
```

---

### `GET /api/v1/ai/rag/documents`
Lists stored RAG knowledge documents with optional `query`, `category`, and `tag` filters.

---

### `DELETE /api/v1/ai/rag/documents/{doc_id}`
Deletes a knowledge document and its associated pgvector embedding.

---

### `POST /api/v1/ai/vision/describe`
Analyzes an uploaded image and generates structured prompt descriptions.

#### Form Data
- `file`: Image file binary
- `variant` (string): `"turbo"`, `"medium"`, or `"large"`
- `provider` (string): `"auto"` or specific provider

---

### `POST /api/v1/ai/vision/extract-style`
Extracts visual descriptors (lighting, medium, color palette, camera style) with optional 1-click indexing into RAG.

#### Form Data
- `file`: Image file binary
- `provider` (string): `"auto"`
- `index_rag` (bool, default: `false`): When `true`, automatically formats descriptors and indexes them into the RAG knowledge base under category `"vision"`.

---

### `POST /api/v1/ai/chat-refine`
Conversational prompt refinement assistant with RAG domain grounding.

#### Request Body
```json
{
  "current_prompt": "A cyber girl in rain",
  "user_message": "Make it more dramatic with cinematic lighting and volumetric fog",
  "use_rag": true,
  "provider": "auto"
}
```

---

## 12. Aesthetic Ranker & Simulator (`/api/v1/aesthetic` & `/api/v1/simulator`)

- `POST /api/v1/aesthetic/score`: Compute aesthetic quality score for a prompt string.
- `POST /api/v1/aesthetic/mutate`: Perform genetic mutation sweep to optimize aesthetic prompt score.
- `POST /api/v1/simulator/run`: Run simulation of prompt execution flow and inspect node stage timings.
