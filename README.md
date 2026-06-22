# IntellixDoc

A RAG-based document Q&A system. Upload PDFs, ask questions in natural language, and get answers with source citations.

- **Upload PDFs** — processed in the background
- **Chat over your docs** — answers grounded in your content
- **Citations** — every answer links back to the source page
- **Pluggable LLMs** — Groq (free), OpenAI, Claude, or local Ollama

## Tech Stack

Next.js + TypeScript (frontend) · FastAPI (backend) · Redis + RQ (jobs) · Qdrant (vectors) · PostgreSQL (metadata) · sentence-transformers (embeddings)

## Prerequisites

- Docker & Docker Compose
- Python 3.10+
- Node.js 18+

## Quick Start

### 1. Configure environment

```bash
git clone https://github.com/rajsriselvan-ca/IntellixDoc
cd IntellixDoc
cp .env.example .env
```

> [!IMPORTANT]
> **You must add an LLM API key.** The app cannot answer questions without one.
> Open `.env` and set your provider + key:
> ```env
> LLM_PROVIDER=groq          # groq | openai | claude | ollama
> GROQ_API_KEY=your_key_here # free key at https://console.groq.com
> ```
> Using OpenAI or Claude instead? Set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`.
> Ollama runs locally and needs no key.

### 2. Start infrastructure (Docker)

Runs Postgres, Redis, Qdrant, pgAdmin, and the background worker:

```bash
docker-compose up -d
```

### 3. Run the backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 4. Run the frontend

In a new terminal:

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

### 5. Open the app

Go to **http://localhost:3000**, upload a PDF, wait for status `completed`, then start a chat.
API docs: **http://localhost:8000/docs**

## Configuration

Set in `.env` (project root). Defaults match `docker-compose.yml`, so you usually only need the LLM key.

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | `groq`, `openai`, `claude`, or `ollama` | `groq` |
| `GROQ_API_KEY` / `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | API key for your provider | — |
| `OLLAMA_BASE_URL` | Ollama server (no key needed) | `http://localhost:11434` |
| `EMBEDDING_MODEL` | sentence-transformers model | `all-MiniLM-L6-v2` |
| `REDIS_URL` / `QDRANT_URL` / `DATABASE_URL` | Service URLs | localhost (Docker) |

Frontend uses `NEXT_PUBLIC_API_URL` in `frontend/.env.local` to reach the backend.

## Troubleshooting

- **"No relevant information" / empty answers** — Make sure the document status is `completed` (the worker must be running: `docker-compose logs -f worker`).
- **Backend can't reach Redis/Qdrant** — Confirm `docker-compose up -d` is running; ports 6379 and 6333 must be free.
- **Frontend can't reach backend** — Check the backend is on port 8000 and `NEXT_PUBLIC_API_URL` matches.
- **Port already in use** — Run the backend on another port (`--port 8001`) and update `NEXT_PUBLIC_API_URL`.

## More

- **Deployment:** see [DEPLOYMENT.md](DEPLOYMENT.md)
- **Contributing:** see [CONTRIBUTING.md](CONTRIBUTING.md)
- **License:** MIT — see [LICENSE](LICENSE)
