from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.book_curation import BookCurationResponse
from app.schemas.book_evaluation import BookEvaluationCandidate


class BookCurationReviewStateResponse(BaseModel):
    document_id: str
    evaluation_status: str
    evaluation_version: int

    candidate: BookEvaluationCandidate | None

    evaluation_source: str | None
    evaluation_model: str | None
    evaluation_error: str | None
    confidence: float | None

    evaluated_at: datetime | None
    reviewed_at: datetime | None
    review_notes: str | None

    curation: BookCurationResponse


class BookCurationReviewRequest(BaseModel):
    action: Literal["approve", "reject"]

    edited_candidate: BookEvaluationCandidate | None = None

    review_notes: str | None = Field(
        default=None,
        max_length=4000,
    )


class BookCurationReviewResponse(BaseModel):
    document_id: str
    action: Literal["approve", "reject"]
    evaluation_status: str

    applied: bool
    updated_fields: list[str]

    candidate: BookEvaluationCandidate | None

    review_notes: str | None
    reviewed_at: datetime

    curation: BookCurationResponse