from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.book_skill_mapping import (
    BookSkillMapping,
)
from app.models.document import Document
from app.schemas.book_skill_review import (
    BookSkillReviewQueueResponse,
    BookSkillReviewRequest,
    BookSkillReviewResponse,
    BookSkillReviewResult,
)
from app.services.book_skill_review import (
    build_book_skill_review_response,
    review_book_skill_mapping,
)


router = APIRouter(
    prefix="/book-skill-mappings",
    tags=["book-skill-mapping-reviews"],
)


@router.get("/documents/{document_id}/review-queue", response_model=BookSkillReviewQueueResponse)
def get_document_review_queue(document_id: str, 
                              mapping_status: str | None = Query(default="pending"),
                              db: Session = Depends(get_db),
                                ):
    document = db.get(
        Document,
        document_id,
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    statement = (
        select(BookSkillMapping)
        .where(
            BookSkillMapping.document_id
            == document_id
        )
        .order_by(
            BookSkillMapping.is_primary_skill
            .desc(),
            BookSkillMapping.updated_at.desc(),
        )
    )

    if mapping_status:
        statement = statement.where(
            BookSkillMapping.mapping_status
            == mapping_status
        )

    mappings = list(
        db.scalars(statement).all()
    )

    try:
        reviews = [
            build_book_skill_review_response(
                db=db,
                mapping=mapping,
            )
            for mapping in mappings
        ]

        return BookSkillReviewQueueResponse(
            document_id=document_id,
            result_count=len(reviews),
            reviews=reviews,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@router.get(
    "/{mapping_id}/review",
    response_model=BookSkillReviewResponse,
)
def get_mapping_review(
    mapping_id: str,
    db: Session = Depends(get_db),
):
    mapping = db.get(
        BookSkillMapping,
        mapping_id,
    )

    if mapping is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Book-to-skill mapping "
                "was not found."
            ),
        )

    try:
        return build_book_skill_review_response(
            db=db,
            mapping=mapping,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@router.patch(
    "/{mapping_id}/review",
    response_model=BookSkillReviewResult,
)
def submit_mapping_review(
    mapping_id: str,
    request: BookSkillReviewRequest,
    db: Session = Depends(get_db),
):
    try:
        return review_book_skill_mapping(
            db=db,
            mapping_id=mapping_id,
            action=request.action,
            edited_candidate=(
                request.edited_candidate
            ),
            review_notes=(
                request.review_notes
            ),
        )

    except ValueError as error:
        db.rollback()

        message = str(error)

        status_code = (
            404
            if "not found" in message.lower()
            else 422
        )

        raise HTTPException(
            status_code=status_code,
            detail=message,
        ) from error

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Book-to-skill review failed: "
                f"{type(error).__name__}: "
                f"{error}"
            ),
        ) from error