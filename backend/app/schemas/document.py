from datetime import date, datetime
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class DocumentCreate(BaseModel):
    document_id: str = Field(default_factory=lambda: str(uuid4()))

    filename: str | None = None
    title: str | None = None
    author: str | None = None
    file_type: str | None = None

    source_type: str | None = None
    tool_name: str | None = None
    tool_version: str | None = None
    version_major: int | None = None
    version_minor: int | None = None

    publication_year: int | None = None
    publication_date: date | None = None

    primary_domain: str | None = None
    domains: list[str] | None = None

    page_count: int | None = None
    chunk_count: int | None = None
    text_characters: int | None = None

    content_hash: str | None = None

    is_active: bool = True
    is_deprecated: bool = False
    superseded_by_document_id: str | None = None

    saved_path: str | None = None
    parsed_output_path: str | None = None
    chunks_output_path: str | None = None

    notes: str | None = None

    subtitle: str | None = None
    publisher: str | None = None
    edition: str | None = None

    isbn_10: str | None = None
    isbn_13: str | None = None
    language: str | None = None

    description: str | None = None
    difficulty_level: str | None = None

    topics: list[str] | None = None
    technologies: list[str] | None = None
    tags: list[str] | None = None
    prerequisite_skills: list[str] | None = None

    metadata_source: str | None = None
    metadata_confidence: float | None = None
    metadata_reviewed: bool = False


class DocumentUpdate(BaseModel):
    filename: str | None = None
    title: str | None = None
    author: str | None = None
    file_type: str | None = None

    source_type: str | None = None
    tool_name: str | None = None
    tool_version: str | None = None
    version_major: int | None = None
    version_minor: int | None = None

    publication_year: int | None = None
    publication_date: date | None = None

    primary_domain: str | None = None
    domains: list[str] | None = None

    page_count: int | None = None
    chunk_count: int | None = None
    text_characters: int | None = None

    content_hash: str | None = None

    is_active: bool | None = None
    is_deprecated: bool | None = None
    superseded_by_document_id: str | None = None

    saved_path: str | None = None
    parsed_output_path: str | None = None
    chunks_output_path: str | None = None

    notes: str | None = None

    subtitle: str | None = None
    publisher: str | None = None
    edition: str | None = None

    isbn_10: str | None = None
    isbn_13: str | None = None
    language: str | None = None

    description: str | None = None
    difficulty_level: str | None = None

    topics: list[str] | None = None
    technologies: list[str] | None = None
    tags: list[str] | None = None
    prerequisite_skills: list[str] | None = None

    metadata_source: str | None = None
    metadata_confidence: float | None = Field(
            default=None,
            ge=0.0,
            le=1.0,
        )
    metadata_reviewed: bool | None = None


class DocumentDeprecateRequest(BaseModel):
    superseded_by_document_id: str | None = None
    notes: str | None = None


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: str

    filename: str | None
    title: str | None
    author: str | None
    file_type: str | None

    source_type: str | None
    tool_name: str | None
    tool_version: str | None
    version_major: int | None
    version_minor: int | None

    publication_year: int | None
    publication_date: date | None

    primary_domain: str | None
    domains: list[str] | None

    page_count: int | None
    chunk_count: int | None
    text_characters: int | None

    content_hash: str | None

    is_active: bool
    is_deprecated: bool
    superseded_by_document_id: str | None

    saved_path: str | None
    parsed_output_path: str | None
    chunks_output_path: str | None

    notes: str | None

    ingested_at: datetime
    created_at: datetime
    updated_at: datetime

    subtitle: str | None
    publisher: str | None
    edition: str | None

    isbn_10: str | None
    isbn_13: str | None
    language: str | None

    description: str | None
    difficulty_level: str | None

    topics: list[str] | None
    technologies: list[str] | None
    tags: list[str] | None
    prerequisite_skills: list[str] | None

    metadata_source: str | None
    metadata_confidence: float | None
    metadata_reviewed: bool
    enriched_at: datetime | None