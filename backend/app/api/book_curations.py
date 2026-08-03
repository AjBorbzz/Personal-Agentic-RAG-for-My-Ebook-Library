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

from datetime import datetime, timezone

from pydantic import ValidationError

from app.schemas.book_curation_review import (
    BookCurationReviewRequest,
    BookCurationReviewResponse,
    BookCurationReviewStateResponse,
)
from app.schemas.book_evaluation import BookEvaluationCandidate
from app.services.book_curator_evaluation import (
    apply_evaluation_candidate,
    normalize_candidate,
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


@router.get("",response_model=list[BookCurationResponse])
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

    curation = db.scalar(select(BookCuration)
                 .where(BookCuration.document_id == document_id))

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


@router.get(
    "/{document_id}/review",
    response_model=BookCurationReviewStateResponse,
)
def get_book_curation_review(
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

    candidate = None

    if curation.evaluation_candidate:
        try:
            candidate = BookEvaluationCandidate.model_validate(
                curation.evaluation_candidate
            )
        except ValidationError as error:
            raise HTTPException(
                status_code=500,
                detail=(
                    "The stored evaluation candidate is invalid: "
                    f"{error}"
                ),
            ) from error

    return BookCurationReviewStateResponse(
        document_id=curation.document_id,
        evaluation_status=curation.evaluation_status,
        evaluation_version=curation.evaluation_version,
        candidate=candidate,
        evaluation_source=curation.evaluation_source,
        evaluation_model=curation.evaluation_model,
        evaluation_error=curation.evaluation_error,
        confidence=curation.confidence,
        evaluated_at=curation.evaluated_at,
        reviewed_at=curation.reviewed_at,
        review_notes=curation.review_notes,
        curation=curation,
    )

@router.patch(
    "/{document_id}/review",
    response_model=BookCurationReviewResponse,
)
def review_book_curation(
    document_id: str,
    request: BookCurationReviewRequest,
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

    if not curation.evaluation_candidate:
        raise HTTPException(
            status_code=409,
            detail=(
                "This book does not have an evaluation candidate. "
                "Generate an evaluation first."
            ),
        )

    if curation.evaluation_status == "generating":
        raise HTTPException(
            status_code=409,
            detail=(
                "The evaluation is still being generated and "
                "cannot be reviewed yet."
            ),
        )

    try:
        if request.edited_candidate is not None:
            candidate = normalize_candidate(
                request.edited_candidate
            )
        else:
            candidate = BookEvaluationCandidate.model_validate(
                curation.evaluation_candidate
            )
            candidate = normalize_candidate(candidate)

        reviewed_at = datetime.now(timezone.utc)

        if request.action == "reject":
            curation.evaluation_status = "rejected"
            curation.review_notes = request.review_notes
            curation.reviewed_at = reviewed_at
            curation.evaluation_error = None

            # Preserve the candidate for audit.
            curation.evaluation_candidate = (
                candidate.model_dump()
            )

            db.commit()
            db.refresh(curation)

            return BookCurationReviewResponse(
                document_id=curation.document_id,
                action="reject",
                evaluation_status="rejected",
                applied=False,
                updated_fields=[],
                candidate=candidate,
                review_notes=curation.review_notes,
                reviewed_at=reviewed_at,
                curation=curation,
            )

        updated_fields = apply_evaluation_candidate(
            curation=curation,
            candidate=candidate,
        )

        curation.evaluation_status = "approved"
        curation.review_notes = request.review_notes
        curation.reviewed_at = reviewed_at
        curation.evaluation_error = None

        if curation.evaluation_source == "llm":
            curation.evaluation_source = "llm_reviewed"
        elif not curation.evaluation_source:
            curation.evaluation_source = "manual_reviewed"

        db.commit()
        db.refresh(curation)

        return BookCurationReviewResponse(
            document_id=curation.document_id,
            action="approve",
            evaluation_status="approved",
            applied=True,
            updated_fields=updated_fields,
            candidate=candidate,
            review_notes=curation.review_notes,
            reviewed_at=reviewed_at,
            curation=curation,
        )

    except ValidationError as error:
        db.rollback()

        raise HTTPException(
            status_code=422,
            detail=(
                "The evaluation candidate is invalid: "
                f"{error}"
            ),
        ) from error

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Book curation review failed: "
                f"{type(error).__name__}: {error}"
            ),
        ) from error