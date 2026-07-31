from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


EvaluationStatus = Literal[
    "not_evaluated",
    "generating",
    "pending",
    "approved",
    "rejected",
    "failed",
]

AudienceLevel = Literal[
    "beginner",
    "intermediate",
    "advanced",
    "mixed",
]

RecommendedRole = Literal[
    "foundational",
    "practical_guide",
    "reference",
    "advanced_specialist",
    "supplementary",
    "historical",
    "redundant",
    "avoid",
]

LibraryPriority = Literal[
    "essential",
    "high",
    "medium",
    "low",
    "archive",
]


class BookCurationUpdate(BaseModel):
    evaluation_status: EvaluationStatus | None = None

    overall_score: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    technical_depth_score: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    practicality_score: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    freshness_score: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    authority_score: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    clarity_score: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    outdated_risk_score: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    audience_level: AudienceLevel | None = None
    recommended_role: RecommendedRole | None = None
    library_priority: LibraryPriority | None = None

    curator_summary: str | None = None
    unique_value: str | None = None

    strengths: list[str] | None = None
    weaknesses: list[str] | None = None
    best_for: list[str] | None = None
    not_recommended_for: list[str] | None = None
    outdated_topics: list[str] | None = None

    evaluation_source: str | None = None
    evaluation_model: str | None = None

    confidence: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    review_notes: str | None = None


class BookCurationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    curation_id: str
    document_id: str

    evaluation_status: str

    overall_score: float | None
    technical_depth_score: float | None
    practicality_score: float | None
    freshness_score: float | None
    authority_score: float | None
    clarity_score: float | None
    outdated_risk_score: float | None

    audience_level: str | None
    recommended_role: str | None
    library_priority: str | None

    curator_summary: str | None
    unique_value: str | None

    strengths: list[str] | None
    weaknesses: list[str] | None
    best_for: list[str] | None
    not_recommended_for: list[str] | None
    outdated_topics: list[str] | None

    evaluation_source: str | None
    evaluation_model: str | None
    evaluation_version: int
    confidence: float | None

    metadata_snapshot: dict | None
    evaluation_candidate: dict | None
    review_notes: str | None

    evaluated_at: datetime | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    evaluation_error: str | None