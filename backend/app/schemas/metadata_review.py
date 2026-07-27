from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.document import DocumentResponse
from app.schemas.document_enrichment import EnrichedBookMetadata

from app.schemas.document_qdrant_sync import (
    DocumentQdrantSyncResponse,
)

class StageMetadataCandidateRequest(BaseModel):
    overwrite_existing: bool = False

    max_source_characters: int = Field(
        default=24000,
        ge=4000,
        le=60000,
    )


class MetadataCandidateResponse(BaseModel):
    document_id: str
    review_status: str

    candidate: EnrichedBookMetadata
    proposed_updates: dict[str, Any]

    source_characters_used: int
    source_was_truncated: bool
    warnings: list[str]

    document: DocumentResponse


class MetadataReviewStateResponse(BaseModel):
    document_id: str
    review_status: str

    candidate: EnrichedBookMetadata | None
    proposed_updates: dict[str, Any]

    review_notes: str | None
    metadata_confidence: float | None
    enriched_at: datetime | None
    reviewed_at: datetime | None

    document: DocumentResponse


class MetadataReviewRequest(BaseModel):
    action: Literal["approve", "reject"]

    overwrite_existing: bool = False

    edited_candidate: EnrichedBookMetadata | None = None

    review_notes: str | None = Field(
        default=None,
        max_length=4000,
    )

    sync_to_qdrant: bool = True


class MetadataReviewResponse(BaseModel):
    document_id: str
    action: Literal["approve", "reject"]
    review_status: str

    applied: bool
    updated_fields: list[str]

    candidate: EnrichedBookMetadata | None
    proposed_updates: dict[str, Any]

    document: DocumentResponse

    qdrant_sync: DocumentQdrantSyncResponse | None = None
    warnings: list[str] = Field(default_factory=list)