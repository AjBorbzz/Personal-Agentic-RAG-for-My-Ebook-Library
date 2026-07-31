from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.book_curation import BookCurationResponse


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


class BookEvaluationCandidate(BaseModel):
    overall_score: float = Field(
        default=0,
        ge=0,
        le=100,
    )

    technical_depth_score: float = Field(
        ge=0,
        le=100,
    )

    practicality_score: float = Field(
        ge=0,
        le=100,
    )

    freshness_score: float = Field(
        ge=0,
        le=100,
    )

    authority_score: float = Field(
        ge=0,
        le=100,
    )

    clarity_score: float = Field(
        ge=0,
        le=100,
    )

    outdated_risk_score: float = Field(
        ge=0,
        le=100,
    )

    audience_level: AudienceLevel
    recommended_role: RecommendedRole
    library_priority: LibraryPriority

    curator_summary: str
    unique_value: str | None = None

    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    best_for: list[str] = Field(default_factory=list)
    not_recommended_for: list[str] = Field(
        default_factory=list
    )
    outdated_topics: list[str] = Field(
        default_factory=list
    )

    confidence: float = Field(
        default=0.5,
        ge=0,
        le=1,
    )


class GenerateBookEvaluationRequest(BaseModel):
    max_source_characters: int = Field(
        default=12000,
        ge=4000,
        le=30000,
    )


class GenerateBookEvaluationResponse(BaseModel):
    document_id: str
    evaluation_status: str
    evaluation_version: int

    source_characters_used: int
    source_was_truncated: bool

    candidate: BookEvaluationCandidate
    warnings: list[str] = Field(default_factory=list)

    curation: BookCurationResponse