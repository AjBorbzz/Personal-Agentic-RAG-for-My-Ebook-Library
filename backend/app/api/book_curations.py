from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.book_curation import BookCuration
from app.models.document import Document
from app.schemas.book_curation import (
    BookCurationResponse,
    BookCurationUpdate,
)

router = APIRouter(
    prefix="/book-curations",
    tags=["book-curations"],
)


@router.post(
    "/{document_id}",
    response_model=BookCurationResponse,
    status_code=201,
)
def initialize_book_curation(
    document_id: str,
    db: Session = Depends(get_db),
):
    document = db.get(Document, document_id)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    existing = db.scalar(
        select(BookCuration).where(
            BookCuration.document_id == document_id
        )
    )

    if existing:
        return existing

    curation = BookCuration(
        document_id=document_id,
        evaluation_status="not_evaluated",
        metadata_snapshot={
            "title": document.title,
            "author": document.author,
            "publication_year": document.publication_year,
            "domains": document.domains,
            "topics": document.topics,
            "technologies": document.technologies,
            "difficulty_level": document.difficulty_level,
            "metadata_review_status": (
                document.metadata_review_status
            ),
        },
    )

    db.add(curation)
    db.commit()
    db.refresh(curation)

    return curation


@router.get(
    "",
    response_model=list[BookCurationResponse],
)
def list_book_curations(
    db: Session = Depends(get_db),
    evaluation_status: str | None = Query(default=None),
    library_priority: str | None = Query(default=None),
    recommended_role: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
):
    statement = select(BookCuration).order_by(
        BookCuration.updated_at.desc()
    )

    if evaluation_status:
        statement = statement.where(
            BookCuration.evaluation_status
            == evaluation_status
        )

    if library_priority:
        statement = statement.where(
            BookCuration.library_priority
            == library_priority
        )

    if recommended_role:
        statement = statement.where(
            BookCuration.recommended_role
            == recommended_role
        )

    statement = statement.limit(limit)

    return list(db.scalars(statement).all())


@router.get(
    "/{document_id}",
    response_model=BookCurationResponse,
)
def get_book_curation(
    document_id: str,
    db: Session = Depends(get_db),
):
    curation = db.scalar(
        select(BookCuration).where(
            BookCuration.document_id == document_id
        )
    )

    if not curation:
        raise HTTPException(
            status_code=404,
            detail="Book curation record not found.",
        )

    return curation


@router.patch(
    "/{document_id}",
    response_model=BookCurationResponse,
)
def update_book_curation(
    document_id: str,
    request: BookCurationUpdate,
    db: Session = Depends(get_db),
):
    curation = db.scalar(
        select(BookCuration).where(
            BookCuration.document_id == document_id
        )
    )

    if not curation:
        raise HTTPException(
            status_code=404,
            detail="Book curation record not found.",
        )

    updates = request.model_dump(
        exclude_unset=True
    )

    for field_name, value in updates.items():
        setattr(curation, field_name, value)

    db.commit()
    db.refresh(curation)

    return curation