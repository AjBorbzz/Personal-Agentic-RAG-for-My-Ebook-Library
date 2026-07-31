import asyncio
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from app.core.config import settings
from app.models.document import Document
from app.retrieval.book_curation_prompt import (
    build_book_curation_prompt,
)
from app.schemas.book_evaluation import (
    BookEvaluationCandidate,
)
from app.services.book_metadata_enrichment import (
    load_document_text,
    sample_document_text,
)
from app.services.ollama import (
    generate_structured_text,
)


def _clean_string(value: Any) -> str | None:
    if value is None:
        return None

    cleaned = " ".join(str(value).split()).strip()

    return cleaned or None


def _clean_list(
    values: Any,
    maximum: int,
) -> list[str]:
    if not isinstance(values, list):
        return []

    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        cleaned = _clean_string(value)

        if not cleaned:
            continue

        normalized = cleaned.lower()

        if normalized in seen:
            continue

        seen.add(normalized)
        result.append(normalized)

        if len(result) >= maximum:
            break

    return result


def calculate_overall_score(
    candidate: BookEvaluationCandidate,
) -> float:
    """
    Overall score rewards depth, practicality, freshness,
    authority, and clarity while penalizing outdated risk.
    """

    score = (
        candidate.technical_depth_score * 0.20
        + candidate.practicality_score * 0.20
        + candidate.freshness_score * 0.20
        + candidate.authority_score * 0.15
        + candidate.clarity_score * 0.15
        + (100 - candidate.outdated_risk_score) * 0.10
    )

    return round(score, 1)


def normalize_candidate(
    candidate: BookEvaluationCandidate,
) -> BookEvaluationCandidate:
    candidate.curator_summary = (
        _clean_string(candidate.curator_summary)
        or "No curator summary was generated."
    )

    candidate.unique_value = _clean_string(
        candidate.unique_value
    )

    candidate.strengths = _clean_list(
        candidate.strengths,
        maximum=8,
    )

    candidate.weaknesses = _clean_list(
        candidate.weaknesses,
        maximum=8,
    )

    candidate.best_for = _clean_list(
        candidate.best_for,
        maximum=8,
    )

    candidate.not_recommended_for = _clean_list(
        candidate.not_recommended_for,
        maximum=6,
    )

    candidate.outdated_topics = _clean_list(
        candidate.outdated_topics,
        maximum=10,
    )

    candidate.overall_score = calculate_overall_score(
        candidate
    )

    return candidate


def build_metadata_snapshot(
    document: Document,
) -> dict[str, Any]:
    return {
        "document_id": document.document_id,
        "filename": document.filename,
        "title": document.title,
        "author": document.author,
        "subtitle": document.subtitle,
        "publisher": document.publisher,
        "edition": document.edition,
        "publication_year": document.publication_year,
        "language": document.language,

        "primary_domain": document.primary_domain,
        "domains": document.domains or [],
        "difficulty_level": document.difficulty_level,
        "topics": document.topics or [],
        "technologies": document.technologies or [],
        "tags": document.tags or [],
        "prerequisite_skills": (
            document.prerequisite_skills or []
        ),

        "source_type": document.source_type,
        "tool_name": document.tool_name,
        "tool_version": document.tool_version,
        "version_major": document.version_major,
        "version_minor": document.version_minor,

        "is_active": document.is_active,
        "is_deprecated": document.is_deprecated,

        "metadata_source": document.metadata_source,
        "metadata_confidence": (
            document.metadata_confidence
        ),
        "metadata_reviewed": document.metadata_reviewed,
        "metadata_review_status": (
            document.metadata_review_status
        ),
    }


def configured_generation_model() -> str | None:
    for setting_name in (
        "ollama_model",
        "generation_model",
        "llm_model",
    ):
        value = getattr(
            settings,
            setting_name,
            None,
        )

        if value:
            return str(value)

    return None


async def generate_book_evaluation_candidate(
    *,
    document: Document,
    maximum_source_characters: int,
) -> tuple[
    BookEvaluationCandidate,
    dict[str, Any],
    int,
    bool,
]:
    full_text = load_document_text(document)

    source_sample, was_truncated = sample_document_text(
        full_text,
        maximum_source_characters,
    )

    metadata_snapshot = build_metadata_snapshot(document)

    prompt = build_book_curation_prompt(
        current_year=datetime.now(
            timezone.utc
        ).year,
        metadata=metadata_snapshot,
        source_text=source_sample,
    )

    try:
        raw_response = await asyncio.wait_for(
            generate_structured_text(
                prompt=prompt,
                json_schema=(
                    BookEvaluationCandidate
                    .model_json_schema()
                ),
            ),
            timeout=300,
        )

    except TimeoutError as error:
        raise RuntimeError(
            "Book evaluation timed out after 300 seconds."
        ) from error

    try:
        candidate = (
            BookEvaluationCandidate
            .model_validate_json(raw_response)
        )

    except ValidationError as error:
        raise ValueError(
            "Ollama returned structured JSON, but it did "
            f"not match the evaluation schema: {error}"
        ) from error

    candidate = normalize_candidate(candidate)

    return (
        candidate,
        metadata_snapshot,
        len(source_sample),
        was_truncated,
    )