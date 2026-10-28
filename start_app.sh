#!/usr/bin/env bash
set -Eeuo pipefail

# Personal Agentic RAG for Ebooks
# One-command local development startup.
#
# Default:
#   - Starts Docker support services
#   - Verifies/starts native Ollama on macOS
#   - Starts FastAPI backend
#   - Starts Next.js frontend
#   - Performs health checks
#
# Optional worker:
#   START_WORKER=1 WORKER_COMMAND='your verified worker command' ./start_app.sh
#
# Optional Docker shutdown when this script exits:
#   STOP_DOCKER_ON_EXIT=1 ./start_app.sh

PROJECT_ROOT="${PROJECT_ROOT:-/Users/ajborbz/Projects/personal_agentic_rag_for_my_ebooks}"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
RUN_DIR="$PROJECT_ROOT/.run"
LOG_DIR="$RUN_DIR/logs"

BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"

OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"
QDRANT_URL="${QDRANT_URL:-http://localhost:6333}"

START_WORKER="${START_WORKER:-0}"
WORKER_COMMAND="${WORKER_COMMAND:-}"
STOP_DOCKER_ON_EXIT="${STOP_DOCKER_ON_EXIT:-0}"

BACKEND_PID=""
FRONTEND_PID=""
WORKER_PID=""

mkdir -p "$LOG_DIR"

timestamp() {
  date +"%Y-%m-%d %H:%M:%S"
}

log() {
  printf '[%s] %s\n' "$(timestamp)" "$*"
}

