# Wildcard Prompt Studio V2 — Setup & Deployment Guide

This guide provides instructions for setting up, configuring, and deploying **Wildcard Prompt Studio V2** in local development and production environments.

---

## 1. Prerequisites

Before installing, ensure your machine meets the following requirements:

- **Python**: Version 3.10, 3.11, or 3.12
- **Node.js**: Version 18.x or higher
- **npm** or **pnpm** installed
- *(Optional)* **Docker & Docker Compose**: For containerized deployment
- *(Optional)* **Local AI Runner**: [Ollama](https://ollama.ai) or [KoboldCpp](https://github.com/LostRuins/koboldcpp) for offline prompt optimization

---

## 2. Environment Variables Reference

Create a `.env` file in the `backend/` and `frontend/` directories (or pass them via environment variables).

### Backend Environment Variables (`backend/.env`)

```ini
# Server Settings
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development

# Database Settings
DATABASE_URL=sqlite:///./wildcards.db

# AI Provider Settings
OLLAMA_HOST=http://localhost:11434
KOBOLDCPP_HOST=http://localhost:5001/v1
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# ComfyUI Integration
COMFYUI_WS_URL=ws://localhost:8188/ws
COMFYUI_HTTP_URL=http://localhost:8188

# Discord Sweep Webhook (optional)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

### Frontend Environment Variables (`frontend/.env`)

```ini
# Backend API Base URL
VITE_API_BASE=http://localhost:8000/api/v1
```

---

## 3. Local Development Setup

### Step 1: Clone Repository
```bash
git clone https://github.com/mskiller/wildcard-prompt-studio.git
cd wildcard-prompt-studio
```

### Step 2: Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# (Optional) Build Danbooru Lexicon SQLite database from docs/ CSV
python scripts/build_danbooru_db.py

# Start backend server with live reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Verify the backend is running by opening `http://localhost:8000/health`.

### Step 3: Frontend Setup
In a new terminal:
```bash
# Navigate to frontend directory
cd frontend

# Install node dependencies
npm install

# Start Vite dev server
npm run dev
```
Open `http://localhost:5173` in your web browser.

---

## 4. Docker Production Deployment

### Quick Launch with Docker Compose
To build and run both the FastAPI backend and Nginx-served Vite frontend:

```bash
docker-compose up --build -d
```

Check running containers:
```bash
docker-compose ps
```

Stop service containers:
```bash
docker-compose down
```

---

## 5. Troubleshooting & FAQ

### Q: "Failed to connect to local AI provider (Ollama/KoboldCpp)"
- Ensure Ollama or KoboldCpp service is running on your machine.
- Verify `OLLAMA_HOST` in `backend/.env` points to `http://localhost:11434` (or `http://host.docker.internal:11434` if running inside Docker containers).

### Q: CORS Errors in Frontend Console
- Ensure backend `main.py` has `CORSMiddleware` configured to allow `http://localhost:3000` or `*`.
- Check that `VITE_API_BASE` points accurately to your backend `/api/v1` prefix.

### Q: Slow Embedding Model Loading
- The first time RAG vector queries run, `SentenceTransformer` downloads the embedding model weights. Subsequent runs use cached local weights.
