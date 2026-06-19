import time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agents.rag_router import route_and_retrieve
from app.core.config import settings
from app.retrieval.architecture_review_prompt import build_architecture_review_prompt
from app.services.ollama import generate_text

router = APIRouter()


class ArchitectureReviewRequest(BaseModel):
    system_description: str
    goals: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    review_focus: list[str] = Field(
        default_factory=lambda: [
            "security",
            "scalability",
            "reliability",
            "data model",
            "API design",
            "deployment",
            "observability",
        ]
    )
    target_scale: str = Field(default="small to medium production workload")
    domains: list[str] | None = None
    auto_detect_domains: bool = True
    limit: int = Field(default=12, ge=3, le=20)


class ArchitectureReviewSource(BaseModel):
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


class ArchitectureReviewResponse(BaseModel):
    system_description: str
    architecture_review: str
    collection_name: str

    goals: list[str]
    constraints: list[str]
    review_focus: list[str]
    target_scale: str

    detected_domains: list[str]
    search_domains: list[str]
    rewritten_query: str | None
    domain_filter_used: bool
    fallback_used: bool
    retrieval_attempts: int
    router_notes: list[str]

    source_count: int
    sources: list[ArchitectureReviewSource]

    elapsed_seconds: float
    elapsed_ms: float


def _preview_text(text: str | None, max_chars: int = 500) -> str | None:
    if not text:
        return None

    cleaned = " ".join(text.split())

    if len(cleaned) <= max_chars:
        return cleaned

    return cleaned[:max_chars] + "..."


@router.post("/architecture-review", response_model=ArchitectureReviewResponse)
async def review_architecture(request: ArchitectureReviewRequest):
    start_time = time.perf_counter()

    try:
        retrieval_question = (
            f"Architecture review request:\n"
            f"{request.system_description}\n\n"
            f"Goals: {', '.join(request.goals) if request.goals else 'not specified'}\n"
            f"Constraints: {', '.join(request.constraints) if request.constraints else 'not specified'}\n"
            f"Review focus: {', '.join(request.review_focus)}\n"
            f"Target scale: {request.target_scale}"
        )

        decision = await route_and_retrieve(
            question=retrieval_question,
            collection_name=settings.default_collection,
            limit=request.limit,
            manual_domains=request.domains,
            auto_detect_domains=request.auto_detect_domains,
        )

        if not decision.matches:
            elapsed_seconds = time.perf_counter() - start_time

            return ArchitectureReviewResponse(
                system_description=request.system_description,
                architecture_review="No relevant ebook chunks were found for this architecture review.",
                collection_name=settings.default_collection,

                goals=request.goals,
                constraints=request.constraints,
                review_focus=request.review_focus,
                target_scale=request.target_scale,

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
            )

        prompt = build_architecture_review_prompt(
            system_description=request.system_description,
            matches=decision.matches,
            review_focus=request.review_focus,
            goals=request.goals,
            constraints=request.constraints,
            target_scale=request.target_scale,
            detected_domains=decision.detected_domains,
            search_domains=decision.search_domains,
            rewritten_query=decision.rewritten_query,
        )

        architecture_review = await generate_text(prompt)

        sources: list[ArchitectureReviewSource] = []

        for index, match in enumerate(decision.matches, start=1):
            payload: dict[str, Any] = match.get("payload", {})

            sources.append(
                ArchitectureReviewSource(
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

        return ArchitectureReviewResponse(
            system_description=request.system_description,
            architecture_review=architecture_review,
            collection_name=settings.default_collection,

            goals=request.goals,
            constraints=request.constraints,
            review_focus=request.review_focus,
            target_scale=request.target_scale,

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
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Architecture review failed: {error}",
        )