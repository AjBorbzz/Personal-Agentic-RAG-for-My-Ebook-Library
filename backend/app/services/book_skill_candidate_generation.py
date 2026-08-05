import asyncio
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.book_skill_mapping import (
    BookSkillMapping,
)
from app.models.document import Document
from app.models.skill_taxonomy import (
    ProficiencyLevel,
    Skill,
    SkillAlias,
    SkillCategory,
    SkillDomain,
)
from app.retrieval.book_skill_mapping_prompt import (
    build_book_skill_mapping_prompt,
)
from app.schemas.book_skill_candidate import (
    BookSkillCandidate,
    BookSkillCandidateBatch,
    GeneratedBookSkillMappingResponse,
    GenerateBookSkillCandidatesResponse,
    ShortlistedSkillResponse,
)
from app.schemas.book_skill_mapping import (
    BookSkillMappingResponse,
)
from app.services.book_metadata_enrichment import (
    load_document_text,
    sample_document_text,
)
from app.services.ollama import (
    generate_structured_text,
)


WORD_PATTERN = re.compile(
    r"[a-z0-9][a-z0-9+#._-]*",
    re.IGNORECASE,
)


@dataclass
class SkillContext:
    skill: Skill
    domain: SkillDomain
    category: SkillCategory | None
    aliases: list[SkillAlias]


def _normalize(value: str | None) -> str:
    if not value:
        return ""

    value = value.lower().strip()
    value = re.sub(
        r"[^a-z0-9+#._-]+",
        " ",
        value,
    )

    return " ".join(value.split())


def _tokens(value: str | None) -> set[str]:
    if not value:
        return set()

    return {
        token.lower()
        for token in WORD_PATTERN.findall(value)
        if len(token) >= 2
    }


def _list_text(value: Any) -> str:
    if not isinstance(value, list):
        return ""

    return " ".join(
        str(item)
        for item in value
        if item is not None
    )


def _document_metadata(
    document: Document,
) -> dict[str, Any]:
    return {
        "document_id": document.document_id,
        "filename": document.filename,
        "title": document.title,
        "subtitle": getattr(
            document,
            "subtitle",
            None,
        ),
        "author": document.author,
        "description": getattr(
            document,
            "description",
            None,
        ),
        "primary_domain": (
            document.primary_domain
        ),
        "domains": document.domains or [],
        "topics": document.topics or [],
        "technologies": (
            document.technologies or []
        ),
        "tags": document.tags or [],
        "tool_name": document.tool_name,
        "tool_version": document.tool_version,
        "publication_year": (
            document.publication_year
        ),
        "difficulty_level": getattr(
            document,
            "difficulty_level",
            None,
        ),
        "metadata_reviewed": (
            document.metadata_reviewed
        ),
    }


def _metadata_search_text(
    document: Document,
) -> str:
    parts = [
        document.filename,
        document.title,
        getattr(document, "subtitle", None),
        document.author,
        getattr(document, "description", None),
        document.primary_domain,
        _list_text(document.domains),
        _list_text(document.topics),
        _list_text(document.technologies),
        _list_text(document.tags),
        document.tool_name,
        document.tool_version,
    ]

    return _normalize(
        " ".join(
            str(part)
            for part in parts
            if part
        )
    )


def _load_skill_contexts(
    db: Session,
) -> list[SkillContext]:
    skills = list(
        db.scalars(
            select(Skill)
            .where(
                Skill.is_active.is_(True),
                Skill.is_deprecated.is_(False),
            )
            .order_by(Skill.name)
        ).all()
    )

    if not skills:
        return []

    domain_ids = {
        skill.domain_id
        for skill in skills
    }

    category_ids = {
        skill.category_id
        for skill in skills
        if skill.category_id
    }

    skill_ids = {
        skill.skill_id
        for skill in skills
    }

    domains = list(
        db.scalars(
            select(SkillDomain).where(
                SkillDomain.domain_id.in_(
                    domain_ids
                )
            )
        ).all()
    )

    categories = []

    if category_ids:
        categories = list(
            db.scalars(
                select(SkillCategory).where(
                    SkillCategory.category_id.in_(
                        category_ids
                    )
                )
            ).all()
        )

    aliases = list(
        db.scalars(
            select(SkillAlias).where(
                SkillAlias.skill_id.in_(
                    skill_ids
                )
            )
        ).all()
    )

    domain_by_id = {
        domain.domain_id: domain
        for domain in domains
    }

    category_by_id = {
        category.category_id: category
        for category in categories
    }

    aliases_by_skill: dict[
        str,
        list[SkillAlias],
    ] = {}

    for alias in aliases:
        aliases_by_skill.setdefault(
            alias.skill_id,
            [],
        ).append(alias)

    contexts = []

    for skill in skills:
        domain = domain_by_id.get(
            skill.domain_id
        )

        if not domain:
            continue

        category = (
            category_by_id.get(
                skill.category_id
            )
            if skill.category_id
            else None
        )

        contexts.append(
            SkillContext(
                skill=skill,
                domain=domain,
                category=category,
                aliases=aliases_by_skill.get(
                    skill.skill_id,
                    [],
                ),
            )
        )

    return contexts


