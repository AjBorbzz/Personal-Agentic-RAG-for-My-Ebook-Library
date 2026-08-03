from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BookSkillMapping(Base):
    __tablename__ = "book_skill_mappings"

    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "skill_id",
            name="uq_book_skill_mappings_document_skill",
        ),
        CheckConstraint(
            "relevance_score IS NULL "
            "OR (relevance_score >= 0 "
            "AND relevance_score <= 100)",
            name="ck_book_skill_mapping_relevance",
        ),
        CheckConstraint(
            "coverage_score IS NULL "
            "OR (coverage_score >= 0 "
            "AND coverage_score <= 100)",
            name="ck_book_skill_mapping_coverage",
        ),
        CheckConstraint(
            "depth_score IS NULL "
            "OR (depth_score >= 0 "
            "AND depth_score <= 100)",
            name="ck_book_skill_mapping_depth",
        ),
        CheckConstraint(
            "practicality_score IS NULL "
            "OR (practicality_score >= 0 "
            "AND practicality_score <= 100)",
            name="ck_book_skill_mapping_practicality",
        ),
        CheckConstraint(
            "confidence IS NULL "
            "OR (confidence >= 0 "
            "AND confidence <= 1)",
            name="ck_book_skill_mapping_confidence",
        ),
    )

    mapping_id: Mapped[str] = mapped_column(
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
        nullable=False,
        index=True,
    )

    skill_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey(
            "skills.skill_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    mapping_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        index=True,
    )
    # generating
    # pending
    # approved
    # rejected
    # failed

    coverage_level: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
        index=True,
    )
    # mention
    # introductory
    # working
    # advanced
    # comprehensive

    is_primary_skill: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    relevance_score: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )

    coverage_score: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )

    depth_score: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )

    practicality_score: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )

    confidence: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )

    recommended_entry_level_id: Mapped[
        str | None
    ] = mapped_column(
        String(100),
        ForeignKey(
            "proficiency_levels.level_id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    recommended_exit_level_id: Mapped[
        str | None
    ] = mapped_column(
        String(100),
        ForeignKey(
            "proficiency_levels.level_id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    coverage_summary: Mapped[str | None] = (
        mapped_column(
            Text,
            nullable=True,
        )
    )

    learning_outcomes: Mapped[
        list | None
    ] = mapped_column(
        JSON,
        nullable=True,
    )

    covered_topics: Mapped[
        list | None
    ] = mapped_column(
        JSON,
        nullable=True,
    )

    limitations: Mapped[
        list | None
    ] = mapped_column(
        JSON,
        nullable=True,
    )

    mapping_source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="manual",
        index=True,
    )
    # manual
    # metadata
    # llm
    # llm_reviewed
    # imported

    mapping_model: Mapped[str | None] = (
        mapped_column(
            String(200),
            nullable=True,
        )
    )

    mapping_version: Mapped[int] = (
        mapped_column(
            Integer,
            nullable=False,
            default=1,
        )
    )

    candidate_payload: Mapped[
        dict | None
    ] = mapped_column(
        JSON,
        nullable=True,
    )

    candidate_error: Mapped[str | None] = (
        mapped_column(
            Text,
            nullable=True,
        )
    )

    candidate_generated_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    review_notes: Mapped[str | None] = (
        mapped_column(
            Text,
            nullable=True,
        )
    )

    reviewed_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = (
        mapped_column(
            DateTime(timezone=True),
            nullable=False,
            default=utc_now,
        )
    )

    updated_at: Mapped[datetime] = (
        mapped_column(
            DateTime(timezone=True),
            nullable=False,
            default=utc_now,
            onupdate=utc_now,
        )
    )


class BookSkillEvidence(Base):
    __tablename__ = "book_skill_evidence"

    __table_args__ = (
        CheckConstraint(
            "confidence IS NULL "
            "OR (confidence >= 0 "
            "AND confidence <= 1)",
            name="ck_book_skill_evidence_confidence",
        ),
        CheckConstraint(
            "page_start IS NULL "
            "OR page_start >= 1",
            name="ck_book_skill_evidence_page_start",
        ),
        CheckConstraint(
            "page_end IS NULL "
            "OR page_end >= 1",
            name="ck_book_skill_evidence_page_end",
        ),
        CheckConstraint(
            "page_end IS NULL "
            "OR page_start IS NULL "
            "OR page_end >= page_start",
            name="ck_book_skill_evidence_page_range",
        ),
    )

    evidence_id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    mapping_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey(
            "book_skill_mappings.mapping_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    evidence_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        index=True,
    )
    # chapter
    # section
    # page
    # chunk
    # metadata
    # manual

    chapter_title: Mapped[str | None] = (
        mapped_column(
            String(500),
            nullable=True,
        )
    )

    section_title: Mapped[str | None] = (
        mapped_column(
            String(500),
            nullable=True,
        )
    )

    page_start: Mapped[int | None] = (
        mapped_column(
            Integer,
            nullable=True,
        )
    )

    page_end: Mapped[int | None] = (
        mapped_column(
            Integer,
            nullable=True,
        )
    )

    chunk_id: Mapped[str | None] = (
        mapped_column(
            String(200),
            nullable=True,
            index=True,
        )
    )

    excerpt: Mapped[str | None] = (
        mapped_column(
            Text,
            nullable=True,
        )
    )

    source_locator: Mapped[
        dict | None
    ] = mapped_column(
        JSON,
        nullable=True,
    )

    confidence: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )

    display_order: Mapped[int] = (
        mapped_column(
            Integer,
            nullable=False,
            default=0,
        )
    )

    created_at: Mapped[datetime] = (
        mapped_column(
            DateTime(timezone=True),
            nullable=False,
            default=utc_now,
        )
    )