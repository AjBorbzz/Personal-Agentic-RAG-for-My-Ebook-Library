import time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.domains import normalize_domain
from app.retrieval.rag_prompt import build_rag_prompt
from app.retrieval.source_quality import has_reasonable_sources
from app.services.domain_classifier import classify_domains
from app.services.ollama import generate_embedding, generate_text
from app.services.qdrant_store import search_similar_chunks

router = APIRouter()


class RagChatRequest(BaseModel):
    question: str
    limit: int = Field(default=5, ge=1, le=20)
    domains: list[str] | None = None
    auto_detect_domains: bool = True
    active_only: bool = True
    include_deprecated: bool = False

    tool_name: str | None = None
    tool_version: str | None = None
    version_major: int | None = None
    version_minor: int | None = None
    source_type: str | None = None
    publication_year: int | None = None


class RagSource(BaseModel):
    source_number: int
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
    chunk_preview: str | None
    source_type: str | None = None
    tool_name: str | None = None
    tool_version: str | None = None
    version_major: int | None = None
    version_minor: int | None = None
    publication_year: int | None = None
    content_hash: str | None = None
    is_active: bool | None = None
    is_deprecated: bool | None = None
    superseded_by_document_id: str | None = None


class RagChatResponse(BaseModel):
    question: str
    answer: str
    collection_name: str
    detected_domains: list[str]
    search_domains: list[str]
    domain_filter_used: bool
    source_count: int
    sources: list[RagSource]
    elapsed_seconds: float
    elapsed_ms: float
    active_only: bool
    include_deprecated: bool
    tool_name: str | None = None
    tool_version: str | None = None
    version_major: int | None = None
    version_minor: int | None = None
    source_type: str | None = None
    publication_year: int | None = None

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

        detected_domains = classify_domains(request.question).domains

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
            active_only=request.active_only,
            include_deprecated=request.include_deprecated,
            tool_name=request.tool_name,
            tool_version=request.tool_version,
            version_major=request.version_major,
            version_minor=request.version_minor,
            source_type=request.source_type,
            publication_year=request.publication_year,
        )

        domain_filter_used = bool(search_domains and search_domains != ["general"])

        # Fallback: if filtered retrieval finds nothing, search all indexed chunks.
        if not matches and domain_filter_used:
            matches = search_similar_chunks(
                collection_name=settings.default_collection,
                query_vector=query_vector,
                limit=request.limit,
                domains=None,
                active_only=request.active_only,
                include_deprecated=request.include_deprecated,
                tool_name=request.tool_name,
                tool_version=request.tool_version,
                version_major=request.version_major,
                version_minor=request.version_minor,
                source_type=request.source_type,
                publication_year=request.publication_year,
            )
            domain_filter_used = False

        if not matches:
            elapsed_seconds = time.perf_counter() - start_time

            return RagChatResponse(
                question=request.question,
                answer="No relevant ebook chunks were found in the vector database.",
                collection_name=settings.default_collection,
                detected_domains=detected_domains,
                search_domains=search_domains,
                domain_filter_used=domain_filter_used,
                source_count=0,
                sources=[],
                elapsed_seconds=round(elapsed_seconds, 3),
                elapsed_ms=round(elapsed_seconds * 1000, 2),
                active_only=request.active_only,
                include_deprecated=request.include_deprecated,
                tool_name=request.tool_name,
                tool_version=request.tool_version,
                version_major=request.version_major,
                version_minor=request.version_minor,
                source_type=request.source_type,
                publication_year=request.publication_year,
            )

        if not has_reasonable_sources(matches):
            elapsed_seconds = time.perf_counter() - start_time

            return RagChatResponse(
                question=request.question,
                answer=(
                    "The retrieved ebook sources are weak for this question. "
                    "Index more relevant books or ask a more specific question."
                ),
                collection_name=settings.default_collection,
                detected_domains=detected_domains,
                search_domains=search_domains,
                domain_filter_used=domain_filter_used,
                source_count=0,
                sources=[],
                elapsed_seconds=round(elapsed_seconds, 3),
                elapsed_ms=round(elapsed_seconds * 1000, 2),
                active_only=request.active_only,
                include_deprecated=request.include_deprecated,
                tool_name=request.tool_name,
                tool_version=request.tool_version,
                version_major=request.version_major,
                version_minor=request.version_minor,
                source_type=request.source_type,
                publication_year=request.publication_year,
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
                    primary_domain=payload.get("primary_domain"),
                    domains=payload.get("domains"),
                    page_number=payload.get("page_number"),
                    page_start=payload.get("page_start"),
                    page_end=payload.get("page_end"),
                    page_numbers=payload.get("page_numbers"),
                    chunk_index=payload.get("chunk_index"),
                    chunk_preview=_preview_text(payload.get("chunk_text") 
                                                or payload.get("text")
                                                or payload.get("chunk_preview")),
                    source_type=payload.get("source_type"),
                    tool_name=payload.get("tool_name"),
                    tool_version=payload.get("tool_version"),
                    version_major=payload.get("version_major"),
                    version_minor=payload.get("version_minor"),
                    publication_year=payload.get("publication_year"),
                    content_hash=payload.get("content_hash"),
                    is_active=payload.get("is_active"),
                    is_deprecated=payload.get("is_deprecated"),
                    superseded_by_document_id=payload.get("superseded_by_document_id"),
                )
            )

        elapsed_seconds = time.perf_counter() - start_time

        return RagChatResponse(
            question=request.question,
            answer=answer,
            collection_name=settings.default_collection,
            detected_domains=detected_domains,
            search_domains=search_domains,
            domain_filter_used=domain_filter_used,
            source_count=len(sources),
            sources=sources,
            elapsed_seconds=round(elapsed_seconds, 3),
            elapsed_ms=round(elapsed_seconds * 1000, 2),
            active_only=request.active_only,
            include_deprecated=request.include_deprecated,
            tool_name=request.tool_name,
            tool_version=request.tool_version,
            version_major=request.version_major,
            version_minor=request.version_minor,
            source_type=request.source_type,
            publication_year=request.publication_year,
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"RAG chat failed: {error}",
        )


@router.post("/ask", response_model=RagChatResponse)
async def ask(request: RagChatRequest):
    return await rag_chat(request)