def _rank_skill(
    *,
    context: SkillContext,
    metadata_text: str,
    source_text: str,
    metadata_tokens: set[str],
) -> tuple[float, list[str]]:
    score = 0.0
    matched_terms: list[str] = []

    skill = context.skill

    skill_name = _normalize(skill.name)
    skill_slug = _normalize(
        skill.slug.replace("-", " ")
    )

    phrases = [
        skill_name,
        skill_slug,
    ]

    phrases.extend(
        _normalize(alias.alias)
        for alias in context.aliases
    )

    seen_phrases: set[str] = set()

    for phrase in phrases:
        if (
            not phrase
            or phrase in seen_phrases
        ):
            continue

        seen_phrases.add(phrase)

        if phrase in metadata_text:
            score += 6.0
            matched_terms.append(
                f"metadata:{phrase}"
            )
        elif phrase in source_text:
            score += 3.0
            matched_terms.append(
                f"content:{phrase}"
            )

    skill_tokens = _tokens(
        " ".join(
            [
                skill.name,
                skill.slug.replace("-", " "),
                _list_text(skill.tags),
            ]
        )
    )

    overlapping_tokens = (
        skill_tokens & metadata_tokens
    )

    if overlapping_tokens:
        token_score = min(
            len(overlapping_tokens) * 1.5,
            6.0,
        )

        score += token_score

        matched_terms.extend(
            f"token:{token}"
            for token in sorted(
                overlapping_tokens
            )
        )

    domain_terms = {
        _normalize(context.domain.name),
        _normalize(context.domain.slug),
    }

    if any(
        term and term in metadata_text
        for term in domain_terms
    ):
        score += 2.0
        matched_terms.append(
            f"domain:{context.domain.slug}"
        )

    if context.category:
        category_terms = {
            _normalize(
                context.category.name
            ),
            _normalize(
                context.category.slug
            ),
        }

        if any(
            term and term in metadata_text
            for term in category_terms
        ):
            score += 1.5
            matched_terms.append(
                "category:"
                f"{context.category.slug}"
            )

    return round(score, 3), list(
        dict.fromkeys(matched_terms)
    )


def shortlist_skills(
    *,
    db: Session,
    document: Document,
    source_sample: str,
    maximum_candidates: int,
    minimum_score: float,
) -> tuple[
    list[ShortlistedSkillResponse],
    dict[str, SkillContext],
]:
    contexts = _load_skill_contexts(db)

    metadata_text = _metadata_search_text(
        document
    )
    source_text = _normalize(source_sample)

    metadata_tokens = _tokens(metadata_text)

    ranked: list[
        tuple[
            float,
            list[str],
            SkillContext,
        ]
    ] = []

    for context in contexts:
        score, matched_terms = _rank_skill(
            context=context,
            metadata_text=metadata_text,
            source_text=source_text,
            metadata_tokens=metadata_tokens,
        )

        if score < minimum_score:
            continue

        ranked.append(
            (
                score,
                matched_terms,
                context,
            )
        )

    ranked.sort(
        key=lambda item: (
            item[0],
            item[2].skill.name,
        ),
        reverse=True,
    )

    ranked = ranked[:maximum_candidates]

    responses: list[
        ShortlistedSkillResponse
    ] = []

    context_by_slug: dict[
        str,
        SkillContext,
    ] = {}

    for score, matched_terms, context in ranked:
        response = ShortlistedSkillResponse(
            skill_id=context.skill.skill_id,
            slug=context.skill.slug,
            name=context.skill.name,
            domain_name=context.domain.name,
            category_name=(
                context.category.name
                if context.category
                else None
            ),
            skill_type=context.skill.skill_type,
            difficulty_level=(
                context.skill.difficulty_level
            ),
            lexical_score=score,
            matched_terms=matched_terms,
        )

        responses.append(response)
        context_by_slug[
            context.skill.slug
        ] = context

    return responses, context_by_slug


def _level_map(
    db: Session,
) -> dict[str, ProficiencyLevel]:
    levels = list(
        db.scalars(
            select(ProficiencyLevel)
            .order_by(
                ProficiencyLevel.level_order
            )
        ).all()
    )

    return {
        level.code: level
        for level in levels
    }


def _normalized_excerpt(
    value: str,
) -> str:
    return " ".join(
        value.split()
    ).lower()


def _validated_evidence(
    *,
    candidate: BookSkillCandidate,
    source_sample: str,
    warnings: list[str],
) -> list[dict[str, Any]]:
    normalized_source = _normalized_excerpt(
        source_sample
    )

    evidence_items: list[
        dict[str, Any]
    ] = []

    for evidence in candidate.evidence:
        payload = evidence.model_dump()

        excerpt = evidence.excerpt

        if excerpt:
            normalized_excerpt = (
                _normalized_excerpt(excerpt)
            )

            if (
                normalized_excerpt
                not in normalized_source
            ):
                warnings.append(
                    "Removed an unsupported evidence "
                    f"excerpt for skill "
                    f"'{candidate.skill_slug}'."
                )

                payload["excerpt"] = None

        evidence_items.append(payload)

    return evidence_items


def _candidate_payload(
    *,
    candidate: BookSkillCandidate,
    entry_level: ProficiencyLevel,
    exit_level: ProficiencyLevel,
    evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = candidate.model_dump()

    payload[
        "recommended_entry_level_id"
    ] = entry_level.level_id

    payload[
        "recommended_exit_level_id"
    ] = exit_level.level_id

    payload["evidence"] = evidence

    return payload


async def generate_book_skill_candidates(
    *,
    db: Session,
    document: Document,
    max_source_characters: int,
    maximum_candidate_skills: int,
    maximum_mappings: int,
    minimum_shortlist_score: float,
    regenerate_approved: bool,
) -> GenerateBookSkillCandidatesResponse:
    warnings: list[str] = []

    full_text = load_document_text(document)

    source_sample, _ = sample_document_text(
        full_text,
        max_source_characters,
    )

    if not source_sample.strip():
        raise ValueError(
            "The document has no readable text."
        )

    shortlist, context_by_slug = (
        shortlist_skills(
            db=db,
            document=document,
            source_sample=source_sample,
            maximum_candidates=(
                maximum_candidate_skills
            ),
            minimum_score=(
                minimum_shortlist_score
            ),
        )
    )

    if not shortlist:
        raise ValueError(
            "No matching taxonomy skills were "
            "found for this document."
        )

    model_name = (
        settings.book_skill_mapping_model
    )

    prompt = build_book_skill_mapping_prompt(
        document_metadata=(
            _document_metadata(document)
        ),
        source_sample=source_sample,
        shortlisted_skills=shortlist,
        maximum_mappings=maximum_mappings,
    )

    raw_response = await asyncio.wait_for(
        generate_structured_text(
            prompt=prompt,
            json_schema=(
                BookSkillCandidateBatch
                .model_json_schema()
            ),
            model=model_name,
        ),
        timeout=300,
    )

    try:
        if isinstance(raw_response, str):
            generated = (
                BookSkillCandidateBatch
                .model_validate_json(
                    raw_response
                )
            )
        else:
            generated = (
                BookSkillCandidateBatch
                .model_validate(
                    raw_response
                )
            )

    except ValidationError as error:
        raise ValueError(
            "The language model returned an "
            "invalid book-to-skill candidate "
            f"payload: {error}"
        ) from error

    level_by_code = _level_map(db)

    required_level_codes = {
        "awareness",
        "foundational",
        "working",
        "advanced",
        "expert",
    }

    missing_level_codes = (
        required_level_codes
        - set(level_by_code)
    )

    if missing_level_codes:
        raise ValueError(
            "Missing proficiency levels: "
            + ", ".join(
                sorted(missing_level_codes)
            )
        )

    created_count = 0
    updated_count = 0
    skipped_count = 0

    generated_responses: list[
        GeneratedBookSkillMappingResponse
    ] = []

    seen_skill_slugs: set[str] = set()
    primary_count = 0

    candidates = sorted(
        generated.mappings,
        key=lambda item: (
            item.is_primary_skill,
            item.relevance_score,
            item.coverage_score,
        ),
        reverse=True,
    )[:maximum_mappings]

    for candidate in candidates:
        if candidate.skill_slug in seen_skill_slugs:
            warnings.append(
                "Ignored duplicate skill candidate: "
                f"'{candidate.skill_slug}'."
            )
            continue

        seen_skill_slugs.add(
            candidate.skill_slug
        )

        context = context_by_slug.get(
            candidate.skill_slug
        )

        if context is None:
            warnings.append(
                "Ignored skill outside the "
                "approved shortlist: "
                f"'{candidate.skill_slug}'."
            )
            continue

        if candidate.is_primary_skill:
            primary_count += 1

            if primary_count > 3:
                candidate.is_primary_skill = False

                warnings.append(
                    "Only three primary skills are "
                    "allowed. Demoted "
                    f"'{candidate.skill_slug}'."
                )

        entry_level = level_by_code[
            candidate
            .recommended_entry_level_code
        ]

        exit_level = level_by_code[
            candidate
            .recommended_exit_level_code
        ]

        if (
            entry_level.level_order
            > exit_level.level_order
        ):
            warnings.append(
                "Skipped skill with an invalid "
                "entry/exit proficiency range: "
                f"'{candidate.skill_slug}'."
            )

            skipped_count += 1

            generated_responses.append(
                GeneratedBookSkillMappingResponse(
                    skill_id=(
                        context.skill.skill_id
                    ),
                    skill_slug=(
                        context.skill.slug
                    ),
                    skill_name=(
                        context.skill.name
                    ),
                    created=False,
                    skipped=True,
                    skip_reason=(
                        "Entry proficiency is "
                        "higher than exit "
                        "proficiency."
                    ),
                    mapping=None,
                )
            )

            continue

        existing = db.scalar(
            select(BookSkillMapping).where(
                BookSkillMapping.document_id
                == document.document_id,
                BookSkillMapping.skill_id
                == context.skill.skill_id,
            )
        )

        if (
            existing is not None
            and existing.mapping_status
            == "approved"
            and not regenerate_approved
        ):
            skipped_count += 1

            generated_responses.append(
                GeneratedBookSkillMappingResponse(
                    skill_id=(
                        context.skill.skill_id
                    ),
                    skill_slug=(
                        context.skill.slug
                    ),
                    skill_name=(
                        context.skill.name
                    ),
                    created=False,
                    skipped=True,
                    skip_reason=(
                        "An approved mapping "
                        "already exists."
                    ),
                    mapping=(
                        BookSkillMappingResponse
                        .model_validate(existing)
                    ),
                )
            )

            continue

        evidence = _validated_evidence(
            candidate=candidate,
            source_sample=source_sample,
            warnings=warnings,
        )

        payload = _candidate_payload(
            candidate=candidate,
            entry_level=entry_level,
            exit_level=exit_level,
            evidence=evidence,
        )

        created = existing is None

        if existing is None:
            mapping = BookSkillMapping(
                document_id=(
                    document.document_id
                ),
                skill_id=(
                    context.skill.skill_id
                ),
                mapping_status="pending",
                mapping_source="llm",
                mapping_model=model_name,
                mapping_version=1,
                candidate_payload=payload,
                candidate_error=None,
                candidate_generated_at=(
                    datetime.now(
                        timezone.utc
                    )
                ),
            )

            db.add(mapping)
            db.flush()

            created_count += 1

        else:
            mapping = existing

            mapping.mapping_status = "pending"
            mapping.mapping_source = "llm"
            mapping.mapping_model = model_name
            mapping.mapping_version += 1
            mapping.candidate_payload = payload
            mapping.candidate_error = None
            mapping.candidate_generated_at = (
                datetime.now(
                    timezone.utc
                )
            )

            updated_count += 1

        generated_responses.append(
            GeneratedBookSkillMappingResponse(
                skill_id=context.skill.skill_id,
                skill_slug=context.skill.slug,
                skill_name=context.skill.name,
                created=created,
                skipped=False,
                skip_reason=None,
                mapping=(
                    BookSkillMappingResponse
                    .model_validate(mapping)
                ),
            )
        )

    db.commit()

    for item in generated_responses:
        if item.mapping is None:
            continue

        refreshed = db.get(
            BookSkillMapping,
            item.mapping.mapping_id,
        )

        if refreshed:
            item.mapping = (
                BookSkillMappingResponse
                .model_validate(refreshed)
            )

    return GenerateBookSkillCandidatesResponse(
        document_id=document.document_id,
        model=model_name,
        source_characters_used=len(
            source_sample
        ),
        shortlisted_skill_count=len(
            shortlist
        ),
        generated_candidate_count=len(
            generated_responses
        ),
        mappings_created=created_count,
        mappings_updated=updated_count,
        mappings_skipped=skipped_count,
        analysis_summary=(
            generated.analysis_summary
        ),
        shortlist=shortlist,
        generated_mappings=(
            generated_responses
        ),
        warnings=warnings,
    )