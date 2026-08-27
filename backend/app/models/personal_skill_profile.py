from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class PersonalSkillProfile(Base):
    __tablename__ = "personal_skill_profiles"

    profile_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    profile_name = Column(
        String(255),
        nullable=False,
    )

    description = Column(
        Text,
        nullable=True,
    )

    is_default = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    skill_states = relationship(
        "PersonalSkillState",
        back_populates="profile",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index(
            "uq_personal_skill_profiles_one_default",
            "is_default",
            unique=True,
            postgresql_where=text("is_default = true"),
        ),
        Index(
            "ix_personal_skill_profiles_is_active",
            "is_active",
        ),
    )


class PersonalSkillState(Base):
    __tablename__ = "personal_skill_states"

    profile_skill_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "personal_skill_profiles.profile_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    # Phase 13C canonical skill IDs are string-backed
    # in the current PostgreSQL schema.
    skill_id = Column(
        String,
        ForeignKey("skills.skill_id"),
        nullable=False,
    )

    # Current live proficiency PK is proficiency_levels.level_id.
    current_level_id = Column(
        String,
        ForeignKey("proficiency_levels.level_id"),
        nullable=True,
    )

    target_level_id = Column(
        String,
        ForeignKey("proficiency_levels.level_id"),
        nullable=True,
    )

    confidence = Column(
        Numeric(4, 3),
        nullable=True,
    )

    career_priority = Column(
        Integer,
        nullable=False,
        default=3,
        server_default=text("3"),
    )

    learning_status = Column(
        String(32),
        nullable=False,
        default="not_started",
        server_default=text("'not_started'"),
    )

    last_assessed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    notes = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    profile = relationship(
        "PersonalSkillProfile",
        back_populates="skill_states",
    )

    evidence = relationship(
        "PersonalSkillEvidence",
        back_populates="skill_state",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "profile_id",
            "skill_id",
            name="uq_personal_skill_states_profile_skill",
        ),
        CheckConstraint(
            "confidence IS NULL OR "
            "(confidence >= 0 AND confidence <= 1)",
            name="ck_personal_skill_states_confidence",
        ),
        CheckConstraint(
            "career_priority >= 1 AND career_priority <= 5",
            name="ck_personal_skill_states_career_priority",
        ),
        CheckConstraint(
            "learning_status IN ("
            "'not_started', "
            "'planned', "
            "'learning', "
            "'practicing', "
            "'demonstrated', "
            "'maintained', "
            "'paused'"
            ")",
            name="ck_personal_skill_states_learning_status",
        ),
        Index(
            "ix_personal_skill_states_profile_id",
            "profile_id",
        ),
        Index(
            "ix_personal_skill_states_skill_id",
            "skill_id",
        ),
        Index(
            "ix_personal_skill_states_current_level_id",
            "current_level_id",
        ),
        Index(
            "ix_personal_skill_states_target_level_id",
            "target_level_id",
        ),
        Index(
            "ix_personal_skill_states_learning_status",
            "learning_status",
        ),
    )


