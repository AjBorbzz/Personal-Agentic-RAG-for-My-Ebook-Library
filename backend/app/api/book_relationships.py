from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.book_relationship import BookRelationship
from app.models.document import Document
from app.schemas.book_relationship import (
    BookRelationshipResponse,
    ReviewBookRelationshipRequest,
    ReviewBookRelationshipResponse,
    ScanBookRelationshipsRequest,
    ScanBookRelationshipsResponse,
)
from app.services.book_relationship_detection import (
    scan_document_relationships,
)

router = APIRouter(
    prefix="/book-relationships",
    tags=["book-relationships"],
)


@router.post(
    "/scan/{document_id}",
    response_model=ScanBookRelationshipsResponse,
)
def scan_book_relationship_candidates(
    document_id: str,
    request: ScanBookRelationshipsRequest,
    db: Session = Depends(get_db),
):
    target_document = db.get(
        Document,
        document_id,
    )

    if not target_document:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    statement = (
        select(Document)
        .where(Document.document_id != document_id)
        .order_by(Document.updated_at.desc())
    )

    if not request.include_inactive:
        statement = statement.where(
            Document.is_active.is_(True)
        )

    if not request.include_deprecated:
        statement = statement.where(
            Document.is_deprecated.is_(False)
        )

    statement = statement.limit(
        request.max_comparisons
    )

    comparison_documents = list(
        db.scalars(statement).all()
    )

    try:
        candidates, warnings = (
            scan_document_relationships(
                db=db,
                target_document=target_document,
                comparison_documents=comparison_documents,
                content_sample_characters=(
                    request.content_sample_characters
                ),
                shingle_size=request.shingle_size,
                minimum_confidence=(
                    request.minimum_confidence
                ),
            )
        )

        return ScanBookRelationshipsResponse(
            document_id=document_id,
            compared_documents=len(
                comparison_documents
            ),
            candidate_count=len(candidates),
            candidates=candidates,
            warnings=warnings,
        )

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Relationship scan failed: "
                f"{type(error).__name__}: {error}"
            ),
        ) from error


@router.get(
    "",
    response_model=list[BookRelationshipResponse],
)
def list_book_relationships(
    db: Session = Depends(get_db),
    document_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    relationship_type: str | None = Query(default=None),
    minimum_confidence: float | None = Query(
        default=None,
        ge=0,
        le=1,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
):
    statement = select(BookRelationship).order_by(
        BookRelationship.confidence.desc(),
        BookRelationship.updated_at.desc(),
    )

    if document_id:
        statement = statement.where(
            or_(
                BookRelationship.document_a_id
                == document_id,
                BookRelationship.document_b_id
                == document_id,
            )
        )

    if status:
        statement = statement.where(
            BookRelationship.status == status
        )

    if relationship_type:
        statement = statement.where(
            BookRelationship.relationship_type
            == relationship_type
        )

    if minimum_confidence is not None:
        statement = statement.where(
            BookRelationship.confidence
            >= minimum_confidence
        )

    statement = statement.limit(limit)

    return list(db.scalars(statement).all())


@router.get(
    "/{relationship_id}",
    response_model=BookRelationshipResponse,
)
def get_book_relationship(
    relationship_id: str,
    db: Session = Depends(get_db),
):
    relationship = db.get(
        BookRelationship,
        relationship_id,
    )

    if not relationship:
        raise HTTPException(
            status_code=404,
            detail="Book relationship not found.",
        )

    return relationship


@router.patch(
    "/{relationship_id}/review",
    response_model=ReviewBookRelationshipResponse,
)
def review_book_relationship(
    relationship_id: str,
    request: ReviewBookRelationshipRequest,
    db: Session = Depends(get_db),
):
    relationship = db.get(
        BookRelationship,
        relationship_id,
    )

    if not relationship:
        raise HTTPException(
            status_code=404,
            detail="Book relationship not found.",
        )

    valid_document_ids = {
        relationship.document_a_id,
        relationship.document_b_id,
    }

    for selected_id in (
        request.recommended_primary_document_id,
        request.recommended_superseded_document_id,
    ):
        if (
            selected_id is not None
            and selected_id not in valid_document_ids
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    "Recommended document IDs must belong "
                    "to the relationship pair."
                ),
            )

    if (
        request.recommended_primary_document_id
        and request.recommended_superseded_document_id
        and request.recommended_primary_document_id
        == request.recommended_superseded_document_id
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "The primary and superseded document "
                "cannot be the same document."
            ),
        )

    if request.relationship_type is not None:
        relationship.relationship_type = (
            request.relationship_type
        )

    if (
        request.recommended_primary_document_id
        is not None
    ):
        relationship.recommended_primary_document_id = (
            request.recommended_primary_document_id
        )

    if (
        request.recommended_superseded_document_id
        is not None
    ):
        relationship.recommended_superseded_document_id = (
            request.recommended_superseded_document_id
        )

    if request.recommended_action is not None:
        relationship.recommended_action = (
            request.recommended_action
        )

    relationship.status = (
        "approved"
        if request.action == "approve"
        else "rejected"
    )

    relationship.review_notes = request.review_notes
    relationship.reviewed_at = datetime.now(
        timezone.utc
    )

    db.commit()
    db.refresh(relationship)

    return ReviewBookRelationshipResponse(
        relationship_id=relationship.relationship_id,
        status=relationship.status,
        relationship=relationship,
    )