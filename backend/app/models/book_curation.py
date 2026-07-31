from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BookCuration(Base):
    __tablename__ = "book_curations"

    __table_args__ = (
        CheckConstraint(
            "overall_score IS NULL OR "
            "(overall_score >= 0 AND overall_score <= 100)",
            name="ck_book_curations_overall_score",
        ),
        CheckConstraint(
            "technical_depth_score IS NULL OR "
            "(technical_depth_score >= 0 AND technical_depth_score <= 100)",
            name="ck_book_curations_technical_depth_score",
        ),
        CheckConstraint(
            "practicality_score IS NULL OR "
            "(practicality_score >= 0 AND practicality_score <= 100)",
            name="ck_book_curations_practicality_score",
        ),
        CheckConstraint(
            "freshness_score IS NULL OR "
            "(freshness_score >= 0 AND freshness_score <= 100)",
            name="ck_book_curations_freshness_score",
        ),
        CheckConstraint(
            "authority_score IS NULL OR "
            "(authority_score >= 0 AND authority_score <= 100)",
            name="ck_book_curations_authority_score",
        ),
        CheckConstraint(
            "clarity_score IS NULL OR "
            "(clarity_score >= 0 AND clarity_score <= 100)",
            name="ck_book_curations_clarity_score",
        ),
        CheckConstraint(
            "outdated_risk_score IS NULL OR "
            "(outdated_risk_score >= 0 AND outdated_risk_score <= 100)",
            name="ck_book_curations_outdated_risk_score",
        ),
        CheckConstraint(
            "confidence IS NULL OR "
            "(confidence >= 0 AND confidence <= 1)",
            name="ck_book_curations_confidence",
        ),
    )

    curation_id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    document_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey(
            "documents.document_id",
            ondelete="CASCADE",
        ),
        unique=True,
        nullable=False,
        index=True,
    )

    evaluation_status: Mapped[str] = mapped_column(
        String(30),
        default="not_evaluated",
        nullable=False,
        index=True,
    )
    # not_evaluated, generating, pending, approved, rejected, failed

    overall_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        index=True,
    )

    technical_depth_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    practicality_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    freshness_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    authority_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    clarity_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    outdated_risk_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    audience_level: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    # beginner, intermediate, advanced, mixed

    recommended_role: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    # foundational, practical_guide, reference, advanced_specialist,
    # supplementary, historical, redundant, avoid

    library_priority: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        index=True,
    )
    # essential, high, medium, low, archive

    curator_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    unique_value: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    strengths: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    weaknesses: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    best_for: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    not_recommended_for: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    outdated_topics: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    evaluation_source: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )
    # llm, manual, llm_reviewed

    evaluation_model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    evaluation_version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    metadata_snapshot: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    evaluation_candidate: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    review_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    evaluated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
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

    evaluation_error: Mapped[str | None] = mapped_column(
    Text,
    nullable=True,
)