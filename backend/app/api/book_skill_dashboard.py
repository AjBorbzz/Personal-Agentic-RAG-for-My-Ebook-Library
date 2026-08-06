from collections import defaultdict
from statistics import mean

from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.book_skill_mapping import (
    BookSkillMapping,
)
from app.models.document import Document
from app.models.skill_taxonomy import (
    Skill,
    SkillCategory,
    SkillDomain,
)
from app.schemas.book_skill_dashboard import (
    BookCoverageSummary,
    BookSkillDashboardResponse,
    BookSkillDashboardStats,
    BookSkillDomainOption,
    BookSkillStatusCount,
    PendingBookSkillReview,
    SkillCoverageSummary,
    UnmappedSkillSummary,
)


router = APIRouter(
    prefix="/book-skill-dashboard",
    tags=["book-skill-dashboard"],
)


def _document_title(
    document: Document,
) -> str:
    return (
        document.title
        or document.filename
        or document.document_id
    )


def _score_value(
    value: float | None,
) -> float:
    return float(value or 0)


def _mapping_quality_score(
    mapping: BookSkillMapping,
) -> float:
    """
    Deterministic score used only for dashboard
    ranking.

    Relevance:    30%
    Coverage:     25%
    Depth:        25%
    Practicality: 20%
    """

    result = (
        _score_value(
            mapping.relevance_score
        )
        * 0.30
        + _score_value(
            mapping.coverage_score
        )
        * 0.25
        + _score_value(
            mapping.depth_score
        )
        * 0.25
        + _score_value(
            mapping.practicality_score
        )
        * 0.20
    )

    return round(result, 2)


def _average(
    values: list[float],
) -> float:
    if not values:
        return 0.0

    return round(mean(values), 2)


