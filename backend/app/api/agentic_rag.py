import time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agents.rag_router import route_and_retrieve
from app.core.config import settings
from app.retrieval.agentic_rag_prompt import build_agentic_rag_prompt
from app.services.ollama import generate_text

router = APIRouter()


class AgenticRagRequest(BaseModel):
    question: str
    limit: int = Field(default=8, ge=1, le=20)
    domains: list[str] | None = None
    auto_detect_domains: bool = True

    # Version-aware retrieval behavior
    active_only: bool = True
    include_deprecated: bool = False

    tool_name: str | None = None
    tool_version: str | None = None
    version_major: int | None = None
    version_minor: int | None = None
    source_type: str | None = None
    publication_year: int | None = None


class AgenticRagSource(BaseModel):
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

    # Registry/version metadata
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


class AgenticRagResponse(BaseModel):
    question: str
    answer: str
    collection_name: str

    intent: str
    retrieval_strategy: str
    detected_domains: list[str]
    search_domains: list[str]
    rewritten_query: str | None
    domain_filter_used: bool
    fallback_used: bool
    retrieval_attempts: int
    router_notes: list[str]

    source_count: int
    sources: list[AgenticRagSource]

    elapsed_seconds: float
    elapsed_ms: float

    # Version-aware filter metadata
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


def _get_chunk_text(payload: dict[str, Any]) -> str | None:
    return (
        payload.get("chunk_text")
        or payload.get("text")
        or payload.get("chunk_preview")
    )


def _build_source(index: int, match: dict[str, Any]) -> AgenticRagSource:
    payload: dict[str, Any] = match.get("payload", {})

    return AgenticRagSource(
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
        chunk_preview=_preview_text(_get_chunk_text(payload)),

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


@router.post("/agentic-rag-chat", response_model=AgenticRagResponse)
async def agentic_rag_chat(request: AgenticRagRequest):
    start_time = time.perf_counter()

    try:
        decision = await route_and_retrieve(
            question=request.question,
            collection_name=settings.default_collection,
            limit=request.limit,
            manual_domains=request.domains,
            auto_detect_domains=request.auto_detect_domains,
            active_only=request.active_only,
            include_deprecated=request.include_deprecated,
            tool_name=request.tool_name,
            tool_version=request.tool_version,
            version_major=request.version_major,
            version_minor=request.version_minor,
            source_type=request.source_type,
            publication_year=request.publication_year,
        )

        if not decision.matches:
            elapsed_seconds = time.perf_counter() - start_time

            return AgenticRagResponse(
                question=request.question,
                answer="No relevant ebook chunks were found in the vector database.",
                collection_name=settings.default_collection,

                intent=decision.intent,
                retrieval_strategy=decision.retrieval_strategy,
                detected_domains=decision.detected_domains,
                search_domains=decision.search_domains,
                rewritten_query=decision.rewritten_query,
                domain_filter_used=decision.domain_filter_used,
                fallback_used=decision.fallback_used,
                retrieval_attempts=decision.retrieval_attempts,
                router_notes=decision.notes,

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

        prompt = build_agentic_rag_prompt(
            question=request.question,
            matches=decision.matches,
            intent=decision.intent,
            retrieval_strategy=decision.retrieval_strategy,
            detected_domains=decision.detected_domains,
            search_domains=decision.search_domains,
            rewritten_query=decision.rewritten_query,
        )

        answer = await generate_text(prompt)

        sources = [
            _build_source(index, match)
            for index, match in enumerate(decision.matches, start=1)
        ]

        elapsed_seconds = time.perf_counter() - start_time

        return AgenticRagResponse(
            question=request.question,
            answer=answer,
            collection_name=settings.default_collection,

            intent=decision.intent,
            retrieval_strategy=decision.retrieval_strategy,
            detected_domains=decision.detected_domains,
            search_domains=decision.search_domains,
            rewritten_query=decision.rewritten_query,
            domain_filter_used=decision.domain_filter_used,
            fallback_used=decision.fallback_used,
            retrieval_attempts=decision.retrieval_attempts,
            router_notes=decision.notes,

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

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Agentic RAG chat failed: {type(error).__name__}: {error}",
        )