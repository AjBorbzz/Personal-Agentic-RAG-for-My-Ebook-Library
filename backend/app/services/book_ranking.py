import re
from typing import Any

from app.models.book_curation import BookCuration
from app.models.book_relationship import BookRelationship
from app.models.document import Document
from app.schemas.book_ranking import (
    BookRankingBreakdown,
    BookRankingItem,
    RankingPurpose,
)


PURPOSE_WEIGHTS: dict[str, dict[str, float]] = {
    "learning": {
        "technical_depth": 0.15,
        "practicality": 0.15,
        "freshness": 0.10,
        "authority": 0.15,
        "clarity": 0.35,
        "currentness": 0.10,
    },
    "project": {
        "technical_depth": 0.15,
        "practicality": 0.30,
        "freshness": 0.20,
        "authority": 0.10,
        "clarity": 0.10,
        "currentness": 0.15,
    },
    "reference": {
        "technical_depth": 0.25,
        "practicality": 0.10,
        "freshness": 0.15,
        "authority": 0.25,
        "clarity": 0.15,
        "currentness": 0.10,
    },
    "current_technology": {
        "technical_depth": 0.05,
        "practicality": 0.15,
        "freshness": 0.35,
        "authority": 0.10,
        "clarity": 0.10,
        "currentness": 0.25,
    },
    "foundational": {
        "technical_depth": 0.20,
        "practicality": 0.15,
        "freshness": 0.10,
        "authority": 0.20,
        "clarity": 0.25,
        "currentness": 0.10,
    },
}


PRIORITY_MODIFIERS = {
    "essential": 10.0,
    "high": 6.0,
    "medium": 2.0,
    "low": -4.0,
    "archive": -12.0,
}


ROLE_MODIFIERS: dict[str, dict[str, float]] = {
    "general": {
        "foundational": 4.0,
        "practical_guide": 4.0,
        "reference": 4.0,
        "advanced_specialist": 2.0,
        "supplementary": 0.0,
        "historical": -8.0,
        "redundant": -20.0,
        "avoid": -35.0,
    },
    "learning": {
        "foundational": 10.0,
        "practical_guide": 8.0,
        "reference": 4.0,
        "advanced_specialist": 1.0,
        "supplementary": 1.0,
        "historical": -6.0,
        "redundant": -15.0,
        "avoid": -30.0,
    },
    "project": {
        "foundational": 3.0,
        "practical_guide": 10.0,
        "reference": 6.0,
        "advanced_specialist": 5.0,
        "supplementary": 1.0,
        "historical": -10.0,
        "redundant": -15.0,
        "avoid": -35.0,
    },
    "reference": {
        "foundational": 5.0,
        "practical_guide": 3.0,
        "reference": 10.0,
        "advanced_specialist": 7.0,
        "supplementary": 1.0,
        "historical": -3.0,
        "redundant": -15.0,
        "avoid": -35.0,
    },
    "current_technology": {
        "foundational": 2.0,
        "practical_guide": 7.0,
        "reference": 8.0,
        "advanced_specialist": 5.0,
        "supplementary": 0.0,
        "historical": -18.0,
        "redundant": -18.0,
        "avoid": -40.0,
    },
    "foundational": {
        "foundational": 12.0,
        "practical_guide": 5.0,
        "reference": 4.0,
        "advanced_specialist": -4.0,
        "supplementary": 0.0,
        "historical": -3.0,
        "redundant": -15.0,
        "avoid": -30.0,
    },
}


SUPERSEDED_RELATIONSHIP_PENALTIES = {
    "exact_duplicate": -40.0,
    "same_edition": -35.0,
    "different_edition": -25.0,
    "high_content_overlap": -10.0,
    "related_topic": 0.0,
}


PRIMARY_RELATIONSHIP_BOOSTS = {
    "exact_duplicate": 3.0,
    "same_edition": 3.0,
    "different_edition": 5.0,
    "high_content_overlap": 1.0,
    "related_topic": 0.0,
}


def _clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 100.0,
) -> float:
    return max(minimum, min(value, maximum))