@router.get(
    "",
    response_model=BookSkillDashboardResponse,
)
def get_book_skill_dashboard(
    domain_slug: str | None = Query(
        default=None
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
):
    domains = list(
        db.scalars(
            select(SkillDomain)
            .where(
                SkillDomain.is_active.is_(True)
            )
            .order_by(
                SkillDomain.display_order,
                SkillDomain.name,
            )
        ).all()
    )

    domain_options = [
        BookSkillDomainOption(
            slug=domain.slug,
            name=domain.name,
        )
        for domain in domains
    ]

    mapping_statement = (
        select(
            BookSkillMapping,
            Document,
            Skill,
            SkillDomain,
            SkillCategory,
        )
        .join(
            Document,
            Document.document_id
            == BookSkillMapping.document_id,
        )
        .join(
            Skill,
            Skill.skill_id
            == BookSkillMapping.skill_id,
        )
        .join(
            SkillDomain,
            SkillDomain.domain_id
            == Skill.domain_id,
        )
        .outerjoin(
            SkillCategory,
            SkillCategory.category_id
            == Skill.category_id,
        )
        .order_by(
            BookSkillMapping.updated_at.desc()
        )
    )

    if domain_slug:
        mapping_statement = (
            mapping_statement.where(
                SkillDomain.slug
                == domain_slug
            )
        )

    mapping_rows = db.execute(
        mapping_statement
    ).all()

    skill_statement = (
        select(
            Skill,
            SkillDomain,
            SkillCategory,
        )
        .join(
            SkillDomain,
            SkillDomain.domain_id
            == Skill.domain_id,
        )
        .outerjoin(
            SkillCategory,
            SkillCategory.category_id
            == Skill.category_id,
        )
        .where(
            Skill.is_active.is_(True),
            Skill.is_deprecated.is_(False),
            SkillDomain.is_active.is_(True),
        )
        .order_by(
            SkillDomain.display_order,
            SkillCategory.display_order,
            Skill.name,
        )
    )

    if domain_slug:
        skill_statement = (
            skill_statement.where(
                SkillDomain.slug
                == domain_slug
            )
        )

    skill_rows = db.execute(
        skill_statement
    ).all()

    registered_documents = int(
        db.scalar(
            select(func.count())
            .select_from(Document)
        )
        or 0
    )

    status_counts_map: dict[str, int] = {
        "pending": 0,
        "approved": 0,
        "rejected": 0,
        "failed": 0,
        "generating": 0,
    }

    books_with_any_mappings: set[str] = set()
    books_with_approved_mappings: set[
        str
    ] = set()

    approved_skill_ids: set[str] = set()

    primary_mapping_count = 0

    approved_rows = []
    pending_rows = []

    for (
        mapping,
        document,
        skill,
        domain,
        category,
    ) in mapping_rows:
        books_with_any_mappings.add(
            document.document_id
        )

        status_counts_map[
            mapping.mapping_status
        ] = (
            status_counts_map.get(
                mapping.mapping_status,
                0,
            )
            + 1
        )

        if mapping.mapping_status == "approved":
            approved_rows.append(
                (
                    mapping,
                    document,
                    skill,
                    domain,
                    category,
                )
            )

            books_with_approved_mappings.add(
                document.document_id
            )

            approved_skill_ids.add(
                skill.skill_id
            )

            if mapping.is_primary_skill:
                primary_mapping_count += 1

        elif mapping.mapping_status == "pending":
            pending_rows.append(
                (
                    mapping,
                    document,
                    skill,
                    domain,
                    category,
                )
            )

    # -----------------------------------------
    # Top books
    # -----------------------------------------

    mappings_by_document = defaultdict(
        list
    )

    for row in approved_rows:
        mapping, document, *_ = row

        mappings_by_document[
            document.document_id
        ].append(row)

    top_books: list[
        BookCoverageSummary
    ] = []

    for document_rows in (
        mappings_by_document.values()
    ):
        first_mapping, document, *_ = (
            document_rows[0]
        )

        del first_mapping

        mappings = [
            row[0]
            for row in document_rows
        ]

        primary_skills = [
            row[2].name
            for row in document_rows
            if row[0].is_primary_skill
        ]

        top_books.append(
            BookCoverageSummary(
                document_id=(
                    document.document_id
                ),
                document_title=(
                    _document_title(document)
                ),
                author=getattr(
                    document,
                    "author",
                    None,
                ),
                approved_mapping_count=len(
                    mappings
                ),
                primary_skill_count=len(
                    primary_skills
                ),
                average_quality_score=_average(
                    [
                        _mapping_quality_score(
                            mapping
                        )
                        for mapping in mappings
                    ]
                ),
                average_relevance_score=_average(
                    [
                        _score_value(
                            mapping
                            .relevance_score
                        )
                        for mapping in mappings
                    ]
                ),
                average_coverage_score=_average(
                    [
                        _score_value(
                            mapping
                            .coverage_score
                        )
                        for mapping in mappings
                    ]
                ),
                average_depth_score=_average(
                    [
                        _score_value(
                            mapping.depth_score
                        )
                        for mapping in mappings
                    ]
                ),
                average_practicality_score=(
                    _average(
                        [
                            _score_value(
                                mapping
                                .practicality_score
                            )
                            for mapping in mappings
                        ]
                    )
                ),
                primary_skills=sorted(
                    primary_skills
                ),
            )
        )

    top_books.sort(
        key=lambda item: (
            item.average_quality_score,
            item.approved_mapping_count,
            item.primary_skill_count,
            item.document_title.casefold(),
        ),
        reverse=True,
    )

    top_books = top_books[:limit]

    # -----------------------------------------
    # Top skills
    # -----------------------------------------

    mappings_by_skill = defaultdict(list)

    for row in approved_rows:
        mapping, _, skill, *_ = row

        mappings_by_skill[
            skill.skill_id
        ].append(row)

    top_skills: list[
        SkillCoverageSummary
    ] = []

    for skill_rows_group in (
        mappings_by_skill.values()
    ):
        (
            _,
            _,
            skill,
            domain,
            category,
        ) = skill_rows_group[0]

        mappings = [
            row[0]
            for row in skill_rows_group
        ]

        document_ids = {
            row[1].document_id
            for row in skill_rows_group
        }

        primary_document_ids = {
            row[1].document_id
            for row in skill_rows_group
            if row[0].is_primary_skill
        }

        ranked_documents = sorted(
            skill_rows_group,
            key=lambda row:
                _mapping_quality_score(
                    row[0]
                ),
            reverse=True,
        )

        best_row = (
            ranked_documents[0]
            if ranked_documents
            else None
        )

        top_skills.append(
            SkillCoverageSummary(
                skill_id=skill.skill_id,
                skill_slug=skill.slug,
                skill_name=skill.name,
                domain_name=domain.name,
                category_name=(
                    category.name
                    if category
                    else None
                ),
                supporting_book_count=len(
                    document_ids
                ),
                primary_book_count=len(
                    primary_document_ids
                ),
                average_quality_score=_average(
                    [
                        _mapping_quality_score(
                            mapping
                        )
                        for mapping in mappings
                    ]
                ),
                average_relevance_score=_average(
                    [
                        _score_value(
                            mapping
                            .relevance_score
                        )
                        for mapping in mappings
                    ]
                ),
                average_coverage_score=_average(
                    [
                        _score_value(
                            mapping
                            .coverage_score
                        )
                        for mapping in mappings
                    ]
                ),
                average_depth_score=_average(
                    [
                        _score_value(
                            mapping.depth_score
                        )
                        for mapping in mappings
                    ]
                ),
                average_practicality_score=(
                    _average(
                        [
                            _score_value(
                                mapping
                                .practicality_score
                            )
                            for mapping in mappings
                        ]
                    )
                ),
                best_document_id=(
                    best_row[1].document_id
                    if best_row
                    else None
                ),
                best_document_title=(
                    _document_title(
                        best_row[1]
                    )
                    if best_row
                    else None
                ),
                best_document_score=(
                    _mapping_quality_score(
                        best_row[0]
                    )
                    if best_row
                    else None
                ),
            )
        )

    top_skills.sort(
        key=lambda item: (
            item.average_quality_score,
            item.supporting_book_count,
            item.primary_book_count,
            item.skill_name.casefold(),
        ),
        reverse=True,
    )

    top_skills = top_skills[:limit]

    # -----------------------------------------
    # Pending review queue
    # -----------------------------------------

    pending_reviews = [
        PendingBookSkillReview(
            mapping_id=mapping.mapping_id,
            document_id=document.document_id,
            document_title=(
                _document_title(document)
            ),
            skill_id=skill.skill_id,
            skill_name=skill.name,
            domain_name=domain.name,
            category_name=(
                category.name
                if category
                else None
            ),
            mapping_version=(
                mapping.mapping_version
            ),
            mapping_model=(
                mapping.mapping_model
            ),
            candidate_generated_at=(
                mapping
                .candidate_generated_at
            ),
            updated_at=mapping.updated_at,
        )
        for (
            mapping,
            document,
            skill,
            domain,
            category,
        ) in pending_rows[:limit]
    ]

    # -----------------------------------------
    # Unmapped skills
    # -----------------------------------------

    unmapped_skills = [
        UnmappedSkillSummary(
            skill_id=skill.skill_id,
            skill_slug=skill.slug,
            skill_name=skill.name,
            domain_name=domain.name,
            category_name=(
                category.name
                if category
                else None
            ),
            skill_type=skill.skill_type,
            difficulty_level=(
                skill.difficulty_level
            ),
        )
        for (
            skill,
            domain,
            category,
        ) in skill_rows
        if skill.skill_id
        not in approved_skill_ids
    ]

    unmapped_skills = (
        unmapped_skills[:limit]
    )

    active_skill_count = len(
        skill_rows
    )

    stats = BookSkillDashboardStats(
        registered_documents=(
            registered_documents
        ),
        books_with_any_mappings=len(
            books_with_any_mappings
        ),
        books_with_approved_mappings=len(
            books_with_approved_mappings
        ),
        total_mappings=len(
            mapping_rows
        ),
        pending_mappings=(
            status_counts_map.get(
                "pending",
                0,
            )
        ),
        approved_mappings=(
            status_counts_map.get(
                "approved",
                0,
            )
        ),
        rejected_mappings=(
            status_counts_map.get(
                "rejected",
                0,
            )
        ),
        failed_mappings=(
            status_counts_map.get(
                "failed",
                0,
            )
        ),
        primary_mappings=(
            primary_mapping_count
        ),
        active_skills=active_skill_count,
        skills_with_approved_books=len(
            approved_skill_ids
        ),
        unmapped_active_skills=(
            active_skill_count
            - len(approved_skill_ids)
        ),
    )

    status_counts = [
        BookSkillStatusCount(
            status=status,
            count=status_counts_map.get(
                status,
                0,
            ),
        )
        for status in [
            "pending",
            "approved",
            "rejected",
            "failed",
            "generating",
        ]
    ]

    return BookSkillDashboardResponse(
        domain_filter=domain_slug,
        domains=domain_options,
        stats=stats,
        status_counts=status_counts,
        top_books=top_books,
        top_skills=top_skills,
        pending_reviews=pending_reviews,
        unmapped_skills=unmapped_skills,
    )