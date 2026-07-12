# Phase 1: Architecture Scaffolding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish the foundational Docker Compose architecture, PostgreSQL database (with pgvector), Redis, FastAPI backend skeleton, and React frontend skeleton.

**Architecture:** We will set up a Docker Compose environment with 4 core services: `db` (pgvector), `redis`, `backend` (FastAPI), and `frontend` (Vite/React). We will configure the backend to connect to the database and Redis, and verify the connections.

**Tech Stack:** Docker Compose, PostgreSQL (pgvector), Redis, Python 3, FastAPI, Node.js, React, Vite, Pytest.

---

### Task 1: Project Initialization & Infrastructure Checks

**Files:**
- Create: `docker-compose.yml`
- Create: `tests/test_infrastructure.py`
- Create: `requirements.txt`
- Create: `pytest.ini`

- [ ] **Step 1: Write the failing test for infrastructure**

```python
# tests/test_infrastructure.py
import socket

def test_postgres_port_open():
    """Verify PostgreSQL is running and port 5432 is open."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 5432))
    assert result == 0, "PostgreSQL port 5432 is not open"
    sock.close()

def test_redis_port_open():
    """Verify Redis is running and port 6379 is open."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 6379))
    assert result == 0, "Redis port 6379 is not open"
    sock.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_infrastructure.py -v`
Expected: FAIL (ConnectionRefusedError or assertion failure because docker-compose isn't running)

- [ ] **Step 3: Write minimal implementation (docker-compose.yml)**

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: ankane/pgvector:latest
    environment:
      POSTGRES_USER: wildcard
      POSTGRES_PASSWORD: wildcardpassword
      POSTGRES_DB: wildcard_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U wildcard -d wildcard_db"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

- [ ] **Step 4: Run test to verify it passes**

Run: `docker compose up -d db redis`
Run: `pytest tests/test_infrastructure.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git init
git add docker-compose.yml tests/test_infrastructure.py
git commit -m "feat: add docker-compose infrastructure for db and redis"
```

### Task 2: Backend FastAPI Skeleton

**Files:**
- Create: `backend/main.py`
- Create: `backend/requirements.txt`
- Create: `backend/Dockerfile`
- Modify: `docker-compose.yml:25-35`
- Create: `tests/test_backend_api.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_backend_api.py
import requests

def test_backend_health():
    """Verify the backend health endpoint returns 200 OK."""
    response = requests.get("http://127.0.0.1:8000/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_backend_api.py -v`
Expected: FAIL (ConnectionError)

- [ ] **Step 3: Write minimal implementation**

```python
# backend/main.py
from fastapi import FastAPI

app = FastAPI(title="Wildcard Management Studio API")

@app.get("/health")
def health_check():
    return {"status": "ok"}
```

```text
# backend/requirements.txt
fastapi==0.110.0
uvicorn==0.29.0
```

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

```yaml
# Append to docker-compose.yml services
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    depends_on:
      db:
        condition: service_healthy
```

- [ ] **Step 4: Run test to verify it passes**

Run: `docker compose up -d --build backend`
Run: `pytest tests/test_backend_api.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/ docker-compose.yml tests/test_backend_api.py
git commit -m "feat: add FastAPI backend skeleton and health check"
```

### Task 3: Frontend Vite/React Skeleton

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/Dockerfile`
- Modify: `docker-compose.yml`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_frontend.py
import requests

def test_frontend_health():
    """Verify the frontend dev server is reachable."""
    response = requests.get("http://127.0.0.1:5173")
    assert response.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_frontend.py -v`
Expected: FAIL (ConnectionError)

- [ ] **Step 3: Write minimal implementation**

Run: `npm create vite@latest frontend -- --template react-ts` (Note: run non-interactively or just create the files manually)
Since we need explicit code:

```json
// frontend/package.json
{
  "name": "wildcard-management-studio-frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.66",
    "@types/react-dom": "^18.2.22",
    "@vitejs/plugin-react": "^4.2.1",
    "typescript": "^5.2.2",
    "vite": "^5.2.0"
  }
}
```

```typescript
// frontend/vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    watch: {
      usePolling: true
    }
  }
})
```

```html
<!-- frontend/index.html -->
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Wildcard Management Studio</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

```typescript
// frontend/src/main.tsx
import React from 'react'
import ReactDOM from 'react-dom/client'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <div>Wildcard Management Studio</div>
  </React.StrictMode>,
)
```

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
CMD ["npm", "run", "dev", "--", "--host"]
```

```yaml
# Append to docker-compose.yml services
  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
```

- [ ] **Step 4: Run test to verify it passes**

Run: `docker compose up -d --build frontend`
Run: `pytest tests/test_frontend.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/ docker-compose.yml tests/test_frontend.py
git commit -m "feat: add React+Vite frontend skeleton"
```