class PersonalSkillEvidence(Base):
    __tablename__ = "personal_skill_evidence"

    evidence_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    profile_skill_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "personal_skill_states.profile_skill_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    evidence_type = Column(
        String(32),
        nullable=False,
    )

    title = Column(
        String(255),
        nullable=False,
    )

    description = Column(
        Text,
        nullable=True,
    )

    evidence_date = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    strength = Column(
        Integer,
        nullable=True,
    )

    verification_status = Column(
        String(32),
        nullable=False,
        default="unverified",
        server_default=text("'unverified'"),
    )

    source_url = Column(
        Text,
        nullable=True,
    )

    # Existing documents.document_id is string-backed.
    source_document_id = Column(
        String,
        ForeignKey(
            "documents.document_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    # "metadata" cannot be used as the Python ORM attribute because
    # declarative Base already owns .metadata.
    evidence_metadata = Column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
        server_default=text("'{}'::json"),
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    skill_state = relationship(
        "PersonalSkillState",
        back_populates="evidence",
    )

    __table_args__ = (
        CheckConstraint(
            "evidence_type IN ("
            "'project', "
            "'work_experience', "
            "'certification', "
            "'course', "
            "'assessment', "
            "'repository', "
            "'exercise', "
            "'publication', "
            "'manual'"
            ")",
            name="ck_personal_skill_evidence_type",
        ),
        CheckConstraint(
            "strength IS NULL OR "
            "(strength >= 1 AND strength <= 5)",
            name="ck_personal_skill_evidence_strength",
        ),
        CheckConstraint(
            "verification_status IN ("
            "'unverified', "
            "'reviewed', "
            "'verified', "
            "'rejected'"
            ")",
            name="ck_personal_skill_evidence_verification_status",
        ),
        Index(
            "ix_personal_skill_evidence_profile_skill_id",
            "profile_skill_id",
        ),
        Index(
            "ix_personal_skill_evidence_verification_status",
            "verification_status",
        ),
        Index(
            "ix_personal_skill_evidence_source_document_id",
            "source_document_id",
        ),
    )


# ============================================================
# Career targets
# ============================================================


class CareerTarget(Base):
    __tablename__ = "career_targets"

    career_target_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "personal_skill_profiles.profile_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    role_name = Column(
        String(255),
        nullable=False,
    )

    role_slug = Column(
        String(160),
        nullable=False,
    )

    description = Column(
        Text,
        nullable=True,
    )

    priority = Column(
        Integer,
        nullable=False,
    )

    status = Column(
        String(32),
        nullable=False,
    )

    target_date = Column(
        Date,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    skill_requirements = relationship(
        "CareerTargetSkill",
        back_populates="career_target",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "profile_id",
            "role_slug",
            name=(
                "uq_career_targets_"
                "profile_role_slug"
            ),
        ),
        CheckConstraint(
            "priority >= 1 AND priority <= 5",
            name="ck_career_targets_priority",
        ),
        CheckConstraint(
            "status IN ("
            "'exploring', "
            "'active', "
            "'paused', "
            "'achieved'"
            ")",
            name="ck_career_targets_status",
        ),
        Index(
            "ix_career_targets_profile_id",
            "profile_id",
        ),
        Index(
            "ix_career_targets_status",
            "status",
        ),
        Index(
            "ix_career_targets_priority",
            "priority",
        ),
    )


class CareerTargetSkill(Base):
    __tablename__ = "career_target_skills"

    career_target_skill_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    career_target_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "career_targets.career_target_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    skill_id = Column(
        String(100),
        ForeignKey("skills.skill_id"),
        nullable=False,
    )

    required_level_id = Column(
        String(100),
        ForeignKey(
            "proficiency_levels.level_id"
        ),
        nullable=False,
    )

    importance_weight = Column(
        Integer,
        nullable=False,
    )

    is_required = Column(
        Boolean,
        nullable=False,
    )

    rationale = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    career_target = relationship(
        "CareerTarget",
        back_populates="skill_requirements",
    )

    __table_args__ = (
        UniqueConstraint(
            "career_target_id",
            "skill_id",
            name=(
                "uq_career_target_skills_"
                "target_skill"
            ),
        ),
        CheckConstraint(
            "importance_weight >= 1 "
            "AND importance_weight <= 5",
            name=(
                "ck_career_target_skills_"
                "importance"
            ),
        ),
        Index(
            "ix_career_target_skills_target_id",
            "career_target_id",
        ),
        Index(
            "ix_career_target_skills_skill_id",
            "skill_id",
        ),
        Index(
            "ix_career_target_skills_"
            "required_level_id",
            "required_level_id",
        ),
        Index(
            "ix_career_target_skills_is_required",
            "is_required",
        ),
    )