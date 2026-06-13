from fastapi import FastAPI 

from app.api.health import router as health_router 
from app.api.chat import router as chat_router 
from app.api.ingest import router as ingest_router

app = FastAPI(title="Personal Agentic RAG", version="0.1.0")

app.include_router(health_router, tags=["health"])
app.include_router(chat_router, tags=["chat"])
app.include_router(ingest_router, tags=["ingestion"])