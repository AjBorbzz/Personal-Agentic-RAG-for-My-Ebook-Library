from typing import Any

from pydantic import BaseModel, Field

from app.schemas.document import DocumentResponse


class EnrichedBookMetadata(BaseModel):
    title: str | None = None
    author: str | None = None
    subtitle: str | None = None
    publisher: str | None = None
    edition: str | None = None

    isbn_10: str | None = None
    isbn_13: str | None = None
    language: str | None = None
    publication_year: int | None = Field(
        default=None,
        ge=1000,
        le=2100,
    )

    description: str | None = None

    difficulty_level: str | None = None

    topics: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    prerequisite_skills: list[str] = Field(default_factory=list)

    metadata_confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
    )


class DocumentEnrichmentRequest(BaseModel):
    dry_run: bool = True
    overwrite_existing: bool = False

    max_source_characters: int = Field(
        default=24000,
        ge=4000,
        le=60000,
    )


class DocumentEnrichmentResponse(BaseModel):
    document_id: str

    dry_run: bool
    applied: bool
    overwrite_existing: bool

    source_characters_used: int
    source_was_truncated: bool

    candidate: EnrichedBookMetadata
    proposed_updates: dict[str, Any]
    updated_fields: list[str]
    warnings: list[str]

    document: DocumentResponse