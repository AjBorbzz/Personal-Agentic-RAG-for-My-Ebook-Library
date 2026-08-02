import re
from difflib import SequenceMatcher
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.book_relationship import BookRelationship
from app.models.document import Document
from app.services.book_metadata_enrichment import (
    load_document_text,
    sample_document_text,
)


WORD_PATTERN = re.compile(
    r"[a-z0-9][a-z0-9_+#.\-]*",
    flags=re.IGNORECASE,
)

DETECTOR_VERSION = 1


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""

    normalized = value.lower().strip()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return " ".join(normalized.split())


def _text_similarity(
    value_a: str | None,
    value_b: str | None,
) -> float:
    normalized_a = _normalize_text(value_a)
    normalized_b = _normalize_text(value_b)

    if not normalized_a or not normalized_b:
        return 0.0

    return round(
        SequenceMatcher(
            None,
            normalized_a,
            normalized_b,
        ).ratio(),
        4,
    )


def _normalize_isbn(value: str | None) -> str:
    if not value:
        return ""

    return re.sub(
        r"[^0-9xX]",
        "",
        value,
    ).upper()


def _isbn_values(document: Document) -> set[str]:
    return {
        value
        for value in (
            _normalize_isbn(document.isbn_10),
            _normalize_isbn(document.isbn_13),
        )
        if value
    }


def _normalize_terms(values: Any) -> set[str]:
    if not isinstance(values, list):
        return set()

    return {
        _normalize_text(str(value))
        for value in values
        if _normalize_text(str(value))
    }


def _metadata_terms(document: Document) -> set[str]:
    terms: set[str] = set()

    for values in (
        document.domains,
        document.topics,
        document.technologies,
        document.tags,
        document.prerequisite_skills,
    ):
        terms.update(_normalize_terms(values))

    if document.primary_domain:
        terms.add(_normalize_text(document.primary_domain))

    if document.tool_name:
        terms.add(_normalize_text(document.tool_name))

    return {term for term in terms if term}


def _jaccard(
    values_a: set[str],
    values_b: set[str],
) -> float:
    if not values_a or not values_b:
        return 0.0

    intersection = len(values_a & values_b)
    union = len(values_a | values_b)

    if union == 0:
        return 0.0

    return round(intersection / union, 4)


def _create_shingles(
    text: str | None,
    shingle_size: int,
) -> set[tuple[str, ...]]:
    if not text:
        return set()

    words = [
        word.lower()
        for word in WORD_PATTERN.findall(text)
    ]

    if len(words) < shingle_size:
        return set()

    return {
        tuple(words[index : index + shingle_size])
        for index in range(
            len(words) - shingle_size + 1
        )
    }


def _content_overlap(
    text_a: str | None,
    text_b: str | None,
    shingle_size: int,
) -> float:
    shingles_a = _create_shingles(
        text_a,
        shingle_size,
    )
    shingles_b = _create_shingles(
        text_b,
        shingle_size,
    )

    if not shingles_a or not shingles_b:
        return 0.0

    intersection = len(shingles_a & shingles_b)

    containment = intersection / min(
        len(shingles_a),
        len(shingles_b),
    )

    union = len(shingles_a | shingles_b)
    jaccard = intersection / union if union else 0.0

    # Containment helps detect an older edition contained
    # within a larger, newer edition.
    score = containment * 0.70 + jaccard * 0.30

    return round(score, 4)


def _safe_document_sample(
    document: Document,
    maximum_characters: int,
) -> str | None:
    try:
        full_text = load_document_text(document)
    except (FileNotFoundError, OSError, ValueError):
        return None

    sample, _ = sample_document_text(
        full_text,
        maximum_characters,
    )

    return sample


def _document_snapshot(
    document: Document,
) -> dict[str, Any]:
    return {
        "document_id": document.document_id,
        "filename": document.filename,
        "title": document.title,
        "author": document.author,
        "edition": document.edition,
        "publication_year": document.publication_year,
        "isbn_10": document.isbn_10,
        "isbn_13": document.isbn_13,
        "primary_domain": document.primary_domain,
        "domains": document.domains or [],
        "topics": document.topics or [],
        "technologies": document.technologies or [],
        "tool_name": document.tool_name,
        "tool_version": document.tool_version,
        "is_active": document.is_active,
        "is_deprecated": document.is_deprecated,
        "metadata_reviewed": document.metadata_reviewed,
    }


