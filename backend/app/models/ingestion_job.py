from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    job_id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    document_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="queued",
        index=True,
    )
    # queued, running, completed, failed, cancelled

    current_step: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    progress_percent: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    original_filename: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    stored_filename: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    upload_path: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    file_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    content_hash: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )

    source_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    tool_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    tool_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    version_major: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    version_minor: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    publication_year: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        index=True,
    )

    is_deprecated: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
    )

    index_after_ingest: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    attempt_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    max_attempts: Mapped[int] = mapped_column(
        Integer,
        default=3,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    result: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )