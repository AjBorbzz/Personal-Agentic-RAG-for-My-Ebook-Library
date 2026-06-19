from fastapi import FastAPI

from app.api.agentic_rag import router as agentic_rag_router
from app.api.chat import router as chat_router
from app.api.domains import router as domains_router
from app.api.health import router as health_router
from app.api.ingest import router as ingest_router
from app.api.index import router as index_router
from app.api.learning_path import router as learning_path_router
from app.api.rag import router as rag_router
from app.api.router_preview import router as router_preview_router
from app.api.search import router as search_router
from app.api.project_generator import router as project_generator_router
from app.api.architecture_reviewer import router as architecture_reviewer_router
from app.api.code_reviewer import router as code_reviewer_router

app = FastAPI(
    title="Personal Agentic RAG",
    version="0.10.0",
)

app.include_router(health_router, tags=["health"])
app.include_router(chat_router, tags=["chat"])
app.include_router(ingest_router, tags=["ingestion"])
app.include_router(index_router, tags=["indexing"])
app.include_router(search_router, tags=["search"])
app.include_router(rag_router, tags=["rag"])
app.include_router(domains_router, tags=["domains"])
app.include_router(router_preview_router, tags=["router-preview"])
app.include_router(agentic_rag_router, tags=["agentic-rag"])
app.include_router(learning_path_router, tags=["learning-path"])
app.include_router(project_generator_router, tags=["project-generator"])
app.include_router(architecture_reviewer_router, tags=["architecture-reviewer"])
app.include_router(code_reviewer_router, tags=["code-reviewer"])