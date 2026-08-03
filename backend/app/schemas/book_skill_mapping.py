from datetime import datetime
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


MappingStatus = Literal[
    "generating",
    "pending",
    "approved",
    "rejected",
    "failed",
]

CoverageLevel = Literal[
    "mention",
    "introductory",
    "working",
    "advanced",
    "comprehensive",
]

MappingSource = Literal[
    "manual",
    "metadata",
    "llm",
    "llm_reviewed",
    "imported",
]

EvidenceType = Literal[
    "chapter",
    "section",
    "page",
    "chunk",
    "metadata",
    "manual",
]


class BookSkillEvidenceCreate(BaseModel):
    evidence_type: EvidenceType

    chapter_title: str | None = Field(
        default=None,
        max_length=500,
    )

    section_title: str | None = Field(
        default=None,
        max_length=500,
    )

    page_start: int | None = Field(
        default=None,
        ge=1,
    )

    page_end: int | None = Field(
        default=None,
        ge=1,
    )

    chunk_id: str | None = Field(
        default=None,
        max_length=200,
    )

    excerpt: str | None = Field(
        default=None,
        max_length=4000,
    )

    source_locator: dict[str, Any] | None = None

    confidence: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    display_order: int = 0


class BookSkillEvidenceResponse(
    BookSkillEvidenceCreate
):
    model_config = ConfigDict(
        from_attributes=True
    )

    evidence_id: str
    mapping_id: str
    created_at: datetime


class BookSkillMappingCreate(BaseModel):
    document_id: str
    skill_id: str

    mapping_status: MappingStatus = "pending"

    coverage_level: CoverageLevel | None = None
    is_primary_skill: bool = False

    relevance_score: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    coverage_score: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    depth_score: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    practicality_score: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    confidence: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    recommended_entry_level_id: str | None = None
    recommended_exit_level_id: str | None = None

    coverage_summary: str | None = Field(
        default=None,
        max_length=6000,
    )

    learning_outcomes: list[str] = Field(
        default_factory=list
    )

    covered_topics: list[str] = Field(
        default_factory=list
    )

    limitations: list[str] = Field(
        default_factory=list
    )

    mapping_source: MappingSource = "manual"

    mapping_model: str | None = Field(
        default=None,
        max_length=200,
    )

    evidence: list[
        BookSkillEvidenceCreate
    ] = Field(default_factory=list)


class BookSkillMappingUpdate(BaseModel):
    mapping_status: MappingStatus | None = None

    coverage_level: CoverageLevel | None = None
    is_primary_skill: bool | None = None

    relevance_score: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    coverage_score: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    depth_score: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    practicality_score: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    confidence: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    recommended_entry_level_id: str | None = None
    recommended_exit_level_id: str | None = None

    coverage_summary: str | None = Field(
        default=None,
        max_length=6000,
    )

    learning_outcomes: list[str] | None = None
    covered_topics: list[str] | None = None
    limitations: list[str] | None = None

    mapping_source: MappingSource | None = None

    mapping_model: str | None = Field(
        default=None,
        max_length=200,
    )

    review_notes: str | None = Field(
        default=None,
        max_length=4000,
    )


class BookSkillMappingResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    mapping_id: str

    document_id: str
    skill_id: str

    mapping_status: str
    coverage_level: str | None

    is_primary_skill: bool

    relevance_score: float | None
    coverage_score: float | None
    depth_score: float | None
    practicality_score: float | None

    confidence: float | None

    recommended_entry_level_id: str | None
    recommended_exit_level_id: str | None

    coverage_summary: str | None

    learning_outcomes: list[str] | None
    covered_topics: list[str] | None
    limitations: list[str] | None

    mapping_source: str
    mapping_model: str | None
    mapping_version: int

    candidate_payload: dict[str, Any] | None
    candidate_error: str | None

    candidate_generated_at: datetime | None

    review_notes: str | None
    reviewed_at: datetime | None

    created_at: datetime
    updated_at: datetime


class BookSkillMappingDetailResponse(BaseModel):
    mapping: BookSkillMappingResponse
    evidence: list[BookSkillEvidenceResponse]