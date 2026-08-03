from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Boolean,
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


class SkillDomain(Base):
    __tablename__ = "skill_domains"

    domain_id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    slug: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        unique=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        unique=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class SkillCategory(Base):
    __tablename__ = "skill_categories"

    __table_args__ = (
        UniqueConstraint(
            "domain_id",
            "slug",
            name="uq_skill_categories_domain_slug",
        ),
    )

    category_id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    domain_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey(
            "skill_domains.domain_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    parent_category_id: Mapped[str | None] = mapped_column(
        String(100),
        ForeignKey(
            "skill_categories.category_id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    slug: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class Skill(Base):
    __tablename__ = "skills"

    skill_id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    domain_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey(
            "skill_domains.domain_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    category_id: Mapped[str | None] = mapped_column(
        String(100),
        ForeignKey(
            "skill_categories.category_id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    slug: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
        unique=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(240),
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    skill_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="concept",
        index=True,
    )
    # concept
    # practice
    # language
    # framework
    # platform
    # tool
    # architecture
    # methodology

    difficulty_level: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="foundational",
        index=True,
    )
    # foundational
    # intermediate
    # advanced
    # expert

    tags: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    is_deprecated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    superseded_by_skill_id: Mapped[str | None] = (
        mapped_column(
            String(100),
            ForeignKey(
                "skills.skill_id",
                ondelete="SET NULL",
            ),
            nullable=True,
            index=True,
        )
    )

    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="manual",
    )
    # manual
    # imported
    # llm_candidate
    # reviewed_llm

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class SkillAlias(Base):
    __tablename__ = "skill_aliases"

    __table_args__ = (
        UniqueConstraint(
            "skill_id",
            "normalized_alias",
            name="uq_skill_aliases_skill_alias",
        ),
    )

    alias_id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
        default=lambda: str(uuid4()),
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

    alias: Mapped[str] = mapped_column(
        String(240),
        nullable=False,
    )

    normalized_alias: Mapped[str] = mapped_column(
        String(240),
        nullable=False,
        index=True,
    )

    alias_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="synonym",
    )
    # synonym
    # abbreviation
    # product_name
    # former_name
    # alternate_spelling

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )


class SkillRelationship(Base):
    __tablename__ = "skill_relationships"

    __table_args__ = (
        UniqueConstraint(
            "source_skill_id",
            "target_skill_id",
            "relationship_type",
            name="uq_skill_relationships_edge",
        ),
    )

    relationship_id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    source_skill_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey(
            "skills.skill_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    target_skill_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey(
            "skills.skill_id",
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
    # prerequisite
    # related
    # complements
    # supersedes

    strength: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="manual",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class ProficiencyLevel(Base):
    __tablename__ = "proficiency_levels"

    level_id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        unique=True,
    )

    level_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        unique=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    evidence_expectations: Mapped[list | None] = (
        mapped_column(
            JSON,
            nullable=True,
        )
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )