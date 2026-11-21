# Script usage

The scripts in this directory are command-line clients for the local Personal
Agentic RAG FastAPI backend. They do not run retrieval or an LLM by themselves:
the backend must be running, and the generation scripts need ebooks that have
already been ingested and indexed.

Run the examples below from the repository root unless a step says otherwise.

## What is here

| Path | Purpose | Default output |
| --- | --- | --- |
| `batch_ingest_index.py` | Upload and optionally index every supported ebook in a directory | `data/batch_ingest_manifest.json` |
| `generate_learning_path.py` | Build a source-grounded learning plan | `data/exports/learning_path.md` |
| `generate_project_plan.py` | Build a source-grounded portfolio project plan | `data/exports/project_plan.md` |
| `generate_architecture_review.py` | Review a described system architecture | `data/exports/architecture_review.md` |
| `review_code_file.py` | Review one local source file | `data/exports/code_review.md` |
| `migrations/` | Manual PostgreSQL schema migrations | Database changes |

All four generation/review scripts append a `Retrieved Sources` section to the
Markdown returned by the backend. An existing file at the selected `--output`
path is overwritten.

## Prerequisites and backend startup

The expected local services are:

- PostgreSQL for the document registry and ingestion metadata.
- Qdrant for indexed ebook chunks.
- Ollama for embeddings and text generation.
- The FastAPI backend, which the scripts call over HTTP.

### 1. Install the Python dependencies

```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
python -m pip install -r backend/requirements.txt
```

The repository currently targets Python 3.11. The CLI scripts themselves need
`httpx`; installing the backend requirements installs it.

### 2. Start PostgreSQL and Qdrant

```bash
docker compose up -d postgres qdrant
docker compose ps
```

The included Compose file exposes PostgreSQL on host port `5433` and Qdrant on
host port `6333`. Ensure `backend/app/.env` contains a matching SQLAlchemy URL:

```dotenv
DATABASE_URL=postgresql+psycopg://rag:rag@localhost:5433/ebook_rag
```

`backend/app/.env` is ignored by Git. Do not commit credentials.

### 3. Start Ollama and install the configured models

In another terminal, start Ollama and make sure these current defaults exist:

```bash
ollama serve
ollama pull qwen3:8b
ollama pull nomic-embed-text
```

The active Ollama URL, Qdrant URL, collection, and model defaults are defined in
`backend/app/core/config.py`. At present those settings are hard-coded in the
`Settings` model; model-related variables in `backend/app/.env` do not override
them. Update `config.py` if your service URLs or model names differ.

### 4. Initialize the database and run FastAPI

From a backend shell with the virtual environment active:

```bash
cd backend
python -m app.db.init_db
uvicorn app.main:app --reload --port 8000
```

Verify the API from another terminal:

```bash
curl http://localhost:8000/health
```

The health endpoint only confirms that FastAPI is responding. It does not test
PostgreSQL, Qdrant, Ollama, or model availability.

## Recommended first run

Activate the environment, ingest a small sample, and then generate an artifact:

```bash
source backend/.venv/bin/activate

python scripts/batch_ingest_index.py /absolute/path/to/ebooks \
  --recursive \
  --limit 5

python scripts/generate_learning_path.py \
  --goal "Learn practical RAG system design" \
  --duration-weeks 6 \
  --hours-per-week 5 \
  --domains ai_ml system_architecture
```

Use absolute ebook paths when practical. The batch manifest keys files by their
resolved absolute paths.

## Batch ingest and index

`batch_ingest_index.py` discovers `.pdf`, `.epub`, and `.txt` files, calls
`POST /ingest`, and then calls `POST /index/{document_id}`. Files are processed
sequentially in sorted path order.

### Common commands

Ingest and index all supported files below a directory:

```bash
python scripts/batch_ingest_index.py /absolute/path/to/ebooks --recursive
```

Test the first five discovered files:

```bash
python scripts/batch_ingest_index.py /absolute/path/to/ebooks \
  --recursive \
  --limit 5
```

Ingest and extract files without creating Qdrant vectors:

```bash
python scripts/batch_ingest_index.py /absolute/path/to/ebooks \
  --recursive \
  --no-index
```

Use a different backend or manifest:

```bash
python scripts/batch_ingest_index.py /absolute/path/to/ebooks \
  --recursive \
  --base-url http://localhost:8001 \
  --manifest data/manifests/my_library.json
```

### Options

| Option | Meaning |
| --- | --- |
| `input_dir` | Required directory to scan. |
| `--recursive` | Include nested directories. Without it, scan only the top level. |
| `--no-index` | Stop after parsing, chunking, and database registration. |
| `--limit N` | Process only the first `N` sorted discoveries. |
| `--manifest PATH` | Change the resume/status file. |
| `--force` | Ignore the local manifest's completed status and attempt processing again. |
| `--base-url URL` | FastAPI URL; default is `http://localhost:8000`. |

### Manifest behavior

The manifest stores each absolute path, SHA-256 hash, document ID, status,
selected API response fields, errors, and timestamps. It is saved after each
major step, so an interrupted run retains progress.

A matching file is skipped when its recorded status is `indexed`. With
`--no-index`, a matching `ingested` file is also skipped. Inspect results with:

```bash
jq '.files[] | {filename, document_id, status, error}' \
  data/batch_ingest_manifest.json

jq '.files[] | select(.status == "failed")' \
  data/batch_ingest_manifest.json
```

Important behavior:

- `--force` bypasses only the local manifest. The backend still rejects content
  whose hash is already registered, normally with HTTP `409 Conflict`.
- A file previously run with `--no-index` cannot currently be resumed directly
  into indexing by this script; a normal rerun tries to ingest it again. Use the
  saved `document_id` with `POST /index/{document_id}` or rework the registry
  entry before retrying.
- Individual file failures are recorded and processing continues. The script
  still exits successfully after the batch, so automation should inspect the
  manifest for `failed` records.
- Image-only/scanned PDFs fail when no text can be extracted; OCR is not part of
  the current ingestion path.

## Generate a learning path

```bash
python scripts/generate_learning_path.py \
  --goal "Become productive with distributed systems design" \
  --duration-weeks 8 \
  --hours-per-week 6 \
  --current-level beginner \
  --target-level intermediate \
  --domains distributed_systems system_architecture \
  --limit 10 \
  --output data/exports/distributed_systems_path.md
```

`--goal` is required. The backend accepts `1-52` weeks, `1-80` hours per week,
and a retrieval `--limit` of `3-20`.

## Generate a project plan

```bash
python scripts/generate_project_plan.py \
  --goal "Build a production-ready document question-answering service" \
  --target-role "AI Engineer" \
  --project-level intermediate \
  --duration-weeks 6 \
  --domains ai_ml backend_development devops \
  --limit 12 \
  --output data/exports/rag_project_plan.md
```

`--goal` is required. The backend accepts `1-52` weeks and a retrieval `--limit`
of `3-20`.

## Generate an architecture review

Repeat `--goal` and `--constraint` for multiple entries. Values following
`--review-focus` form one space-separated list.

```bash
python scripts/generate_architecture_review.py \
  --system-description "FastAPI ingestion API backed by PostgreSQL and Qdrant, with Ollama for local inference" \
  --goal "Support a 100,000-document library" \
  --goal "Keep all book content local" \
  --constraint "Single-node deployment initially" \
  --constraint "No managed cloud services" \
  --review-focus security scalability reliability observability \
  --target-scale "100 concurrent users" \
  --domains system_architecture distributed_systems cybersecurity \
  --limit 12 \
  --output data/exports/local_rag_architecture_review.md
```

`--system-description` is required. If `--review-focus` is omitted, the API uses
its default focus areas. The backend accepts a retrieval `--limit` of `3-20`.

## Review a code file

```bash
python scripts/review_code_file.py \
  --file backend/app/api/ingest.py \
  --language python \
  --code-context "FastAPI endpoint that accepts untrusted ebook uploads" \
  --review-focus correctness security reliability testing \
  --domains backend_development cybersecurity \
  --limit 10 \
  --max-code-chars 16000 \
  --output data/exports/ingest_code_review.md
```

The file must be UTF-8-compatible; undecodable bytes are ignored. The server
accepts `--max-code-chars` from `1000-50000` and a retrieval `--limit` of
`3-20`. Only one file is reviewed per invocation.

## Shared generation options

| Option | Behavior |
| --- | --- |
| `--domains DOMAIN ...` | Restrict retrieval to one or more domains. Omit it to auto-detect domains. |
| `--limit N` | Maximum retrieved chunks. The API validates a range of `3-20`. |
| `--base-url URL` | FastAPI URL; default is `http://localhost:8000`. |
| `--output PATH` | Markdown destination; parent directories are created automatically. |

Known domain values are:

```text
ai_ml backend_development cloud_computing cybersecurity data_engineering
databases devops distributed_systems general linux_systems networking
system_architecture
```

Because `--domains` and `--review-focus` accept a variable number of values,
place another named option after their values when more arguments follow.

Print the exact CLI help at any time:

```bash
python scripts/generate_architecture_review.py --help
python scripts/batch_ingest_index.py --help
```

## Manual database migrations

The SQL files in `scripts/migrations/` are manual PostgreSQL migrations. Back up
the database before applying them and stop on the first SQL error. They assume
the base `documents` table already exists, normally after running
`python -m app.db.init_db` from `backend/`.

The dependency-safe order is:

1. `phase_13a_document_metadata.sql`
2. `phase_13a_metadata_review.sql`
3. `phase_13b_book_curations.sql`
4. `phase_13b_evaluation_error.sql`
5. `phase_13b_book_relationships.sql`
6. `phase_13c_skill_taxonomy.sql`
7. `phase_13c_proficiency_seed.sql`
8. `phase_13d_book_skill_mapping.sql`
9. `phase_13e_personal_skill_profile.sql`
10. `phase_13e_career_targets.sql`
11. `phase_13f_skill_recommendations.sql`

For the default Compose database:

```bash
export MIGRATION_DATABASE_URL='postgresql://rag:rag@localhost:5433/ebook_rag'

mkdir -p data/backups
pg_dump "$MIGRATION_DATABASE_URL" \
  --file data/backups/ebook_rag_before_manual_migrations.sql

psql "$MIGRATION_DATABASE_URL" -v ON_ERROR_STOP=1 -f scripts/migrations/phase_13a_document_metadata.sql
psql "$MIGRATION_DATABASE_URL" -v ON_ERROR_STOP=1 -f scripts/migrations/phase_13a_metadata_review.sql
psql "$MIGRATION_DATABASE_URL" -v ON_ERROR_STOP=1 -f scripts/migrations/phase_13b_book_curations.sql
psql "$MIGRATION_DATABASE_URL" -v ON_ERROR_STOP=1 -f scripts/migrations/phase_13b_evaluation_error.sql
psql "$MIGRATION_DATABASE_URL" -v ON_ERROR_STOP=1 -f scripts/migrations/phase_13b_book_relationships.sql
psql "$MIGRATION_DATABASE_URL" -v ON_ERROR_STOP=1 -f scripts/migrations/phase_13c_skill_taxonomy.sql
psql "$MIGRATION_DATABASE_URL" -v ON_ERROR_STOP=1 -f scripts/migrations/phase_13c_proficiency_seed.sql
psql "$MIGRATION_DATABASE_URL" -v ON_ERROR_STOP=1 -f scripts/migrations/phase_13d_book_skill_mapping.sql
psql "$MIGRATION_DATABASE_URL" -v ON_ERROR_STOP=1 -f scripts/migrations/phase_13e_personal_skill_profile.sql
psql "$MIGRATION_DATABASE_URL" -v ON_ERROR_STOP=1 -f scripts/migrations/phase_13e_career_targets.sql
psql "$MIGRATION_DATABASE_URL" -v ON_ERROR_STOP=1 -f scripts/migrations/phase_13f_skill_recommendations.sql
```

There is no migration-version ledger in this directory. Several files are
additive or use `IF NOT EXISTS`, but the Phase 13E table/index migrations are
not safely rerunnable. Record which files were applied and do not blindly run
the full list against an existing database.

## Troubleshooting

- **Backend health check failed:** start Uvicorn and confirm `--base-url`.
- **Connection refused on port 6333:** start Qdrant with Docker Compose.
- **Ollama connection/model error:** start Ollama and pull the models configured
  in `backend/app/core/config.py`.
- **HTTP 409 during ingestion:** the document content hash already exists in
  PostgreSQL. Check the manifest and document registry before retrying.
- **HTTP 422 from a generation endpoint:** check server-side ranges, especially
  retrieval limit, duration, hours per week, and maximum code characters.
- **"No relevant ebook chunks were found":** ingest and index relevant ebooks,
  then verify the selected domains are not too restrictive.
- **Long-running request:** indexing and local generation can be slow. The
  clients intentionally allow up to 30 minutes for response reads.
