import time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agents.rag_router import route_and_retrieve
from app.core.config import settings
from app.retrieval.learning_path_prompt import build_learning_path_prompt
from app.services.ollama import generate_text

router = APIRouter()


class LearningPathRequest(BaseModel):
    goal: str
    duration_weeks: int = Field(default=8, ge=1, le=52)
    hours_per_week: int = Field(default=5, ge=1, le=80)
    current_level: str = Field(default="beginner")
    target_level: str = Field(default="intermediate")
    domains: list[str] | None = None
    auto_detect_domains: bool = True
    limit: int = Field(default=10, ge=3, le=20)


class LearningPathSource(BaseModel):
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


class LearningPathResponse(BaseModel):
    goal: str
    learning_path: str
    collection_name: str

    detected_domains: list[str]
    search_domains: list[str]
    rewritten_query: str | None
    domain_filter_used: bool
    fallback_used: bool
    retrieval_attempts: int
    router_notes: list[str]

    duration_weeks: int
    hours_per_week: int
    current_level: str
    target_level: str

    source_count: int
    sources: list[LearningPathSource]

    elapsed_seconds: float
    elapsed_ms: float


def _preview_text(text: str | None, max_chars: int = 500) -> str | None:
    if not text:
        return None

    cleaned = " ".join(text.split())

    if len(cleaned) <= max_chars:
        return cleaned

    return cleaned[:max_chars] + "..."


@router.post("/learning-path", response_model=LearningPathResponse)
async def generate_learning_path(request: LearningPathRequest):
    start_time = time.perf_counter()

    try:
        decision = await route_and_retrieve(
            question=request.goal,
            collection_name=settings.default_collection,
            limit=request.limit,
            manual_domains=request.domains,
            auto_detect_domains=request.auto_detect_domains,
        )

        if not decision.matches:
            elapsed_seconds = time.perf_counter() - start_time

            return LearningPathResponse(
                goal=request.goal,
                learning_path="No relevant ebook chunks were found for this learning path.",
                collection_name=settings.default_collection,

                detected_domains=decision.detected_domains,
                search_domains=decision.search_domains,
                rewritten_query=decision.rewritten_query,
                domain_filter_used=decision.domain_filter_used,
                fallback_used=decision.fallback_used,
                retrieval_attempts=decision.retrieval_attempts,
                router_notes=decision.notes,

                duration_weeks=request.duration_weeks,
                hours_per_week=request.hours_per_week,
                current_level=request.current_level,
                target_level=request.target_level,

                source_count=0,
                sources=[],

                elapsed_seconds=round(elapsed_seconds, 3),
                elapsed_ms=round(elapsed_seconds * 1000, 2),
            )

        prompt = build_learning_path_prompt(
            goal=request.goal,
            matches=decision.matches,
            duration_weeks=request.duration_weeks,
            hours_per_week=request.hours_per_week,
            current_level=request.current_level,
            target_level=request.target_level,
            detected_domains=decision.detected_domains,
            search_domains=decision.search_domains,
            rewritten_query=decision.rewritten_query,
        )

        learning_path = await generate_text(prompt)

        sources: list[LearningPathSource] = []

        for index, match in enumerate(decision.matches, start=1):
            payload: dict[str, Any] = match.get("payload", {})

            sources.append(
                LearningPathSource(
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
                    chunk_preview=_preview_text(payload.get("chunk_text")),
                )
            )

        elapsed_seconds = time.perf_counter() - start_time

        return LearningPathResponse(
            goal=request.goal,
            learning_path=learning_path,
            collection_name=settings.default_collection,

            detected_domains=decision.detected_domains,
            search_domains=decision.search_domains,
            rewritten_query=decision.rewritten_query,
            domain_filter_used=decision.domain_filter_used,
            fallback_used=decision.fallback_used,
            retrieval_attempts=decision.retrieval_attempts,
            router_notes=decision.notes,

            duration_weeks=request.duration_weeks,
            hours_per_week=request.hours_per_week,
            current_level=request.current_level,
            target_level=request.target_level,

            source_count=len(sources),
            sources=sources,

            elapsed_seconds=round(elapsed_seconds, 3),
            elapsed_ms=round(elapsed_seconds * 1000, 2),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Learning path generation failed: {error}",
        )