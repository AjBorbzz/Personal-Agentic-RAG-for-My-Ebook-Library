from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.book_skill_mapping import (
    BookSkillMappingResponse,
)


CoverageLevel = Literal[
    "mention",
    "introductory",
    "working",
    "advanced",
    "comprehensive",
]

ProficiencyCode = Literal[
    "awareness",
    "foundational",
    "working",
    "advanced",
    "expert",
]


class BookSkillEvidenceCandidate(BaseModel):
    evidence_type: Literal[
        "chapter",
        "section",
        "page",
        "chunk",
        "metadata",
        "manual",
    ] = "section"

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

    excerpt: str | None = Field(
        default=None,
        max_length=1000,
    )

    confidence: float = Field(
        default=0.7,
        ge=0,
        le=1,
    )


class BookSkillCandidate(BaseModel):
    skill_slug: str = Field(
        min_length=1,
        max_length=160,
    )

    coverage_level: CoverageLevel

    is_primary_skill: bool = False

    relevance_score: float = Field(
        ge=0,
        le=100,
    )

    coverage_score: float = Field(
        ge=0,
        le=100,
    )

    depth_score: float = Field(
        ge=0,
        le=100,
    )

    practicality_score: float = Field(
        ge=0,
        le=100,
    )

    confidence: float = Field(
        ge=0,
        le=1,
    )

    recommended_entry_level_code: ProficiencyCode

    recommended_exit_level_code: ProficiencyCode

    coverage_summary: str = Field(
        min_length=1,
        max_length=4000,
    )

    learning_outcomes: list[str] = Field(
        default_factory=list,
        max_length=12,
    )

    covered_topics: list[str] = Field(
        default_factory=list,
        max_length=20,
    )

    limitations: list[str] = Field(
        default_factory=list,
        max_length=12,
    )

    evidence: list[
        BookSkillEvidenceCandidate
    ] = Field(
        default_factory=list,
        max_length=8,
    )


class BookSkillCandidateBatch(BaseModel):
    analysis_summary: str = Field(
        min_length=1,
        max_length=4000,
    )

    mappings: list[
        BookSkillCandidate
    ] = Field(
        default_factory=list,
        max_length=20,
    )


class GenerateBookSkillCandidatesRequest(BaseModel):
    max_source_characters: int = Field(
        default=16000,
        ge=6000,
        le=40000,
    )

    maximum_candidate_skills: int = Field(
        default=30,
        ge=5,
        le=100,
    )

    maximum_mappings: int = Field(
        default=12,
        ge=1,
        le=20,
    )

    minimum_shortlist_score: float = Field(
        default=1.0,
        ge=0,
        le=100,
    )

    regenerate_approved: bool = False


class ShortlistedSkillResponse(BaseModel):
    skill_id: str
    slug: str
    name: str

    domain_name: str
    category_name: str | None

    skill_type: str
    difficulty_level: str

    lexical_score: float
    matched_terms: list[str]


class GeneratedBookSkillMappingResponse(BaseModel):
    skill_id: str
    skill_slug: str
    skill_name: str

    created: bool
    skipped: bool
    skip_reason: str | None

    mapping: BookSkillMappingResponse | None


class GenerateBookSkillCandidatesResponse(BaseModel):
    document_id: str

    model: str
    source_characters_used: int

    shortlisted_skill_count: int
    generated_candidate_count: int

    mappings_created: int
    mappings_updated: int
    mappings_skipped: int

    analysis_summary: str

    shortlist: list[
        ShortlistedSkillResponse
    ]

    generated_mappings: list[
        GeneratedBookSkillMappingResponse
    ]

    warnings: list[str] = Field(
        default_factory=list
    )


class BookSkillCandidateListItem(BaseModel):
    mapping: BookSkillMappingResponse

    skill_slug: str
    skill_name: str
    domain_name: str
    category_name: str | None


class BookSkillCandidateListResponse(BaseModel):
    document_id: str
    candidate_count: int

    candidates: list[
        BookSkillCandidateListItem
    ]