def _score(
    value: float | None,
    default: float = 50.0,
) -> float:
    if value is None:
        return default

    return _clamp(float(value))


def _normalize_term(value: str | None) -> str:
    if not value:
        return ""

    normalized = value.lower().strip()
    normalized = re.sub(r"[^a-z0-9+#.]+", " ", normalized)

    return " ".join(normalized.split())


def _normalize_terms(
    values: list | None,
) -> set[str]:
    if not values:
        return set()

    return {
        normalized
        for value in values
        if (normalized := _normalize_term(str(value)))
    }


def document_matches_filters(
    document: Document,
    *,
    domain: str | None = None,
    topic: str | None = None,
    technology: str | None = None,
) -> bool:
    if domain:
        normalized_domain = _normalize_term(domain)

        document_domains = _normalize_terms(
            document.domains
        )

        if document.primary_domain:
            document_domains.add(
                _normalize_term(
                    document.primary_domain
                )
            )

        if normalized_domain not in document_domains:
            return False

    if topic:
        if _normalize_term(topic) not in _normalize_terms(
            document.topics
        ):
            return False

    if technology:
        requested_technology = _normalize_term(
            technology
        )

        document_technologies = _normalize_terms(
            document.technologies
        )

        if document.tool_name:
            document_technologies.add(
                _normalize_term(document.tool_name)
            )

        if (
            requested_technology
            not in document_technologies
        ):
            return False

    return True


def _purpose_base_score(
    curation: BookCuration | None,
    purpose: RankingPurpose,
) -> float:
    if curation is None:
        return 35.0

    if purpose == "general":
        return _score(
            curation.overall_score,
            default=50.0,
        )

    weights = PURPOSE_WEIGHTS[purpose]

    components = {
        "technical_depth": _score(
            curation.technical_depth_score
        ),
        "practicality": _score(
            curation.practicality_score
        ),
        "freshness": _score(
            curation.freshness_score
        ),
        "authority": _score(
            curation.authority_score
        ),
        "clarity": _score(
            curation.clarity_score
        ),
        "currentness": (
            100
            - _score(
                curation.outdated_risk_score
            )
        ),
    }

    result = sum(
        components[name] * weight
        for name, weight in weights.items()
    )

    return round(result, 2)


def _audience_modifier(
    *,
    book_audience: str | None,
    requested_audience: str | None,
) -> float:
    if not requested_audience:
        return 0.0

    if not book_audience:
        return -2.0

    if book_audience == requested_audience:
        return 6.0

    if book_audience == "mixed":
        return 3.0

    if (
        requested_audience == "beginner"
        and book_audience == "advanced"
    ):
        return -10.0

    if (
        requested_audience == "advanced"
        and book_audience == "beginner"
    ):
        return -5.0

    return -2.0


def _lifecycle_modifier(
    document: Document,
) -> tuple[float, list[str]]:
    modifier = 0.0
    reasons: list[str] = []

    if document.is_active:
        modifier += 2.0
    else:
        modifier -= 15.0
        reasons.append(
            "The document is inactive."
        )

    if document.is_deprecated:
        modifier -= 25.0
        reasons.append(
            "The document is deprecated."
        )

    if document.metadata_reviewed:
        modifier += 2.0

    return modifier, reasons


def _relationship_modifier(
    *,
    document_id: str,
    relationships: list[BookRelationship],
) -> tuple[float, list[str]]:
    modifier = 0.0
    reasons: list[str] = []

    for relationship in relationships:
        if relationship.status != "approved":
            continue

        if (
            relationship
            .recommended_superseded_document_id
            == document_id
        ):
            penalty = (
                SUPERSEDED_RELATIONSHIP_PENALTIES
                .get(
                    relationship.relationship_type,
                    -10.0,
                )
            )

            modifier += penalty

            reasons.append(
                "This document is marked as superseded "
                f"by an approved "
                f"{relationship.relationship_type} "
                "relationship."
            )

        elif (
            relationship
            .recommended_primary_document_id
            == document_id
        ):
            boost = (
                PRIMARY_RELATIONSHIP_BOOSTS.get(
                    relationship.relationship_type,
                    0.0,
                )
            )

            modifier += boost

            if boost > 0:
                reasons.append(
                    "This document is the preferred "
                    f"source in an approved "
                    f"{relationship.relationship_type} "
                    "relationship."
                )

    return modifier, reasons


