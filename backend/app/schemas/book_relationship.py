from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


RelationshipType = Literal[
    "exact_duplicate",
    "same_edition",
    "different_edition",
    "high_content_overlap",
    "related_topic",
]

RelationshipStatus = Literal[
    "pending",
    "approved",
    "rejected",
]


class ScanBookRelationshipsRequest(BaseModel):
    max_comparisons: int = Field(
        default=100,
        ge=1,
        le=1000,
    )

    include_inactive: bool = False
    include_deprecated: bool = True

    content_sample_characters: int = Field(
        default=30000,
        ge=6000,
        le=60000,
    )

    shingle_size: int = Field(
        default=5,
        ge=3,
        le=8,
    )

    minimum_confidence: float = Field(
        default=0.55,
        ge=0,
        le=1,
    )


class BookRelationshipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    relationship_id: str
    pair_key: str

    document_a_id: str
    document_b_id: str

    relationship_type: str
    status: str

    exact_hash_match: bool
    isbn_match: bool

    title_similarity: float | None
    author_similarity: float | None
    metadata_overlap_score: float | None
    content_overlap_score: float | None

    confidence: float

    reasons: list[str] | None

    document_a_snapshot: dict | None
    document_b_snapshot: dict | None

    recommended_primary_document_id: str | None
    recommended_superseded_document_id: str | None
    recommended_action: str | None

    detector_version: int

    review_notes: str | None
    reviewed_at: datetime | None

    created_at: datetime
    updated_at: datetime


class ScanBookRelationshipsResponse(BaseModel):
    document_id: str
    compared_documents: int
    candidate_count: int

    candidates: list[BookRelationshipResponse]
    warnings: list[str] = Field(default_factory=list)


class ReviewBookRelationshipRequest(BaseModel):
    action: Literal["approve", "reject"]

    relationship_type: RelationshipType | None = None

    recommended_primary_document_id: str | None = None
    recommended_superseded_document_id: str | None = None

    recommended_action: str | None = Field(
        default=None,
        max_length=100,
    )

    review_notes: str | None = Field(
        default=None,
        max_length=4000,
    )


class ReviewBookRelationshipResponse(BaseModel):
    relationship_id: str
    status: str
    relationship: BookRelationshipResponse