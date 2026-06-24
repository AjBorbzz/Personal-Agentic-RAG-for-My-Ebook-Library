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