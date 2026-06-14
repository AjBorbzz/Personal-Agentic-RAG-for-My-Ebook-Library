import time 
from typing import Any 
from fastapi import APIRouter, HTTPException 
from pydantic import BaseModel, Field 

from app.core.config import settings 
from app.retrieval.rag_prompt import build_rag_prompt 
from app.services.ollama import generate_embedding, generate_text 
from app.services.qdrant_store import search_similar_chunks 
from app.retrieval.source_quality import has_reasonable_sources

router = APIRouter() 

class RagChatRequest(BaseModel):
    question: str 
    limit: int = Field(default=5, ge=1, le=20)

class RagSource(BaseModel):
    source_number: int 
    score: float 
    document_id: str | None 
    filename: str | None 
    title: str | None 
    author: str | None 
    file_type: str | None 
    chunk_index: int | None 
    chunk_preview: str | None 

class RagChatResponse(BaseModel):
    question: str 
    answer: str 
    collection_name: str 
    source_count: int 
    sources: list[RagSource]
    elapsed_seconds: float 
    elapsed_ms: float 

def _preview_text(text: str | None, max_chars: int = 500) -> str | None:
    if not text:
        return None 
    cleaned = " ".join(text.split())

    if len(cleaned) <= max_chars:
        return cleaned 
    
    return cleaned[:max_chars] + "..."

@router.post("/rag-chat", response_model=RagChatResponse)
async def rag_chat(request: RagChatRequest):
    start_time = time.perf_counter() 

    try:
        query_vector = await generate_embedding(request.question)
        matches = search_similar_chunks(
            collection_name=settings.default_collection, 
            query_vector=query_vector,
            limit=request.limit,
        )

        if not matches:
            elapsed_seconds = time.perf_counter() - start_time 
            return RagChatResponse(
                question=request.question,
                answer="No relevant ebook chunks were found in the vector database.",
                collection_name=settings.default_collection,
                source_count=0,
                sources=[],
                elapsed_seconds=round(elapsed_seconds, 3),
                elapsed_ms=round(elapsed_seconds * 1000, 2),
            )
        
        if not has_reasonable_sources(matches):
            elapsed_seconds = time.perf_counter() - start_time 
            return RagChatResponse(
                question=request.question,
                answer="The retrieved ebook sources are weak for this question."
                       "Index more relevant books or ask a more specific question.",
                collection_name=settings.default_collection,
                source_count=0,
                sources=[],
                elapsed_seconds=round(elapsed_seconds, 3),
                elapsed_ms=round(elapsed_seconds * 1000, 2),
            )
        
        prompt = build_rag_prompt(
            question=request.question,
            matches=matches,
        )
        answer = await generate_text(prompt)

        sources: list[RagSource] = []

        for index, match in enumerate(matches, start=1):
            payload: dict[str, Any] = match.get("payload", {})

            sources.append(
                RagSource(
                    source_number=index,
                    score=match["score"],
                    document_id=payload.get("document_id"),
                    filename=payload.get("filename"),
                    title=payload.get("title"),
                    author=payload.get("author"),
                    file_type=payload.get("file_type"),
                    chunk_index=payload.get("chunk_index"),
                    chunk_preview=_preview_text(payload.get("chunk_text"))
                )
            )
        elapsed_seconds = time.perf_counter() - start_time 

        return RagChatResponse(
            question=request.question,
            answer=answer,
            collection_name=settings.default_collection,
            source_count=len(sources),
            sources=sources,
            elapsed_seconds=round(elapsed_seconds, 3),
            elapsed_ms=round(elapsed_seconds * 1000, 2)
        )
    
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"RAG chat failed : {error}"
        )