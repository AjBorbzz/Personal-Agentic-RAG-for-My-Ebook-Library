from datetime import datetime

from pydantic import BaseModel, Field


class BookSkillDomainOption(BaseModel):
    slug: str
    name: str


class BookSkillDashboardStats(BaseModel):
    registered_documents: int

    books_with_any_mappings: int
    books_with_approved_mappings: int

    total_mappings: int
    pending_mappings: int
    approved_mappings: int
    rejected_mappings: int
    failed_mappings: int

    primary_mappings: int

    active_skills: int
    skills_with_approved_books: int
    unmapped_active_skills: int


class BookSkillStatusCount(BaseModel):
    status: str
    count: int


class BookCoverageSummary(BaseModel):
    document_id: str
    document_title: str
    author: str | None

    approved_mapping_count: int
    primary_skill_count: int

    average_quality_score: float
    average_relevance_score: float
    average_coverage_score: float
    average_depth_score: float
    average_practicality_score: float

    primary_skills: list[str] = Field(
        default_factory=list
    )


class SkillCoverageSummary(BaseModel):
    skill_id: str
    skill_slug: str
    skill_name: str

    domain_name: str
    category_name: str | None

    supporting_book_count: int
    primary_book_count: int

    average_quality_score: float
    average_relevance_score: float
    average_coverage_score: float
    average_depth_score: float
    average_practicality_score: float

    best_document_id: str | None
    best_document_title: str | None
    best_document_score: float | None


class PendingBookSkillReview(BaseModel):
    mapping_id: str

    document_id: str
    document_title: str

    skill_id: str
    skill_name: str

    domain_name: str
    category_name: str | None

    mapping_version: int
    mapping_model: str | None

    candidate_generated_at: datetime | None
    updated_at: datetime


class UnmappedSkillSummary(BaseModel):
    skill_id: str
    skill_slug: str
    skill_name: str

    domain_name: str
    category_name: str | None

    skill_type: str
    difficulty_level: str


class BookSkillDashboardResponse(BaseModel):
    domain_filter: str | None

    domains: list[
        BookSkillDomainOption
    ]

    stats: BookSkillDashboardStats

    status_counts: list[
        BookSkillStatusCount
    ]

    top_books: list[
        BookCoverageSummary
    ]

    top_skills: list[
        SkillCoverageSummary
    ]

    pending_reviews: list[
        PendingBookSkillReview
    ]

    unmapped_skills: list[
        UnmappedSkillSummary
    ]