from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.book_curation import BookCuration
from app.models.book_relationship import (
    BookRelationship,
)
from app.models.document import Document
from app.schemas.book_curator_dashboard import (
    BookCurationQueueItem,
    BookCuratorDashboardResponse,
    BookCuratorDashboardStats,
)
from app.schemas.book_ranking import RankingPurpose
from app.services.book_ranking import (
    calculate_book_ranking,
    document_matches_filters,
)


router = APIRouter(
    prefix="/book-curator-dashboard",
    tags=["book-curator-dashboard"],
)


def _load_relationships(
    *,
    db: Session,
    document_ids: list[str],
) -> list[BookRelationship]:
    if not document_ids:
        return []

    statement = (
        select(BookRelationship)
        .where(
            or_(
                BookRelationship.document_a_id.in_(
                    document_ids
                ),
                BookRelationship.document_b_id.in_(
                    document_ids
                ),
            )
        )
        .order_by(
            BookRelationship.confidence.desc(),
            BookRelationship.updated_at.desc(),
        )
    )

    return list(
        db.scalars(statement).all()
    )


def _relationship_map(
    relationships: list[BookRelationship],
) -> dict[str, list[BookRelationship]]:
    result: dict[
        str,
        list[BookRelationship],
    ] = defaultdict(list)

    for relationship in relationships:
        result[
            relationship.document_a_id
        ].append(relationship)

        result[
            relationship.document_b_id
        ].append(relationship)

    return result


@router.get(
    "",
    response_model=BookCuratorDashboardResponse,
)
def get_book_curator_dashboard(
    purpose: RankingPurpose = Query(
        default="general"
    ),
    domain: str | None = Query(default=None),
    topic: str | None = Query(default=None),
    technology: str | None = Query(default=None),
    audience_level: str | None = Query(
        default=None
    ),
    top_books_limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    review_queue_limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    relationship_limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(Document, BookCuration)
        .outerjoin(
            BookCuration,
            BookCuration.document_id
            == Document.document_id,
        )
        .order_by(Document.updated_at.desc())
    ).all()

    filtered_rows: list[
        tuple[Document, BookCuration | None]
    ] = []

    for document, curation in rows:
        if not document_matches_filters(
            document,
            domain=domain,
            topic=topic,
            technology=technology,
        ):
            continue

        filtered_rows.append(
            (document, curation)
        )

    document_ids = [
        document.document_id
        for document, _ in filtered_rows
    ]

    relationships = _load_relationships(
        db=db,
        document_ids=document_ids,
    )

    relationships_by_document = (
        _relationship_map(relationships)
    )

    ranked_books = []

    for document, curation in filtered_rows:
        if curation is None:
            continue

        if curation.evaluation_status != "approved":
            continue

        if not document.is_active:
            continue

        if document.is_deprecated:
            continue

        ranking = calculate_book_ranking(
            document=document,
            curation=curation,
            relationships=(
                relationships_by_document.get(
                    document.document_id,
                    [],
                )
            ),
            purpose=purpose,
            requested_audience=audience_level,
        )

        ranked_books.append(ranking)

    ranked_books.sort(
        key=lambda item: (
            item.ranking_score,
            item.publication_year or 0,
        ),
        reverse=True,
    )

    top_books = ranked_books[
        :top_books_limit
    ]

    review_queue = []

    reviewable_statuses = {
        "pending",
        "generating",
        "failed",
    }

    status_sort_order = {
        "pending": 0,
        "failed": 1,
        "generating": 2,
    }

    for document, curation in filtered_rows:
        if curation is None:
            continue

        if (
            curation.evaluation_status
            not in reviewable_statuses
        ):
            continue

        review_queue.append(
            BookCurationQueueItem(
                document_id=document.document_id,
                curation_id=curation.curation_id,
                filename=document.filename,
                title=document.title,
                author=document.author,
                publication_year=(
                    document.publication_year
                ),
                evaluation_status=(
                    curation.evaluation_status
                ),
                overall_score=(
                    curation.overall_score
                ),
                audience_level=(
                    curation.audience_level
                ),
                recommended_role=(
                    curation.recommended_role
                ),
                library_priority=(
                    curation.library_priority
                ),
                evaluation_model=(
                    curation.evaluation_model
                ),
                evaluation_error=(
                    curation.evaluation_error
                ),
                evaluated_at=(
                    curation.evaluated_at
                ),
                reviewed_at=(
                    curation.reviewed_at
                ),
                updated_at=(
                    curation.updated_at
                ),
            )
        )

    review_queue.sort(
        key=lambda item: (
            status_sort_order.get(
                item.evaluation_status,
                99,
            ),
            item.updated_at
            or datetime.min.replace(
                tzinfo=timezone.utc
            ),
        )
    )

    pending_relationships = [
        relationship
        for relationship in relationships
        if relationship.status == "pending"
    ][:relationship_limit]

    approved_evaluations = 0
    pending_evaluations = 0
    generating_evaluations = 0
    failed_evaluations = 0
    rejected_evaluations = 0
    not_evaluated = 0
    essential_books = 0

    active_documents = 0
    deprecated_documents = 0

    for document, curation in filtered_rows:
        if document.is_active:
            active_documents += 1

        if document.is_deprecated:
            deprecated_documents += 1

        if curation is None:
            not_evaluated += 1
            continue

        status = curation.evaluation_status

        if status == "approved":
            approved_evaluations += 1
        elif status == "pending":
            pending_evaluations += 1
        elif status == "generating":
            generating_evaluations += 1
        elif status == "failed":
            failed_evaluations += 1
        elif status == "rejected":
            rejected_evaluations += 1
        else:
            not_evaluated += 1

        if (
            status == "approved"
            and curation.library_priority
            == "essential"
        ):
            essential_books += 1

    visible_relationships = [
        relationship
        for relationship in relationships
        if relationship.status != "rejected"
    ]

    stats = BookCuratorDashboardStats(
        total_documents=len(filtered_rows),
        active_documents=active_documents,
        deprecated_documents=(
            deprecated_documents
        ),
        approved_evaluations=(
            approved_evaluations
        ),
        pending_evaluations=pending_evaluations,
        generating_evaluations=(
            generating_evaluations
        ),
        failed_evaluations=failed_evaluations,
        rejected_evaluations=(
            rejected_evaluations
        ),
        not_evaluated=not_evaluated,
        essential_books=essential_books,
        top_pick_books=sum(
            1
            for ranking in ranked_books
            if ranking.recommendation_tier
            == "top_pick"
        ),
        pending_relationships=len(
            pending_relationships
        ),
        exact_duplicates=sum(
            1
            for relationship
            in visible_relationships
            if relationship.relationship_type
            == "exact_duplicate"
        ),
        different_editions=sum(
            1
            for relationship
            in visible_relationships
            if relationship.relationship_type
            == "different_edition"
        ),
        high_content_overlaps=sum(
            1
            for relationship
            in visible_relationships
            if relationship.relationship_type
            == "high_content_overlap"
        ),
    )

    warnings: list[str] = []

    if not approved_evaluations:
        warnings.append(
            "No approved book evaluations were "
            "found for the selected filters."
        )

    return BookCuratorDashboardResponse(
        generated_at=datetime.now(timezone.utc),
        purpose=purpose,
        filters={
            "domain": domain,
            "topic": topic,
            "technology": technology,
            "audience_level": audience_level,
        },
        stats=stats,
        top_books=top_books,
        review_queue=review_queue[
            :review_queue_limit
        ],
        pending_relationships=(
            pending_relationships
        ),
        warnings=warnings,
    )