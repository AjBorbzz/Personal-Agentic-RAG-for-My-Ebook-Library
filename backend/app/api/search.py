import time 
from typing import Any 
from fastapi import APIRouter, HTTPException 
from pydantic import BaseModel, Field 

from app.core.config import settings 
from app.services.ollama import generate_embedding 
from app.services.qdrant_store import search_similar_chunks  

router = APIRouter() 

class SemanticSearchRequest(BaseModel):
    query: str 
    limit: int = Field(default=5, ge=1, le=20)

class SemanticSearchResult(BaseModel):
    score: float 
    document_id: str | None 
    filename: str | None 
    title: str | None 
    author: str | None 
    file_type: str | None 
    page_number: int | None
    chunk_index: int | None 
    chunk_text: str | None 

class SemanticSearchResponse(BaseModel):
    query: str 
    collection_name: str 
    result_count: int 
    results: list[SemanticSearchResult]
    elapsed_seconds: float 
    elapsed_ms: float 

@router.post("/search", response_model=SemanticSearchResponse)
async def semantic_search(request: SemanticSearchRequest):
    start_time = time.perf_counter()
    try:
        query_vector = await generate_embedding(request.query)

        matches = search_similar_chunks(
            collection_name=settings.default_collection,
            query_vector=query_vector,
            limit=request.limit,
        )

        results: list[SemanticSearchResult] = [] 

        for match in matches:
            payload: dict[str, Any] = match.get("payload", {})
            results.append(
                SemanticSearchResult(
                    score=match["score"],
                    document_id=payload.get("document_id"),
                    filename=payload.get("filename"),
                    title=payload.get("title"),
                    author=payload.get("author"),
                    file_type=payload.get("file_type"),
                    page_number=payload.get("page_number"),
                    chunk_index=payload.get("chunk_index"),
                    chunk_text=payload.get("chunk_text"),
                )
            )

        elapsed_seconds = time.perf_counter() - start_time
        return SemanticSearchResponse(
            query=request.query,
            collection_name=settings.default_collection,
            result_count=len(results),
            results=results,
            elapsed_seconds=round(elapsed_seconds, 3),
            elapsed_ms = round(elapsed_seconds * 1000, 2)
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Semantic Search failed: {error}"
        )