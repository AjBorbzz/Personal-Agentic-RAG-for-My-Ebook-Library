from collections import defaultdict

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.book_curation import BookCuration
from app.models.book_relationship import (
    BookRelationship,
)
from app.models.document import Document
from app.schemas.book_ranking import (
    BookRankingItem,
    BookRankingListResponse,
    RankingPurpose,
)

from app.core.config import settings
from app.schemas.book_ranking import (
    BookRankingItem,
    BookRankingListResponse,
    BookRankingQdrantSyncResponse,
    RankingPurpose,
)
from app.services.book_ranking_qdrant_sync import (
    sync_book_ranking_to_qdrant,
)


from app.services.book_ranking import (
    calculate_book_ranking,
    document_matches_filters,
)

router = APIRouter(
    prefix="/book-rankings",
    tags=["book-rankings"],
)


def _load_relationship_map(
    db: Session,
    document_ids: list[str],
) -> dict[str, list[BookRelationship]]:
    relationship_map: dict[
        str,
        list[BookRelationship],
    ] = defaultdict(list)

    if not document_ids:
        return relationship_map

    statement = select(BookRelationship).where(
        BookRelationship.status == "approved",
        or_(
            BookRelationship.document_a_id.in_(
                document_ids
            ),
            BookRelationship.document_b_id.in_(
                document_ids
            ),
        ),
    )

    relationships = list(
        db.scalars(statement).all()
    )

    for relationship in relationships:
        relationship_map[
            relationship.document_a_id
        ].append(relationship)

        relationship_map[
            relationship.document_b_id
        ].append(relationship)

    return relationship_map


@router.get(
    "",
    response_model=BookRankingListResponse,
)
def list_ranked_books(
    purpose: RankingPurpose = Query(
        default="general"
    ),
    domain: str | None = Query(default=None),
    topic: str | None = Query(default=None),
    technology: str | None = Query(default=None),
    audience_level: str | None = Query(default=None),

    active_only: bool = Query(default=True),
    include_deprecated: bool = Query(default=False),
    approved_only: bool = Query(default=True),

    minimum_score: float = Query(
        default=0,
        ge=0,
        le=100,
    ),
    limit: int = Query(
        default=25,
        ge=1,
        le=200,
    ),

    db: Session = Depends(get_db),
):
    statement = (
        select(Document, BookCuration)
        .outerjoin(
            BookCuration,
            BookCuration.document_id
            == Document.document_id,
        )
        .order_by(Document.updated_at.desc())
    )

    if active_only:
        statement = statement.where(
            Document.is_active.is_(True)
        )

    if not include_deprecated:
        statement = statement.where(
            Document.is_deprecated.is_(False)
        )

    rows = db.execute(statement).all()

    candidates: list[
        tuple[Document, BookCuration | None]
    ] = []

    for document, curation in rows:
        if (
            approved_only
            and (
                curation is None
                or curation.evaluation_status
                != "approved"
            )
        ):
            continue

        if not document_matches_filters(
            document,
            domain=domain,
            topic=topic,
            technology=technology,
        ):
            continue

        candidates.append(
            (document, curation)
        )

    relationship_map = _load_relationship_map(
        db,
        [
            document.document_id
            for document, _ in candidates
        ],
    )

    ranked_items: list[BookRankingItem] = []

    for document, curation in candidates:
        item = calculate_book_ranking(
            document=document,
            curation=curation,
            relationships=relationship_map.get(
                document.document_id,
                [],
            ),
            purpose=purpose,
            requested_audience=audience_level,
        )

        if item.ranking_score < minimum_score:
            continue

        ranked_items.append(item)

    ranked_items.sort(
        key=lambda item: (
            item.ranking_score,
            item.publication_year or 0,
        ),
        reverse=True,
    )

    visible_results = ranked_items[:limit]

    return BookRankingListResponse(
        purpose=purpose,
        filters={
            "domain": domain,
            "topic": topic,
            "technology": technology,
            "audience_level": audience_level,
            "active_only": active_only,
            "include_deprecated": (
                include_deprecated
            ),
            "approved_only": approved_only,
            "minimum_score": minimum_score,
        },
        candidate_count=len(candidates),
        result_count=len(visible_results),
        results=visible_results,
    )


@router.get(
    "/document/{document_id}",
    response_model=BookRankingItem,
)
def get_document_ranking(
    document_id: str,
    purpose: RankingPurpose = Query(
        default="general"
    ),
    audience_level: str | None = Query(
        default=None
    ),
    db: Session = Depends(get_db),
):
    document = db.get(
        Document,
        document_id,
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    curation = db.scalar(
        select(BookCuration).where(
            BookCuration.document_id
            == document_id
        )
    )

    relationships = list(
        db.scalars(
            select(BookRelationship).where(
                BookRelationship.status
                == "approved",
                or_(
                    BookRelationship.document_a_id
                    == document_id,
                    BookRelationship.document_b_id
                    == document_id,
                ),
            )
        ).all()
    )

    return calculate_book_ranking(
        document=document,
        curation=curation,
        relationships=relationships,
        purpose=purpose,
        requested_audience=audience_level,
    )

@router.post(
    "/document/{document_id}/sync-qdrant",
    response_model=BookRankingQdrantSyncResponse,
)
def sync_document_ranking(
    document_id: str,
    db: Session = Depends(get_db),
):
    document = db.get(
        Document,
        document_id,
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    curation = db.scalar(
        select(BookCuration).where(
            BookCuration.document_id
            == document_id
        )
    )

    if not curation:
        raise HTTPException(
            status_code=404,
            detail="Book curation record not found.",
        )

    relationships = list(
        db.scalars(
            select(BookRelationship).where(
                BookRelationship.status
                == "approved",
                or_(
                    BookRelationship.document_a_id
                    == document_id,
                    BookRelationship.document_b_id
                    == document_id,
                ),
            )
        ).all()
    )

    try:
        result = sync_book_ranking_to_qdrant(
            document=document,
            curation=curation,
            relationships=relationships,
            collection_name=(
                settings.default_collection
            ),
        )

        return BookRankingQdrantSyncResponse(
            **result
        )

    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to synchronize book ranking: "
                f"{type(error).__name__}: {error}"
            ),
        ) from error