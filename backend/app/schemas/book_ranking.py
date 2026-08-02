from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


RankingPurpose = Literal[
    "general",
    "learning",
    "project",
    "reference",
    "current_technology",
    "foundational",
]


class BookRankingBreakdown(BaseModel):
    purpose_base_score: float

    priority_modifier: float
    role_modifier: float
    audience_modifier: float
    lifecycle_modifier: float
    relationship_modifier: float

    final_score: float


class BookRankingItem(BaseModel):
    document_id: str
    curation_id: str | None

    filename: str | None
    title: str | None
    author: str | None
    publication_year: int | None

    primary_domain: str | None
    domains: list[str]
    topics: list[str]
    technologies: list[str]

    is_active: bool
    is_deprecated: bool

    evaluation_status: str
    overall_score: float | None

    audience_level: str | None
    recommended_role: str | None
    library_priority: str | None

    ranking_purpose: RankingPurpose
    ranking_score: float
    recommendation_tier: str

    breakdown: BookRankingBreakdown
    reasons: list[str]
    warnings: list[str]


class BookRankingListResponse(BaseModel):
    purpose: RankingPurpose
    filters: dict[str, Any]

    candidate_count: int
    result_count: int

    results: list[BookRankingItem]


class BookRankingQdrantSyncResponse(BaseModel):
    document_id: str
    collection_name: str

    matched_points: int
    payload_keys_set: list[str]
    payload_keys_deleted: list[str]

    ranking_score: float
    ranking_purpose: RankingPurpose
    synced_at: datetime

    warnings: list[str] = Field(default_factory=list)