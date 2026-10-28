# Personal Agentic RAG for Ebooks — Startup Script Instructions

This guide explains how to use the project startup script:

```text
start_app.sh
```

The script starts the local services required to run the Personal Agentic RAG for Ebooks application.

---

## What the script starts

The script starts or verifies:

1. Docker Compose support services
   - PostgreSQL
   - Qdrant
   - Redis

2. Native Ollama on macOS

3. FastAPI backend
   - `http://localhost:8000`

4. Optional background ingestion worker

5. Next.js frontend
   - `http://localhost:3000`

It also performs health checks before reporting that the application is ready.

---

## 1. Put the script in the project root

The expected project root is:

```text
/Users/ajborbz/Projects/personal_agentic_rag_for_my_ebooks
```

Copy `start_app.sh` into that directory.

Example:

```bash
cd /Users/ajborbz/Projects/personal_agentic_rag_for_my_ebooks
cp ~/Downloads/start_app.sh .
```

The final location should be:

```text
/Users/ajborbz/Projects/personal_agentic_rag_for_my_ebooks/start_app.sh
```

---

## 2. Make the script executable

Run once:

```bash
cd /Users/ajborbz/Projects/personal_agentic_rag_for_my_ebooks
chmod +x start_app.sh
```

You normally do not need to repeat this unless the file is replaced.

---

## 3. Start the entire application

From the project root:

```bash
./start_app.sh
```

The script will:

```text
Docker Compose
    ↓
PostgreSQL / Qdrant / Redis
    ↓
Ollama
    ↓
FastAPI
    ↓
Optional worker
    ↓
Next.js
    ↓
Health checks
```

When startup succeeds, the terminal displays the local application URLs.

---

## Application URLs

### Frontend

```text
http://localhost:3000
```

### FastAPI backend

```text
http://localhost:8000
```

### FastAPI documentation

```text
http://localhost:8000/docs
```

### Backend health endpoint

```text
http://localhost:8000/health
```

### Ollama

```text
http://localhost:11434
```

### Qdrant

```text
http://localhost:6333
```

---

## 4. Normal development startup

For normal backend/frontend development, use:

```bash
cd /Users/ajborbz/Projects/personal_agentic_rag_for_my_ebooks
./start_app.sh
```

The ingestion worker is not started by default.

This is sufficient when working on:

- FastAPI routes
- Pydantic schemas
- SQLAlchemy services
- PostgreSQL-backed features
- Phase 13 skill intelligence
- frontend pages
- search/RAG APIs that do not require a queued ingestion job

---

## 5. Start with the background ingestion worker

The worker is only required when testing or using queued/background ingestion.

The project intentionally does not hard-code a worker command because the current Phase 12 worker launch command should be verified against the repository before use.

Once the correct worker command is known, start the app with:

```bash
START_WORKER=1 \
WORKER_COMMAND='YOUR_VERIFIED_WORKER_COMMAND' \
./start_app.sh
```

Example structure:

```bash
START_WORKER=1 \
WORKER_COMMAND='python -m ...' \
./start_app.sh
```

Do not invent or substitute a worker command without checking the current repository.

---

## 6. Stop the application

Press:

```text
Ctrl+C
```

in the terminal running `start_app.sh`.

The script stops the processes that it launched:

- FastAPI
- Next.js
- background worker, if enabled

By default, Docker services remain running.

This makes restarting development faster.

---

## 7. Stop Docker automatically too

To stop Docker services when the startup script exits:

```bash
STOP_DOCKER_ON_EXIT=1 ./start_app.sh
```

Then pressing `Ctrl+C` also runs:

```bash
docker compose down
```

This should preserve normal persistent volumes.

Do not routinely delete Docker volumes or local database/vector-storage directories.

---

## 8. Logs

Runtime logs are written under:

```text
.run/logs/
```

Backend:

```text
.run/logs/backend.log
```

Frontend:

```text
.run/logs/frontend.log
```

Worker, when enabled:

```text
.run/logs/worker.log
```

View a log:

```bash
tail -f .run/logs/backend.log
```

or:

```bash
tail -f .run/logs/frontend.log
```

View the most recent 100 lines:

```bash
tail -n 100 .run/logs/backend.log
```

---

## 9. What the script verifies

### PostgreSQL

The script checks:

```bash
docker exec ebook_postgres pg_isready -U rag -d ebook_rag
```

Expected state:

```text
accepting connections
```

---

### Qdrant

The script checks:

```text
http://localhost:6333
```

---

### Redis

When `redis-cli` is installed locally, the script checks:

```bash
redis-cli -h localhost -p 6379 ping
```

