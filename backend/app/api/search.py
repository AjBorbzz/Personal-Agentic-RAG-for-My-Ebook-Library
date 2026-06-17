import time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.domains import normalize_domain
from app.services.domain_classifier import classify_domains
from app.services.ollama import generate_embedding
from app.services.qdrant_store import search_similar_chunks

router = APIRouter()


class SemanticSearchRequest(BaseModel):
    query: str
    limit: int = Field(default=5, ge=1, le=20)
    domains: list[str] | None = None
    auto_detect_domains: bool = True


class SemanticSearchResult(BaseModel):
    score: float
    document_id: str | None
    filename: str | None
    title: str | None
    author: str | None
    file_type: str | None

    primary_domain: str | None
    domains: list[str] | None

    page_number: int | None
    page_start: int | None
    page_end: int | None
    page_numbers: list[int] | None
    chunk_index: int | None
    chunk_text: str | None


class SemanticSearchResponse(BaseModel):
    query: str
    collection_name: str
    detected_domains: list[str]
    search_domains: list[str]
    domain_filter_used: bool
    result_count: int
    results: list[SemanticSearchResult]
    elapsed_seconds: float
    elapsed_ms: float
    


@router.post("/search", response_model=SemanticSearchResponse)
async def semantic_search(request: SemanticSearchRequest):
    start_time = time.perf_counter()

    try:
        query_vector = await generate_embedding(request.query)
        detected_domains = classify_domains(request.query).domains

        if request.domains:
            search_domains = [
                normalize_domain(domain)
                for domain in request.domains
            ]
        elif request.auto_detect_domains:
            search_domains = detected_domains
        else:
            search_domains = []

        matches = search_similar_chunks(
            collection_name=settings.default_collection,
            query_vector=query_vector,
            limit=request.limit,
            domains=search_domains,
        )

        domain_filter_used = bool(search_domains and search_domains != ["general"])

        if not matches and domain_filter_used:
            matches = search_similar_chunks(
                collection_name=settings.default_collection,
                query_vector=query_vector,
                limit=request.limit,
                domains=None,
            )
            domain_filter_used = False

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

                    primary_domain=payload.get("primary_domain"),
                    domains=payload.get("domains"),

                    page_number=payload.get("page_number"),
                    page_start=payload.get("page_start"),
                    page_end=payload.get("page_end"),
                    page_numbers=payload.get("page_numbers"),
                    chunk_index=payload.get("chunk_index"),
                    chunk_text=payload.get("chunk_text"),
                )
            )

        elapsed_seconds = time.perf_counter() - start_time

        return SemanticSearchResponse(
            query=request.query,
            collection_name=settings.default_collection,
            detected_domains=detected_domains,
            search_domains=search_domains,
            domain_filter_used=domain_filter_used,
            result_count=len(results),
            results=results,
            elapsed_seconds=round(elapsed_seconds, 3),
            elapsed_ms=round(elapsed_seconds * 1000, 2),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Semantic search failed: {error}",
        )