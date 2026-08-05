from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.book_skill_candidate import (
    BookSkillCandidate,
)
from app.schemas.book_skill_mapping import (
    BookSkillEvidenceResponse,
    BookSkillMappingResponse,
)


ReviewAction = Literal[
    "approve",
    "reject",
]


class BookSkillReviewRequest(BaseModel):
    action: ReviewAction

    edited_candidate: (
        BookSkillCandidate | None
    ) = None

    review_notes: str | None = Field(
        default=None,
        max_length=4000,
    )


class ProficiencyLevelSummary(BaseModel):
    level_id: str
    code: str
    name: str
    level_order: int


class BookSkillReviewResponse(BaseModel):
    mapping: BookSkillMappingResponse

    document_id: str
    document_title: str

    skill_id: str
    skill_slug: str
    skill_name: str

    domain_name: str
    category_name: str | None

    candidate: dict[str, Any] | None

    trusted_evidence: list[
        BookSkillEvidenceResponse
    ]

    entry_level: (
        ProficiencyLevelSummary | None
    )

    exit_level: (
        ProficiencyLevelSummary | None
    )

    reviewed_action: str | None = None


class BookSkillReviewQueueResponse(BaseModel):
    document_id: str
    result_count: int

    reviews: list[
        BookSkillReviewResponse
    ]


class BookSkillReviewResult(BaseModel):
    mapping_id: str
    action: ReviewAction

    final_status: str
    evidence_created: int

    reviewed_at: datetime

    review: BookSkillReviewResponse