def _recommendation_tier(
    final_score: float,
    curation: BookCuration | None,
) -> str:
    if (
        curation is None
        or curation.evaluation_status
        != "approved"
    ):
        return "unreviewed"

    if final_score >= 85:
        return "top_pick"

    if final_score >= 70:
        return "recommended"

    if final_score >= 55:
        return "useful"

    if final_score >= 40:
        return "use_with_caution"

    return "archive_or_avoid"


def calculate_book_ranking(
    *,
    document: Document,
    curation: BookCuration | None,
    relationships: list[BookRelationship],
    purpose: RankingPurpose,
    requested_audience: str | None = None,
) -> BookRankingItem:
    base_score = _purpose_base_score(
        curation,
        purpose,
    )

    priority_modifier = 0.0
    role_modifier = 0.0
    audience_modifier = 0.0

    reasons: list[str] = []
    warnings: list[str] = []

    if curation is not None:
        priority_modifier = (
            PRIORITY_MODIFIERS.get(
                curation.library_priority or "",
                0.0,
            )
        )

        role_modifier = (
            ROLE_MODIFIERS
            .get(purpose, {})
            .get(
                curation.recommended_role or "",
                0.0,
            )
        )

        audience_modifier = _audience_modifier(
            book_audience=curation.audience_level,
            requested_audience=requested_audience,
        )

        if curation.library_priority:
            reasons.append(
                "Library priority: "
                f"{curation.library_priority}."
            )

        if curation.recommended_role:
            reasons.append(
                "Recommended role: "
                f"{curation.recommended_role}."
            )

    else:
        warnings.append(
            "The document has no curator evaluation."
        )

    if (
        curation is not None
        and curation.evaluation_status
        != "approved"
    ):
        warnings.append(
            "The curator evaluation is not approved."
        )

    lifecycle_modifier, lifecycle_reasons = (
        _lifecycle_modifier(document)
    )

    relationship_modifier, relationship_reasons = (
        _relationship_modifier(
            document_id=document.document_id,
            relationships=relationships,
        )
    )

    reasons.extend(lifecycle_reasons)
    reasons.extend(relationship_reasons)

    final_score = _clamp(
        base_score
        + priority_modifier
        + role_modifier
        + audience_modifier
        + lifecycle_modifier
        + relationship_modifier
    )

    final_score = round(final_score, 2)

    evaluation_status = (
        curation.evaluation_status
        if curation is not None
        else "not_evaluated"
    )

    return BookRankingItem(
        document_id=document.document_id,
        curation_id=(
            curation.curation_id
            if curation is not None
            else None
        ),
        filename=document.filename,
        title=document.title,
        author=document.author,
        publication_year=(
            document.publication_year
        ),
        primary_domain=document.primary_domain,
        domains=document.domains or [],
        topics=document.topics or [],
        technologies=document.technologies or [],
        is_active=document.is_active,
        is_deprecated=document.is_deprecated,
        evaluation_status=evaluation_status,
        overall_score=(
            curation.overall_score
            if curation is not None
            else None
        ),
        audience_level=(
            curation.audience_level
            if curation is not None
            else None
        ),
        recommended_role=(
            curation.recommended_role
            if curation is not None
            else None
        ),
        library_priority=(
            curation.library_priority
            if curation is not None
            else None
        ),
        ranking_purpose=purpose,
        ranking_score=final_score,
        recommendation_tier=(
            _recommendation_tier(
                final_score,
                curation,
            )
        ),
        breakdown=BookRankingBreakdown(
            purpose_base_score=round(
                base_score,
                2,
            ),
            priority_modifier=priority_modifier,
            role_modifier=role_modifier,
            audience_modifier=audience_modifier,
            lifecycle_modifier=lifecycle_modifier,
            relationship_modifier=(
                relationship_modifier
            ),
            final_score=final_score,
        ),
        reasons=reasons,
        warnings=warnings,
    )