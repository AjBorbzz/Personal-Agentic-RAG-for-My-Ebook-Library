import time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agents.rag_router import route_and_retrieve
from app.core.config import settings
from app.retrieval.code_review_prompt import build_code_review_prompt
from app.services.ollama import generate_text

router = APIRouter()


class CodeReviewRequest(BaseModel):
    code: str
    language: str = Field(default="python")
    code_context: str = Field(default="No additional context provided.")
    review_focus: list[str] = Field(
        default_factory=lambda: [
            "correctness",
            "security",
            "reliability",
            "performance",
            "maintainability",
            "testing",
        ]
    )
    domains: list[str] | None = None
    auto_detect_domains: bool = True
    limit: int = Field(default=10, ge=3, le=20)
    max_code_chars: int = Field(default=12000, ge=1000, le=50000)


class CodeReviewSource(BaseModel):
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


class CodeReviewResponse(BaseModel):
    language: str
    code_context: str
    code_review: str
    collection_name: str

    review_focus: list[str]

    detected_domains: list[str]
    search_domains: list[str]
    rewritten_query: str | None
    domain_filter_used: bool
    fallback_used: bool
    retrieval_attempts: int
    router_notes: list[str]

    source_count: int
    sources: list[CodeReviewSource]

    elapsed_seconds: float
    elapsed_ms: float


def _preview_text(text: str | None, max_chars: int = 500) -> str | None:
    if not text:
        return None

    cleaned = " ".join(text.split())

    if len(cleaned) <= max_chars:
        return cleaned

    return cleaned[:max_chars] + "..."


def _build_retrieval_question(request: CodeReviewRequest) -> str:
    code_preview = request.code[:4000]

    return (
        f"Code review request.\n"
        f"Language: {request.language}\n"
        f"Context: {request.code_context}\n"
        f"Review focus: {', '.join(request.review_focus)}\n\n"
        f"Code preview:\n"
        f"{code_preview}"
    )


@router.post("/code-review", response_model=CodeReviewResponse)
async def review_code(request: CodeReviewRequest):
    start_time = time.perf_counter()

    try:
        retrieval_question = _build_retrieval_question(request)

        decision = await route_and_retrieve(
            question=retrieval_question,
            collection_name=settings.default_collection,
            limit=request.limit,
            manual_domains=request.domains,
            auto_detect_domains=request.auto_detect_domains,
        )

        if not decision.matches:
            elapsed_seconds = time.perf_counter() - start_time

            return CodeReviewResponse(
                language=request.language,
                code_context=request.code_context,
                code_review="No relevant ebook chunks were found for this code review.",
                collection_name=settings.default_collection,

                review_focus=request.review_focus,

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

        prompt = build_code_review_prompt(
            code=request.code,
            language=request.language,
            code_context=request.code_context,
            review_focus=request.review_focus,
            matches=decision.matches,
            detected_domains=decision.detected_domains,
            search_domains=decision.search_domains,
            rewritten_query=decision.rewritten_query,
            max_code_chars=request.max_code_chars,
        )

        code_review = await generate_text(prompt)

        sources: list[CodeReviewSource] = []

        for index, match in enumerate(decision.matches, start=1):
            payload: dict[str, Any] = match.get("payload", {})

            sources.append(
                CodeReviewSource(
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

        return CodeReviewResponse(
            language=request.language,
            code_context=request.code_context,
            code_review=code_review,
            collection_name=settings.default_collection,

            review_focus=request.review_focus,

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
            detail=f"Code review failed: {error}",
        )