def _edition_differs(
    document_a: Document,
    document_b: Document,
) -> bool:
    edition_a = _normalize_text(document_a.edition)
    edition_b = _normalize_text(document_b.edition)

    if edition_a and edition_b and edition_a != edition_b:
        return True

    if (
        document_a.publication_year is not None
        and document_b.publication_year is not None
        and document_a.publication_year
        != document_b.publication_year
    ):
        return True

    return False


def _recommend_primary(
    document_a: Document,
    document_b: Document,
    relationship_type: str,
) -> tuple[str | None, str | None, str]:
    if relationship_type == "related_topic":
        return None, None, "keep_both"

    if relationship_type == "high_content_overlap":
        return None, None, "review_overlap"

    year_a = document_a.publication_year
    year_b = document_b.publication_year

    if (
        year_a is not None
        and year_b is not None
        and year_a != year_b
    ):
        if year_a > year_b:
            return (
                document_a.document_id,
                document_b.document_id,
                "deprecate_older",
            )

        return (
            document_b.document_id,
            document_a.document_id,
            "deprecate_older",
        )

    if document_a.is_active != document_b.is_active:
        primary = (
            document_a
            if document_a.is_active
            else document_b
        )
        superseded = (
            document_b
            if document_a.is_active
            else document_a
        )

        return (
            primary.document_id,
            superseded.document_id,
            "archive_duplicate",
        )

    if document_a.metadata_reviewed != document_b.metadata_reviewed:
        primary = (
            document_a
            if document_a.metadata_reviewed
            else document_b
        )
        superseded = (
            document_b
            if document_a.metadata_reviewed
            else document_a
        )

        return (
            primary.document_id,
            superseded.document_id,
            "archive_duplicate",
        )

    return None, None, "review_manually"


def _classify_relationship(
    *,
    exact_hash_match: bool,
    isbn_match: bool,
    title_similarity: float,
    author_similarity: float,
    metadata_overlap: float,
    content_overlap: float,
    edition_differs: bool,
) -> tuple[str | None, float, list[str]]:
    reasons: list[str] = []

    if exact_hash_match:
        return (
            "exact_duplicate",
            1.0,
            ["The SHA-256 content hashes are identical."],
        )

    if (
        content_overlap >= 0.97
        and title_similarity >= 0.85
    ):
        reasons.extend(
            [
                "The sampled text is nearly identical.",
                "The normalized titles are highly similar.",
            ]
        )

        return "exact_duplicate", 0.98, reasons

    if isbn_match and title_similarity >= 0.70:
        reasons.append(
            "The documents share an ISBN identifier."
        )

        if edition_differs:
            reasons.append(
                "Publication year or edition information differs."
            )
            return "different_edition", 0.95, reasons

        return "same_edition", 0.97, reasons

    if (
        title_similarity >= 0.88
        and author_similarity >= 0.65
        and edition_differs
    ):
        confidence = (
            title_similarity * 0.35
            + author_similarity * 0.20
            + content_overlap * 0.30
            + metadata_overlap * 0.15
        )

        reasons.extend(
            [
                "The title and author are highly similar.",
                "Publication year or edition information differs.",
            ]
        )

        if content_overlap >= 0.30:
            reasons.append(
                "The sampled content also overlaps."
            )

        return (
            "different_edition",
            round(max(confidence, 0.65), 4),
            reasons,
        )

    if content_overlap >= 0.70:
        confidence = (
            content_overlap * 0.55
            + title_similarity * 0.20
            + author_similarity * 0.10
            + metadata_overlap * 0.15
        )

        reasons.append(
            "The documents contain substantial sampled-text overlap."
        )

        return (
            "high_content_overlap",
            round(confidence, 4),
            reasons,
        )

    if (
        metadata_overlap >= 0.55
        and (
            title_similarity >= 0.35
            or author_similarity >= 0.35
        )
    ):
        confidence = (
            metadata_overlap * 0.60
            + title_similarity * 0.20
            + author_similarity * 0.20
        )

        reasons.append(
            "The documents cover many of the same topics, "
            "technologies, tags, or domains."
        )

        return (
            "related_topic",
            round(confidence, 4),
            reasons,
        )

    return None, 0.0, []


def _pair_key(
    document_a_id: str,
    document_b_id: str,
) -> str:
    first, second = sorted(
        [document_a_id, document_b_id]
    )

    return f"{first}:{second}"


