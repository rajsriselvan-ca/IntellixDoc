# IntellixDoc

A **RAG-based (Retrieval-Augmented Generation) document Q&A system**. Upload PDFs, ask questions in natural language, and get answers with source citations. Built for accuracy and production use.

---

## What It Does

- **Upload PDFs** — Multiple documents supported; processing runs in the background.
- **Chat over your docs** — Ask questions and get answers grounded in your uploaded content.
- **Citations** — Answers link back to source document and page.
- **Multiple LLM backends** — Groq (free tier), Ollama, OpenAI, or Claude.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 14, React.js, TypeScript, Tailwind CSS |
| **Backend** | FastAPI (Python 3.10+) |
| **Queue / jobs** | Redis, Python RQ |
| **Vector store** | Qdrant |
| **Metadata DB** | PostgreSQL (or SQLite for local dev) |
| **PDF parsing** | PyMuPDF |
| **Embeddings** | sentence-transformers |
| **LLM** | Groq (default), Ollama, OpenAI, Anthropic Claude |

---

## Project Structure

```
IntellixDoc/
├── frontend/           # Next.js app (port 3000)
│   ├── app/
│   │   ├── components/   # ChatInterface, DocumentUpload, Sidebar
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── package.json
│   └── Dockerfile
├── backend/            # FastAPI app (port 8000)
│   ├── app/
│   │   ├── main.py      # API routes
│   │   ├── config.py
│   │   ├── database.py  # SQLAlchemy models
│   │   ├── models.py    # Pydantic schemas
│   │   ├── tasks.py     # RQ tasks
│   │   └── services/    # embedding, llm, pdf_parser, qdrant_service
│   ├── requirements.txt
│   └── Dockerfile
├── worker/             # RQ worker (processes PDFs in background)
│   ├── worker.py
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml  # Postgres, Redis, Qdrant, pgAdmin, Worker
├── .env.example
└── README.md
```

---

## Prerequisites

- **Docker & Docker Compose** — For Postgres, Redis, Qdrant, and the worker.
- **Python 3.10+** — For running the backend locally.
- **Node.js 18+** — For running the frontend locally.

---

## Running Locally

### 1. Clone and configure environment

```bash
git clone <your-repo-url>
cd IntellixDoc
cp .env.example .env
```

Edit `.env` and set at least:

- `LLM_PROVIDER=groq` (or `ollama`, `openai`, `claude`)
- `GROQ_API_KEY=...` — Get a free key at [console.groq.com](https://console.groq.com)

### 2. Start infrastructure (Docker)

Starts Postgres, Redis, Qdrant, pgAdmin, and the RQ worker:

```bash
docker-compose up -d
```

Check services:

```bash
docker-compose ps
```

- **Frontend (you run locally):** will use port **3000**
- **Backend (you run locally):** will use port **8000**
- **Postgres:** 5432 | **Redis:** 6379 | **Qdrant:** 6333 | **pgAdmin:** 5050

### 3. Run backend (local)

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend will use `.env` from the project root (or from `backend/` if you put one there). It expects:

- `REDIS_URL=redis://localhost:6379/0`
- `QDRANT_URL=http://localhost:6333`
- `DATABASE_URL=postgresql://intellixdoc:intellixdoc123@localhost:5432/intellixdoc` (matches `docker-compose` Postgres)

### 4. Run frontend (local)

In a new terminal:

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

### 5. Use the app

- Open **http://localhost:3000**
- Upload a PDF, wait until status is “completed”
- Start a new chat and ask questions about your document
- API docs: **http://localhost:8000/docs**

---

## Configuration

### Backend / Worker `.env` (root or `backend/`)

| Variable | Description | Example |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM backend | `groq`, `ollama`, `openai`, `claude` |
| `GROQ_API_KEY` | Groq API key | From [console.groq.com](https://console.groq.com) |
| `OPENAI_API_KEY` | OpenAI key | For `openai` provider |
| `ANTHROPIC_API_KEY` | Claude key | For `claude` provider |
| `OLLAMA_BASE_URL` | Ollama server | `http://localhost:11434` |
| `REDIS_URL` | Redis for RQ | `redis://localhost:6379/0` |
| `QDRANT_URL` | Qdrant URL | `http://localhost:6333` |
| `DATABASE_URL` | Postgres (or SQLite) | `postgresql://intellixdoc:intellixdoc123@localhost:5432/intellixdoc` |
| `EMBEDDING_MODEL` | Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |

### Frontend `.env.local`

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend  base URL, e.g. `http://localhost:8000` |

---

## API Endpoints (overview)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/documents/upload` | Upload PDF |
| GET | `/api/documents` | List documents |
| POST | `/api/chats` | Create chat |
| GET | `/api/chats/{id}` | Get chat |
| POST | `/api/chats/{id}/messages` | Send message |
| GET | `/api/chats/{id}/messages` | Get messages |

---

## Troubleshooting

- **Backend can’t reach Redis/Qdrant**  
  Ensure `docker-compose up -d` is running and ports 6379 and 6333 are free.  
  Test: `redis-cli -h localhost -p 6379 ping` and `curl http://localhost:6333/health`.

- **Frontend can’t reach backend**  
  Confirm backend is running on 8000 and `NEXT_PUBLIC_API_URL=http://localhost:8000` in `frontend/.env.local`. Check CORS in `backend/app/main.py` allows `http://localhost:3000`.

- **Worker not processing uploads**  
  Check worker logs: `docker-compose logs -f worker`. Ensure Redis is up and worker container has correct `REDIS_URL` and `QDRANT_URL` in `docker-compose.yml`.

- **Port already in use**  
  Change backend port, e.g. `uvicorn app.main:app --reload --port 8001`, and set `NEXT_PUBLIC_API_URL=http://localhost:8001` in the frontend.

- **PyTorch / sentence-transformers on Windows**  
  If you hit DLL or install issues, try the CPU-only build:  
  `pip install torch --index-url https://download.pytorch.org/whl/cpu`  
  then reinstall sentence-transformers.

---

## Scripts (Windows PowerShell)

- `.\start-docker.ps1` — Start Docker Compose services.
- `.\stop-docker.ps1` — Stop services.
- `.\start-backend.ps1` — Start backend (assumes venv and deps installed).
- `.\start-frontend.ps1` — Start frontend (assumes `npm install` done).

---

## Deployment

For production (e.g. Oracle Cloud VM, VPS), see **[DEPLOYMENT.md](DEPLOYMENT.md)** for Docker, Nginx, and SSL setup.

---

## Contributing

See **[CONTRIBUTING.md](CONTRIBUTING.md)** for development setup and contribution guidelines.

---

## License

MIT — see [LICENSE](LICENSE).
