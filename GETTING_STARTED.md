# Personal Agentic RAG for Ebooks — Getting Started

Quick reference for starting the local application after a reboot or development break.

## 1. Go to the project

```bash
cd /Users/ajborbz/Projects/personal_agentic_rag_for_my_ebooks
```

## 2. Start Docker services

PostgreSQL, Qdrant, and Redis run through Docker Compose.

```bash
docker compose up -d
docker compose ps
```

Expected services should include:

- PostgreSQL
- Qdrant
- Redis

Quick checks:

```bash
curl -sS http://localhost:6333
docker exec ebook_postgres pg_isready -U rag -d ebook_rag
redis-cli -h localhost -p 6379 ping
```

Expected Redis result:

```text
PONG
```

## 3. Start / verify Ollama

Ollama runs natively on macOS, not in Docker.

```bash
ollama list
curl -sS http://localhost:11434/api/tags
```

If Ollama is not running, start the Ollama application first.

Do not change model names just because an older setup document uses different model tags. Use the models configured in the current project.

## 4. Start the FastAPI backend

Open a dedicated terminal:

```bash
cd /Users/ajborbz/Projects/personal_agentic_rag_for_my_ebooks/backend
source .venv/bin/activate
PYTHONPATH=. python -m uvicorn app.main:app --reload --port 8000
```

Backend:

```text
http://localhost:8000
```

Useful URLs:

```text
http://localhost:8000/health
http://localhost