die() {
  printf '[%s] ERROR: %s\n' "$(timestamp)" "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

wait_for_url() {
  local url="$1"
  local name="$2"
  local attempts="${3:-30}"
  local delay="${4:-1}"

  for ((i=1; i<=attempts; i++)); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      log "$name is ready: $url"
      return 0
    fi
    sleep "$delay"
  done

  return 1
}

cleanup() {
  local exit_code=$?
  trap - EXIT INT TERM

  log "Stopping local app processes..."

  for pid in "$WORKER_PID" "$FRONTEND_PID" "$BACKEND_PID"; do
    if [[ -n "${pid:-}" ]] && kill -0 "$pid" >/dev/null 2>&1; then
      kill "$pid" >/dev/null 2>&1 || true
    fi
  done

  for pid in "$WORKER_PID" "$FRONTEND_PID" "$BACKEND_PID"; do
    if [[ -n "${pid:-}" ]]; then
      wait "$pid" >/dev/null 2>&1 || true
    fi
  done

  if [[ "$STOP_DOCKER_ON_EXIT" == "1" ]]; then
    log "Stopping Docker support services..."
    (
      cd "$PROJECT_ROOT"
      docker compose down
    ) || true
  else
    log "Docker support services left running."
  fi

  exit "$exit_code"
}

trap cleanup EXIT INT TERM

log "Project root: $PROJECT_ROOT"

[[ -d "$PROJECT_ROOT" ]] || die "Project root does not exist: $PROJECT_ROOT"
[[ -d "$BACKEND_DIR" ]] || die "Backend directory missing: $BACKEND_DIR"
[[ -d "$FRONTEND_DIR" ]] || die "Frontend directory missing: $FRONTEND_DIR"

require_command docker
require_command curl
require_command npm

# ---------------------------------------------------------------------------
# 1. Docker support services
# ---------------------------------------------------------------------------

log "Starting Docker support services..."
(
  cd "$PROJECT_ROOT"
  docker compose up -d
)

log "Docker status:"
(
  cd "$PROJECT_ROOT"
  docker compose ps
)

# PostgreSQL
log "Checking PostgreSQL..."
if ! docker exec ebook_postgres pg_isready -U rag -d ebook_rag >/dev/null 2>&1; then
  die "PostgreSQL is not accepting connections."
fi
log "PostgreSQL is ready."

# Qdrant
log "Checking Qdrant..."
wait_for_url "$QDRANT_URL" "Qdrant" 30 1 \
  || die "Qdrant did not become ready at $QDRANT_URL"

# Redis
log "Checking Redis..."
if command -v redis-cli >/dev/null 2>&1; then
  redis-cli -h localhost -p 6379 ping | grep -q PONG \
    || die "Redis did not return PONG."
  log "Redis is ready."
else
  log "redis-cli not installed; Docker container status will be used instead."
fi

# ---------------------------------------------------------------------------
# 2. Native Ollama
# ---------------------------------------------------------------------------

log "Checking Ollama..."

if ! curl -fsS "$OLLAMA_URL/api/tags" >/dev/null 2>&1; then
  if [[ "$(uname -s)" == "Darwin" ]]; then
    log "Ollama is not responding. Attempting to start the macOS Ollama app..."
    open -a Ollama >/dev/null 2>&1 || true
  fi
fi

wait_for_url "$OLLAMA_URL/api/tags" "Ollama" 30 1 \
  || die "Ollama did not become ready at $OLLAMA_URL"

if command -v ollama >/dev/null 2>&1; then
  log "Installed Ollama models:"
  ollama list || true
fi

# ---------------------------------------------------------------------------
# 3. FastAPI backend
# ---------------------------------------------------------------------------

BACKEND_PYTHON="$BACKEND_DIR/.venv/bin/python"

if [[ ! -x "$BACKEND_PYTHON" ]]; then
  # Older project tree used backend/venv instead of backend/.venv.
  BACKEND_PYTHON="$BACKEND_DIR/venv/bin/python"
fi

[[ -x "$BACKEND_PYTHON" ]] \
  || die "Backend virtual environment Python not found (.venv or venv)."

log "Starting FastAPI backend..."
(
  cd "$BACKEND_DIR"
  exec env PYTHONPATH=. \
    "$BACKEND_PYTHON" -m uvicorn app.main:app \
      --reload \
      --host "$BACKEND_HOST" \
      --port "$BACKEND_PORT"
) >"$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!

log "FastAPI PID: $BACKEND_PID"
log "FastAPI log: $LOG_DIR/backend.log"

wait_for_url "http://localhost:$BACKEND_PORT/health" "FastAPI" 45 1 || {
  tail -n 100 "$LOG_DIR/backend.log" || true
  die "FastAPI failed its health check."
}

# ---------------------------------------------------------------------------
# 4. Optional background ingestion worker
# ---------------------------------------------------------------------------

if [[ "$START_WORKER" == "1" ]]; then
  [[ -n "$WORKER_COMMAND" ]] \
    || die "START_WORKER=1 requires WORKER_COMMAND to be set to the verified Phase 12 worker command."

  log "Starting background ingestion worker..."
  (
    cd "$BACKEND_DIR"
    exec env PYTHONPATH=. bash -lc "$WORKER_COMMAND"
  ) >"$LOG_DIR/worker.log" 2>&1 &
  WORKER_PID=$!

  log "Worker PID: $WORKER_PID"
  log "Worker log: $LOG_DIR/worker.log"
else
  log "Background worker not started."
  log "Use START_WORKER=1 with the verified WORKER_COMMAND when queued ingestion is needed."
fi

# ---------------------------------------------------------------------------
# 5. Next.js frontend
# ---------------------------------------------------------------------------

log "Starting Next.js frontend..."
(
  cd "$FRONTEND_DIR"
  exec npm run dev -- --port "$FRONTEND_PORT"
) >"$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!

log "Frontend PID: $FRONTEND_PID"
log "Frontend log: $LOG_DIR/frontend.log"

wait_for_url "http://localhost:$FRONTEND_PORT" "Next.js frontend" 60 1 || {
  tail -n 100 "$LOG_DIR/frontend.log" || true
  die "Next.js frontend failed to become ready."
}

# ---------------------------------------------------------------------------
# Ready
# ---------------------------------------------------------------------------

cat <<EOF

============================================================
Personal Agentic RAG for Ebooks is running
============================================================

Frontend:
  http://localhost:$FRONTEND_PORT

FastAPI:
  http://localhost:$BACKEND_PORT

API docs:
  http://localhost:$BACKEND_PORT/docs

Health:
  http://localhost:$BACKEND_PORT/health

Ollama:
  $OLLAMA_URL

Qdrant:
  $QDRANT_URL

Logs:
  $LOG_DIR/backend.log
  $LOG_DIR/frontend.log
$(if [[ "$START_WORKER" == "1" ]]; then printf '  %s\n' "$LOG_DIR/worker.log"; fi)

Press Ctrl+C to stop FastAPI, Next.js, and the optional worker.

Docker remains running by default.
To stop Docker automatically when this script exits:
  STOP_DOCKER_ON_EXIT=1 ./start_app.sh

============================================================

EOF

# Keep the launcher alive and fail if either main app process exits.
while true; do
  if ! kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    log "FastAPI process stopped unexpectedly."
    tail -n 100 "$LOG_DIR/backend.log" || true
    exit 1
  fi

  if ! kill -0 "$FRONTEND_PID" >/dev/null 2>&1; then
    log "Next.js process stopped unexpectedly."
    tail -n 100 "$LOG_DIR/frontend.log" || true
    exit 1
  fi

  if [[ -n "$WORKER_PID" ]] && ! kill -0 "$WORKER_PID" >/dev/null 2>&1; then
    log "Worker process stopped unexpectedly."
    tail -n 100 "$LOG_DIR/worker.log" || true
    exit 1
  fi

  sleep 2
done
