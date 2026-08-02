from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BookRelationship(Base):
    __tablename__ = "book_relationships"

    __table_args__ = (
        UniqueConstraint(
            "pair_key",
            name="uq_book_relationships_pair_key",
        ),
    )

    relationship_id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Canonical sorted pair, preventing duplicate A↔B records.
    pair_key: Mapped[str] = mapped_column(
        String(250),
        unique=True,
        nullable=False,
        index=True,
    )

    document_a_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey(
            "documents.document_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    document_b_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey(
            "documents.document_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    relationship_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    # exact_duplicate
    # same_edition
    # different_edition
    # high_content_overlap
    # related_topic

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        index=True,
    )
    # pending, approved, rejected

    exact_hash_match: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    isbn_match: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    title_similarity: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    author_similarity: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    metadata_overlap_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    content_overlap_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True,
    )

    reasons: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    document_a_snapshot: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    document_b_snapshot: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    recommended_primary_document_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    recommended_superseded_document_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    recommended_action: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    # keep_both, review_editions, deprecate_older, archive_duplicate

    detector_version: Mapped[int] = mapped_column(
        default=1,
        nullable=False,
    )

    review_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )