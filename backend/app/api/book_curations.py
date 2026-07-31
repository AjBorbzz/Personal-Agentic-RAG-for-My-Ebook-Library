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

from datetime import datetime, timezone

from app.core.config import settings
from app.schemas.book_evaluation import (
    GenerateBookEvaluationRequest,
    GenerateBookEvaluationResponse,
)
from app.services.book_curator_evaluation import (
    configured_generation_model,
    generate_book_evaluation_candidate,
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


@router.post("/{document_id}/evaluate",response_model=GenerateBookEvaluationResponse)
async def generate_book_evaluation(document_id: str,request: GenerateBookEvaluationRequest,db: Session = Depends(get_db)):
    document = db.get(Document, document_id)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    curation = db.scalar(
        select(BookCuration).where(
            BookCuration.document_id == document_id
        )
    )

    if not curation:
        curation = BookCuration(
            document_id=document_id,
            evaluation_status="not_evaluated",
        )

        db.add(curation)
        db.commit()
        db.refresh(curation)

    if curation.evaluation_status == "generating":
        raise HTTPException(
            status_code=409,
            detail=(
                "A book evaluation is already being generated "
                "for this document."
            ),
        )

    curation.evaluation_status = "generating"
    curation.evaluation_error = None
    curation.review_notes = None
    curation.reviewed_at = None

    db.commit()
    db.refresh(curation)

    warnings: list[str] = []

    if document.metadata_review_status != "approved":
        warnings.append(
            "The document metadata has not been approved. "
            "The evaluation may rely on incomplete metadata."
        )

    try:
        (
            candidate,
            metadata_snapshot,
            source_characters_used,
            source_was_truncated,
        ) = await generate_book_evaluation_candidate(
            document=document,
            maximum_source_characters=(
                request.max_source_characters
            ),
        )

        if source_was_truncated:
            warnings.append(
                "The full book exceeded the evaluation limit. "
                "The beginning, middle, and end were sampled."
            )

        if curation.evaluation_candidate is not None:
            curation.evaluation_version += 1

        curation.evaluation_status = "pending"
        curation.evaluation_candidate = (
            candidate.model_dump()
        )
        curation.metadata_snapshot = metadata_snapshot

        curation.evaluation_source = "llm"
        curation.evaluation_model = (
            configured_generation_model()
        )
        curation.confidence = candidate.confidence

        curation.evaluated_at = datetime.now(
            timezone.utc
        )
        curation.evaluation_error = None

        db.commit()
        db.refresh(curation)

        return GenerateBookEvaluationResponse(
            document_id=document.document_id,
            evaluation_status=(
                curation.evaluation_status
            ),
            evaluation_version=(
                curation.evaluation_version
            ),
            source_characters_used=(
                source_characters_used
            ),
            source_was_truncated=(
                source_was_truncated
            ),
            candidate=candidate,
            warnings=warnings,
            curation=curation,
        )

    except FileNotFoundError as error:
        db.rollback()

        failed_curation = db.scalar(
            select(BookCuration).where(
                BookCuration.document_id
                == document_id
            )
        )

        if failed_curation:
            failed_curation.evaluation_status = "failed"
            failed_curation.evaluation_error = str(error)
            db.commit()

        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except (ValueError, TypeError) as error:
        db.rollback()

        failed_curation = db.scalar(
            select(BookCuration).where(
                BookCuration.document_id
                == document_id
            )
        )

        if failed_curation:
            failed_curation.evaluation_status = "failed"
            failed_curation.evaluation_error = str(error)
            db.commit()

        raise HTTPException(
            status_code=502,
            detail=(
                "The book evaluation model returned "
                f"invalid output: {error}"
            ),
        ) from error

    except RuntimeError as error:
        db.rollback()

        failed_curation = db.scalar(
            select(BookCuration).where(
                BookCuration.document_id
                == document_id
            )
        )

        if failed_curation:
            failed_curation.evaluation_status = "failed"
            failed_curation.evaluation_error = str(error)
            db.commit()

        raise HTTPException(
            status_code=504,
            detail=str(error),
        ) from error

    except Exception as error:
        db.rollback()

        failed_curation = db.scalar(
            select(BookCuration).where(
                BookCuration.document_id
                == document_id
            )
        )

        if failed_curation:
            failed_curation.evaluation_status = "failed"
            failed_curation.evaluation_error = (
                f"{type(error).__name__}: {error}"
            )
            db.commit()

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to generate book evaluation: "
                f"{type(error).__name__}: {error}"
            ),
        ) from error