from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.book_ranking import (
    BookRankingItem,
    RankingPurpose,
)
from app.schemas.book_relationship import (
    BookRelationshipResponse,
)


class BookCuratorDashboardStats(BaseModel):
    total_documents: int
    active_documents: int
    deprecated_documents: int

    approved_evaluations: int
    pending_evaluations: int
    generating_evaluations: int
    failed_evaluations: int
    rejected_evaluations: int
    not_evaluated: int

    essential_books: int
    top_pick_books: int

    pending_relationships: int
    exact_duplicates: int
    different_editions: int
    high_content_overlaps: int


class BookCurationQueueItem(BaseModel):
    document_id: str
    curation_id: str | None

    filename: str | None
    title: str | None
    author: str | None
    publication_year: int | None

    evaluation_status: str
    overall_score: float | None

    audience_level: str | None
    recommended_role: str | None
    library_priority: str | None

    evaluation_model: str | None
    evaluation_error: str | None

    evaluated_at: datetime | None
    reviewed_at: datetime | None
    updated_at: datetime | None


class BookCuratorDashboardResponse(BaseModel):
    generated_at: datetime

    purpose: RankingPurpose
    filters: dict[str, str | None]

    stats: BookCuratorDashboardStats

    top_books: list[BookRankingItem]

    review_queue: list[BookCurationQueueItem]

    pending_relationships: list[
        BookRelationshipResponse
    ]

    warnings: list[str] = Field(
        default_factory=list
    )