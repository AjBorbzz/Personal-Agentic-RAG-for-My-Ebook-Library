from fastapi import FastAPI 

from app.api.health import router as health_router 
from app.api.chat import router as chat_router 
from app.api.ingest import router as ingest_router
from app.api.index import router as index_router
from app.api.search import router as search_router
from app.api.rag import router as rag_router

app = FastAPI(title="Personal Agentic RAG", version="0.1.0")

app.include_router(health_router, tags=["health"])
app.include_router(chat_router, tags=["chat"])
app.include_router(ingest_router, tags=["ingestion"])
app.include_router(index_router, tags=["indexing"])
app.include_router(search_router, tags=["search"])
app.include_router(rag_router, tags=["rag"])