def evaluate_document_pair(
    *,
    document_a: Document,
    document_b: Document,
    text_a: str | None,
    text_b: str | None,
    shingle_size: int,
) -> dict[str, Any] | None:
    exact_hash_match = bool(
        document_a.content_hash
        and document_b.content_hash
        and document_a.content_hash
        == document_b.content_hash
    )

    isbn_match = bool(
        _isbn_values(document_a)
        & _isbn_values(document_b)
    )

    title_similarity = _text_similarity(
        document_a.title or document_a.filename,
        document_b.title or document_b.filename,
    )

    author_similarity = _text_similarity(
        document_a.author,
        document_b.author,
    )

    metadata_overlap = _jaccard(
        _metadata_terms(document_a),
        _metadata_terms(document_b),
    )

    content_overlap = _content_overlap(
        text_a,
        text_b,
        shingle_size,
    )

    relationship_type, confidence, reasons = (
        _classify_relationship(
            exact_hash_match=exact_hash_match,
            isbn_match=isbn_match,
            title_similarity=title_similarity,
            author_similarity=author_similarity,
            metadata_overlap=metadata_overlap,
            content_overlap=content_overlap,
            edition_differs=_edition_differs(
                document_a,
                document_b,
            ),
        )
    )

    if not relationship_type:
        return None

    (
        recommended_primary,
        recommended_superseded,
        recommended_action,
    ) = _recommend_primary(
        document_a,
        document_b,
        relationship_type,
    )

    first, second = sorted(
        [document_a, document_b],
        key=lambda item: item.document_id,
    )

    return {
        "pair_key": _pair_key(
            document_a.document_id,
            document_b.document_id,
        ),
        "document_a_id": first.document_id,
        "document_b_id": second.document_id,
        "relationship_type": relationship_type,
        "exact_hash_match": exact_hash_match,
        "isbn_match": isbn_match,
        "title_similarity": title_similarity,
        "author_similarity": author_similarity,
        "metadata_overlap_score": metadata_overlap,
        "content_overlap_score": content_overlap,
        "confidence": confidence,
        "reasons": reasons,
        "document_a_snapshot": _document_snapshot(first),
        "document_b_snapshot": _document_snapshot(second),
        "recommended_primary_document_id": (
            recommended_primary
        ),
        "recommended_superseded_document_id": (
            recommended_superseded
        ),
        "recommended_action": recommended_action,
        "detector_version": DETECTOR_VERSION,
    }


def upsert_relationship(
    *,
    db: Session,
    evidence: dict[str, Any],
) -> BookRelationship:
    relationship = db.scalar(
        select(BookRelationship).where(
            BookRelationship.pair_key
            == evidence["pair_key"]
        )
    )

    if relationship is None:
        relationship = BookRelationship(
            status="pending",
            **evidence,
        )
        db.add(relationship)

    else:
        # Preserve a human decision during rescans.
        existing_status = relationship.status

        for field_name, value in evidence.items():
            setattr(
                relationship,
                field_name,
                value,
            )

        relationship.status = existing_status

    db.flush()
    return relationship


def scan_document_relationships(
    *,
    db: Session,
    target_document: Document,
    comparison_documents: list[Document],
    content_sample_characters: int,
    shingle_size: int,
    minimum_confidence: float,
) -> tuple[list[BookRelationship], list[str]]:
    warnings: list[str] = []

    target_text = _safe_document_sample(
        target_document,
        content_sample_characters,
    )

    if target_text is None:
        warnings.append(
            "The target document had no readable parsed text. "
            "Detection used metadata only."
        )

    relationships: list[BookRelationship] = []

    for comparison_document in comparison_documents:
        comparison_text = _safe_document_sample(
            comparison_document,
            content_sample_characters,
        )

        evidence = evaluate_document_pair(
            document_a=target_document,
            document_b=comparison_document,
            text_a=target_text,
            text_b=comparison_text,
            shingle_size=shingle_size,
        )

        if not evidence:
            continue

        if evidence["confidence"] < minimum_confidence:
            continue

        relationship = upsert_relationship(
            db=db,
            evidence=evidence,
        )

        relationships.append(relationship)

    db.commit()

    for relationship in relationships:
        db.refresh(relationship)

    relationships.sort(
        key=lambda item: item.confidence,
        reverse=True,
    )

    return relationships, warnings