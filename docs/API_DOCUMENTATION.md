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
Returns all registered wildcard files and categories in hierarchical tree format.

#### Response `200 OK`
```json
{
  "categories": [
    {
      "name": "character",
      "files": ["fantasy_hero.txt", "cyberpunk_hacker.txt"]
    },
    {
      "name": "lighting",
      "files": ["studio_lights.txt", "cinematic_sunlight.txt"]
    }
  ]
}
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
Dispatches a matrix sweep generation job across ComfyUI with optional Discord webhook forwarding.

#### Request Body
```json
{
  "prompts": ["a cyberpunk cat in neon city", "a steampunk fox in forest"],
  "steps": 25,
  "cfg": 7.0,
  "sampler": "euler",
  "scheduler": "beta",
  "model": "Mklan_Kea2_V1.safetensors",
  "send_to_discord": true,
  "discord_webhook_url": "https://discord.com/api/webhooks/..."
}
```

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

## 10. RAG Knowledge & Simulator (`/api/v1/ai/rag` & `/api/v1/simulator`)

- `POST /api/v1/ai/rag/query`: Perform semantic similarity search over stored prompt knowledge vectors.
- `POST /api/v1/simulator/run`: Run simulation of prompt execution flow and inspect node stage timings.

---

## 11. Aesthetic Ranker (`/api/v1/aesthetic`)

- `POST /api/v1/aesthetic/score`: Compute aesthetic quality score for a given prompt string.
- `POST /api/v1/aesthetic/mutate`: Perform genetic mutation sweep to optimize aesthetic prompt score.
