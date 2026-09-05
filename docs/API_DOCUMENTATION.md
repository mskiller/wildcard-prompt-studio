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

---

## 7. RAG Knowledge & Simulator (`/api/v1/ai/rag` & `/api/v1/simulator`)

- `POST /api/v1/ai/rag/query`: Perform semantic similarity search over stored prompt knowledge vectors.
- `POST /api/v1/simulator/run`: Run simulation of prompt execution flow and inspect node stage timings.

---

## 8. Aesthetic Ranker (`/api/v1/aesthetic`)

- `POST /api/v1/aesthetic/score`: Compute aesthetic quality score for a given prompt string.
- `POST /api/v1/aesthetic/mutate`: Perform genetic mutation sweep to optimize aesthetic prompt score.