Expected:

```text
PONG
```

---

### Ollama

The script checks:

```text
http://localhost:11434/api/tags
```

On macOS, if Ollama is not responding, the script attempts to launch the Ollama application.

---

### FastAPI

The script waits for:

```text
http://localhost:8000/health
```

before continuing.

---

### Next.js

The script waits for:

```text
http://localhost:3000
```

before reporting startup success.

---

## 10. Python virtual environment handling

The script checks for the backend Python environment in this order:

```text
backend/.venv/bin/python
```

then:

```text
backend/venv/bin/python
```

This supports both virtual-environment names that have appeared during project development.

If neither exists, startup stops with an error.

---

## 11. Useful commands while the app is running

### Check backend health

```bash
curl -sS http://localhost:8000/health
```

### Open API documentation

```bash
open http://localhost:8000/docs
```

### Open frontend

```bash
open http://localhost:3000
```

### Check Qdrant

```bash
curl -sS http://localhost:6333/collections
```

### Check Ollama

```bash
ollama list
curl -sS http://localhost:11434/api/tags
```

### Check PostgreSQL

```bash
docker exec ebook_postgres \
  psql -U rag -d ebook_rag \
  -c 'SELECT 1;'
```

### Check Docker services

```bash
docker compose ps
```

---

## 12. If startup fails

Check the first failing dependency instead of modifying application code immediately.

Recommended order:

```text
1. Docker
2. PostgreSQL
3. Qdrant
4. Redis
5. Ollama
6. FastAPI
7. Worker
8. Next.js
9. Feature/API behavior
```

---

## Docker troubleshooting

```bash
docker compose ps -a
```

```bash
docker compose logs --tail=150 postgres qdrant redis
```

PostgreSQL logs:

```bash
docker logs --tail=100 ebook_postgres
```

---

## FastAPI troubleshooting

Read the backend log:

```bash
tail -n 100 .run/logs/backend.log
```

Manual backend compile test:

```bash
cd /Users/ajborbz/Projects/personal_agentic_rag_for_my_ebooks/backend

PYTHONPATH=. python -m compileall app
PYTHONPATH=. python -c 'from app.main import app; print(app.title)'
```

---

## Frontend troubleshooting

Read the frontend log:

```bash
tail -n 100 .run/logs/frontend.log
```

Manual frontend build:

```bash
cd /Users/ajborbz/Projects/personal_agentic_rag_for_my_ebooks/frontend
npm run build
```

---

## Ollama troubleshooting

```bash
ollama list
```

```bash
curl -sS http://localhost:11434/api/tags
```

On macOS, launch Ollama manually if required.

Do not change configured model names only because an older project document used different model tags.

---

## 13. Override the project path

The default project path is:

```text
/Users/ajborbz/Projects/personal_agentic_rag_for_my_ebooks
```

If the repository is moved, override it:

```bash
PROJECT_ROOT=/new/path/to/personal_agentic_rag_for_my_ebooks \
./start_app.sh
```

---

## 14. Override ports

Backend example:

```bash
BACKEND_PORT=8001 ./start_app.sh
```

Frontend example:

```bash
FRONTEND_PORT=3001 ./start_app.sh
```

Both:

```bash
BACKEND_PORT=8001 \
FRONTEND_PORT=3001 \
./start_app.sh
```

Use the normal project ports unless there is a specific local conflict.

---

## 15. Recommended daily workflow

Start development:

```bash
cd /Users/ajborbz/Projects/personal_agentic_rag_for_my_ebooks
./start_app.sh
```

Open:

```text
http://localhost:3000
```

Check API documentation when needed:

```text
http://localhost:8000/docs
```

Watch backend logs:

```bash
tail -f .run/logs/backend.log
```

Stop the host development processes:

```text
Ctrl+C
```

Leave Docker running for the next development session unless there is a reason to stop it.

---

# Quick Reference

## Start

```bash
cd /Users/ajborbz/Projects/personal_agentic_rag_for_my_ebooks
./start_app.sh
```

## Start and stop Docker with the application

```bash
STOP_DOCKER_ON_EXIT=1 ./start_app.sh
```

## Start with ingestion worker

```bash
START_WORKER=1 \
WORKER_COMMAND='YOUR_VERIFIED_WORKER_COMMAND' \
./start_app.sh
```

## Frontend

```text
http://localhost:3000
```

## API docs

```text
http://localhost:8000/docs
```

## Health

```text
http://localhost:8000/health
```

## Logs

```text
.run/logs/backend.log
.run/logs/frontend.log
.run/logs/worker.log
```

## Stop

```text
Ctrl+C
```
