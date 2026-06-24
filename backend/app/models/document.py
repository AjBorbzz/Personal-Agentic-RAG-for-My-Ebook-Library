from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Document(Base):
    __tablename__ = "documents"

    document_id: Mapped[str] = mapped_column(String(100), primary_key=True)

    filename: Mapped[str | None] = mapped_column(String(500), nullable=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    author: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    source_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tool_name: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    tool_version: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    version_major: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    version_minor: Mapped[int | None] = mapped_column(Integer, nullable=True)

    publication_year: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    publication_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    primary_domain: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    domains: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    text_characters: Mapped[int | None] = mapped_column(Integer, nullable=True)

    content_hash: Mapped[str | None] = mapped_column(String(128), unique=True, index=True, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_deprecated: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    superseded_by_document_id: Mapped[str | None] = mapped_column(
        String(100),
        ForeignKey("documents.document_id"),
        nullable=True,
    )

    saved_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_output_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    chunks_output_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )