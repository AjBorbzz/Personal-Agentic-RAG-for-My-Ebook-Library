from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    delete,
    func,
    select,
)
from sqlalchemy.orm import Session

from app.models.book_skill_mapping import (
    BookSkillEvidence,
    BookSkillMapping,
)
from app.models.document import Document
from app.models.skill_taxonomy import (
    ProficiencyLevel,
    Skill,
    SkillCategory,
    SkillDomain,
)
from app.schemas.book_skill_candidate import (
    BookSkillCandidate,
)
from app.schemas.book_skill_mapping import (
    BookSkillEvidenceResponse,
    BookSkillMappingResponse,
)
from app.schemas.book_skill_review import (
    BookSkillReviewResponse,
    BookSkillReviewResult,
    ProficiencyLevelSummary,
)
from app.services.book_metadata_enrichment import (
    load_document_text,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _get_mapping(
    db: Session,
    mapping_id: str,
) -> BookSkillMapping:
    mapping = db.get(
        BookSkillMapping,
        mapping_id,
    )

    if mapping is None:
        raise ValueError(
            "Book-to-skill mapping was not found."
        )

    return mapping


def _get_document(
    db: Session,
    document_id: str,
) -> Document:
    document = db.get(
        Document,
        document_id,
    )

    if document is None:
        raise ValueError(
            "The mapped document was not found."
        )

    return document


def _get_skill(
    db: Session,
    skill_id: str,
) -> Skill:
    skill = db.get(
        Skill,
        skill_id,
    )

    if skill is None:
        raise ValueError(
            "The mapped skill was not found."
        )

    return skill


def _get_level_by_code(
    db: Session,
    code: str,
) -> ProficiencyLevel:
    level = db.scalar(
        select(ProficiencyLevel).where(
            ProficiencyLevel.code == code
        )
    )

    if level is None:
        raise ValueError(
            "Unknown proficiency level code: "
            f"'{code}'."
        )

    return level


def _level_summary(
    level: ProficiencyLevel | None,
) -> ProficiencyLevelSummary | None:
    if level is None:
        return None

    return ProficiencyLevelSummary(
        level_id=level.level_id,
        code=level.code,
        name=level.name,
        level_order=level.level_order,
    )


def _normalize_excerpt(
    value: str,
) -> str:
    return " ".join(
        value.split()
    ).casefold()


def _load_candidate(
    *,
    mapping: BookSkillMapping,
    edited_candidate: (
        BookSkillCandidate | None
    ),
) -> BookSkillCandidate:
    if edited_candidate is not None:
        return edited_candidate

    if not mapping.candidate_payload:
        raise ValueError(
            "This mapping has no candidate "
            "payload to review."
        )

    return BookSkillCandidate.model_validate(
        mapping.candidate_payload
    )


def _validate_candidate_skill(
    *,
    candidate: BookSkillCandidate,
    skill: Skill,
) -> None:
    if candidate.skill_slug != skill.slug:
        raise ValueError(
            "The candidate skill slug does not "
            "match the mapping's canonical skill. "
            f"Expected '{skill.slug}', received "
            f"'{candidate.skill_slug}'."
        )


def _validate_primary_skill_limit(
    *,
    db: Session,
    mapping: BookSkillMapping,
    candidate: BookSkillCandidate,
) -> None:
    if not candidate.is_primary_skill:
        return

    approved_primary_count = int(
        db.scalar(
            select(func.count())
            .select_from(BookSkillMapping)
            .where(
                BookSkillMapping.document_id
                == mapping.document_id,
                BookSkillMapping.mapping_id
                != mapping.mapping_id,
                BookSkillMapping.mapping_status
                == "approved",
                BookSkillMapping.is_primary_skill
                .is_(True),
            )
        )
        or 0
    )

    if approved_primary_count >= 3:
        raise ValueError(
            "A document may have no more than "
            "three approved primary skills."
        )


def _validate_evidence(
    *,
    document: Document,
    candidate: BookSkillCandidate,
) -> None:
    evidence_with_excerpt = [
        evidence
        for evidence in candidate.evidence
        if evidence.excerpt
        and evidence.evidence_type
        not in {
            "metadata",
            "manual",
        }
    ]

    if not evidence_with_excerpt:
        return

    full_text = load_document_text(document)
    normalized_source = _normalize_excerpt(
        full_text
    )

    for evidence in evidence_with_excerpt:
        assert evidence.excerpt is not None

        normalized_excerpt = (
            _normalize_excerpt(
                evidence.excerpt
            )
        )

        if (
            normalized_excerpt
            not in normalized_source
        ):
            raise ValueError(
                "An evidence excerpt could not "
                "be verified in the parsed book "
                "text."
            )


def _has_trusted_mapping(
    mapping: BookSkillMapping,
) -> bool:
    return bool(
        mapping.reviewed_at
        and (
            mapping.coverage_level is not None
            or mapping.relevance_score is not None
            or mapping.coverage_summary
        )
    )


def build_book_skill_review_response(
    *,
    db: Session,
    mapping: BookSkillMapping,
    reviewed_action: str | None = None,
) -> BookSkillReviewResponse:
    document = _get_document(
        db,
        mapping.document_id,
    )

    skill = _get_skill(
        db,
        mapping.skill_id,
    )

    domain = db.get(
        SkillDomain,
        skill.domain_id,
    )

    if domain is None:
        raise ValueError(
            "The skill domain was not found."
        )

    category = None

    if skill.category_id:
        category = db.get(
            SkillCategory,
            skill.category_id,
        )

    evidence = list(
        db.scalars(
            select(BookSkillEvidence)
            .where(
                BookSkillEvidence.mapping_id
                == mapping.mapping_id
            )
            .order_by(
                BookSkillEvidence.display_order,
                BookSkillEvidence.created_at,
            )
        ).all()
    )

    entry_level = None

    if mapping.recommended_entry_level_id:
        entry_level = db.get(
            ProficiencyLevel,
            mapping.recommended_entry_level_id,
        )

    exit_level = None

    if mapping.recommended_exit_level_id:
        exit_level = db.get(
            ProficiencyLevel,
            mapping.recommended_exit_level_id,
        )

    document_title = (
        document.title
        or document.filename
        or document.document_id
    )

    return BookSkillReviewResponse(
        mapping=(
            BookSkillMappingResponse
            .model_validate(mapping)
        ),
        document_id=document.document_id,
        document_title=document_title,
        skill_id=skill.skill_id,
        skill_slug=skill.slug,
        skill_name=skill.name,
        domain_name=domain.name,
        category_name=(
            category.name
            if category
            else None
        ),
        candidate=mapping.candidate_payload,
        trusted_evidence=[
            BookSkillEvidenceResponse
            .model_validate(item)
            for item in evidence
        ],
        entry_level=_level_summary(
            entry_level
        ),
        exit_level=_level_summary(
            exit_level
        ),
        reviewed_action=reviewed_action,
    )


def approve_book_skill_mapping(
    *,
    db: Session,
    mapping: BookSkillMapping,
    edited_candidate: (
        BookSkillCandidate | None
    ),
    review_notes: str | None,
) -> BookSkillReviewResult:
    candidate = _load_candidate(
        mapping=mapping,
        edited_candidate=edited_candidate,
    )

    skill = _get_skill(
        db,
        mapping.skill_id,
    )

    document = _get_document(
        db,
        mapping.document_id,
    )

    _validate_candidate_skill(
        candidate=candidate,
        skill=skill,
    )

    _validate_primary_skill_limit(
        db=db,
        mapping=mapping,
        candidate=candidate,
    )

    entry_level = _get_level_by_code(
        db,
        candidate.recommended_entry_level_code,
    )

    exit_level = _get_level_by_code(
        db,
        candidate.recommended_exit_level_code,
    )

    if (
        entry_level.level_order
        > exit_level.level_order
    ):
        raise ValueError(
            "Recommended entry proficiency "
            "cannot be higher than recommended "
            "exit proficiency."
        )

    _validate_evidence(
        document=document,
        candidate=candidate,
    )

    reviewed_at = utc_now()

    candidate_payload: dict[str, Any] = (
        candidate.model_dump()
    )

    candidate_payload[
        "recommended_entry_level_id"
    ] = entry_level.level_id

    candidate_payload[
        "recommended_exit_level_id"
    ] = exit_level.level_id

    mapping.mapping_status = "approved"
    mapping.coverage_level = (
        candidate.coverage_level
    )
    mapping.is_primary_skill = (
        candidate.is_primary_skill
    )

    mapping.relevance_score = (
        candidate.relevance_score
    )
    mapping.coverage_score = (
        candidate.coverage_score
    )
    mapping.depth_score = (
        candidate.depth_score
    )
    mapping.practicality_score = (
        candidate.practicality_score
    )
    mapping.confidence = (
        candidate.confidence
    )

    mapping.recommended_entry_level_id = (
        entry_level.level_id
    )
    mapping.recommended_exit_level_id = (
        exit_level.level_id
    )

    mapping.coverage_summary = (
        candidate.coverage_summary
    )
    mapping.learning_outcomes = list(
        candidate.learning_outcomes
    )
    mapping.covered_topics = list(
        candidate.covered_topics
    )
    mapping.limitations = list(
        candidate.limitations
    )

    mapping.mapping_source = "llm_reviewed"
    mapping.candidate_payload = (
        candidate_payload
    )
    mapping.candidate_error = None

    mapping.review_notes = review_notes
    mapping.reviewed_at = reviewed_at

    db.execute(
        delete(BookSkillEvidence).where(
            BookSkillEvidence.mapping_id
            == mapping.mapping_id
        )
    )

    for index, evidence in enumerate(
        candidate.evidence
    ):
        db.add(
            BookSkillEvidence(
                mapping_id=mapping.mapping_id,
                evidence_type=(
                    evidence.evidence_type
                ),
                chapter_title=(
                    evidence.chapter_title
                ),
                section_title=(
                    evidence.section_title
                ),
                page_start=(
                    evidence.page_start
                ),
                page_end=evidence.page_end,
                excerpt=evidence.excerpt,
                confidence=(
                    evidence.confidence
                ),
                display_order=index,
            )
        )

    db.commit()
    db.refresh(mapping)

    review = (
        build_book_skill_review_response(
            db=db,
            mapping=mapping,
            reviewed_action="approve",
        )
    )

    return BookSkillReviewResult(
        mapping_id=mapping.mapping_id,
        action="approve",
        final_status=mapping.mapping_status,
        evidence_created=len(
            candidate.evidence
        ),
        reviewed_at=reviewed_at,
        review=review,
    )


def reject_book_skill_mapping(
    *,
    db: Session,
    mapping: BookSkillMapping,
    review_notes: str | None,
) -> BookSkillReviewResult:
    reviewed_at = utc_now()

    had_trusted_mapping = (
        _has_trusted_mapping(mapping)
    )

    # When a previously approved mapping was
    # regenerated, rejecting the new candidate
    # restores the existing trusted mapping.
    if had_trusted_mapping:
        mapping.mapping_status = "approved"
        mapping.mapping_source = "llm_reviewed"
    else:
        mapping.mapping_status = "rejected"

    mapping.review_notes = review_notes
    mapping.reviewed_at = reviewed_at

    db.commit()
    db.refresh(mapping)

    review = (
        build_book_skill_review_response(
            db=db,
            mapping=mapping,
            reviewed_action="reject",
        )
    )

    return BookSkillReviewResult(
        mapping_id=mapping.mapping_id,
        action="reject",
        final_status=mapping.mapping_status,
        evidence_created=0,
        reviewed_at=reviewed_at,
        review=review,
    )


def review_book_skill_mapping(
    *,
    db: Session,
    mapping_id: str,
    action: str,
    edited_candidate: (
        BookSkillCandidate | None
    ),
    review_notes: str | None,
) -> BookSkillReviewResult:
    mapping = _get_mapping(
        db,
        mapping_id,
    )

    if action == "approve":
        return approve_book_skill_mapping(
            db=db,
            mapping=mapping,
            edited_candidate=(
                edited_candidate
            ),
            review_notes=review_notes,
        )

    if action == "reject":
        return reject_book_skill_mapping(
            db=db,
            mapping=mapping,
            review_notes=review_notes,
        )

    raise ValueError(
        f"Unsupported review action: {action}"
    )