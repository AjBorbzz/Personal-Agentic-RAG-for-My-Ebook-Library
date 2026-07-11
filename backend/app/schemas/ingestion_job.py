from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IngestionJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str
    document_id: str | None

    status: str

    original_filename: str | None
    stored_filename: str | None
    upload_path: str | None
    file_type: str | None

    content_hash: str | None

    source_type: str | None
    tool_name: str | None
    tool_version: str | None
    version_major: int | None
    version_minor: int | None
    publication_year: int | None

    is_active: bool
    is_deprecated: bool

    notes: str | None

    result: dict | None
    error_message: str | None

    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class CancelJobResponse(BaseModel):
    job_id: str
    status: str
    message: str