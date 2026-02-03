# Contributing to IntellixDoc

Thank you for your interest in contributing to IntellixDoc!

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- Redis (or use Docker)
- Qdrant (or use Docker)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd IntellixDoc
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

4. **Start Services with Docker**
   ```bash
   # Start Redis and Qdrant
   docker-compose up -d redis qdrant
   
   # Or start everything
   docker-compose up -d
   ```

5. **Run Backend**
   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```

6. **Run Worker** (in separate terminal)
   ```bash
   cd backend
   rq worker --url redis://localhost:6379/0
   ```

7. **Run Frontend**
   ```bash
   cd frontend
   npm run dev
   ```

## Code Style

### Python
- Follow PEP 8
- Use type hints
- Document functions with docstrings
- Maximum line length: 100 characters

### TypeScript/React
- Use TypeScript
- Follow ESLint rules
- Use functional components with hooks
- Prefer named exports

## Testing

```bash
# Backend tests (when available)
cd backend
pytest

# Frontend tests (when available)
cd frontend
npm test
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Project Structure

```
IntellixDoc/
├── backend/          # FastAPI backend
│   ├── app/
│   │   ├── main.py   # API endpoints
│   │   ├── database.py
│   │   ├── models.py
│   │   └── services/ # Business logic
│   └── requirements.txt
├── frontend/         # Next.js frontend
│   ├── app/
│   │   ├── page.tsx
│   │   └── components/
│   └── package.json
├── worker/           # RQ worker
│   └── worker.py
└── docker-compose.yml
```

## Questions?

Feel free to open an issue for any questions or suggestions!

