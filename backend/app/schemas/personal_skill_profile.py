from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


LearningStatus = Literal[
    "not_started",
    "planned",
    "learning",
    "practicing",
    "demonstrated",
    "maintained",
    "paused",
]

EvidenceType = Literal[
    "project",
    "work_experience",
    "certification",
    "course",
    "assessment",
    "repository",
    "exercise",
    "publication",
    "manual",
]

EvidenceVerificationStatus = Literal[
    "unverified",
    "reviewed",
    "verified",
    "rejected",
]


# ============================================================
# Personal Skill Profile
# ============================================================


class PersonalSkillProfileBase(BaseModel):
    profile_name: str = Field(
        min_length=1,
        max_length=255,
    )
    description: str | None = None
    is_default: bool = False
    is_active: bool = True


class PersonalSkillProfileCreate(PersonalSkillProfileBase):
    pass


class PersonalSkillProfileUpdate(BaseModel):
    profile_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )
    description: str | None = None
    is_default: bool | None = None
    is_active: bool | None = None


class PersonalSkillProfileRead(PersonalSkillProfileBase):
    model_config = ConfigDict(from_attributes=True)

    profile_id: UUID
    created_at: datetime
    updated_at: datetime


# ============================================================
# Personal Skill State
# ============================================================


class PersonalSkillStateBase(BaseModel):
    # Existing Phase 13C proficiency identifiers are string-backed
    # in the current repository.
    current_level_id: str | None = None
    target_level_id: str | None = None

    confidence: Decimal | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    career_priority: int = Field(
        default=3,
        ge=1,
        le=5,
    )

    learning_status: LearningStatus = "not_started"

    last_assessed_at: datetime | None = None
    notes: str | None = None


class PersonalSkillStateCreate(PersonalSkillStateBase):
    profile_id: UUID

    # Existing canonical Phase 13C skill identity is string-backed.
    skill_id: str = Field(min_length=1)


class PersonalSkillStateUpdate(BaseModel):
    current_level_id: str | None = None
    target_level_id: str | None = None

    confidence: Decimal | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    career_priority: int | None = Field(
        default=None,
        ge=1,
        le=5,
    )

    learning_status: LearningStatus | None = None

    last_assessed_at: datetime | None = None
    notes: str | None = None


class PersonalSkillStateRead(PersonalSkillStateBase):
    model_config = ConfigDict(from_attributes=True)

    profile_skill_id: UUID
    profile_id: UUID
    skill_id: str

    created_at: datetime
    updated_at: datetime


# ============================================================
# Personal Skill Evidence
# ============================================================


class PersonalSkillEvidenceBase(BaseModel):
    evidence_type: EvidenceType

    title: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str | None = None
    evidence_date: datetime | None = None

    strength: int | None = Field(
        default=None,
        ge=1,
        le=5,
    )

    verification_status: EvidenceVerificationStatus = "unverified"

    # Kept as str rather than HttpUrl because the project may store
    # local references as well as external URLs.
    source_url: str | None = None

    # Existing documents.document_id is string-backed.
    source_document_id: str | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)


class PersonalSkillEvidenceCreate(PersonalSkillEvidenceBase):
    profile_skill_id: UUID


class PersonalSkillEvidenceUpdate(BaseModel):
    evidence_type: EvidenceType | None = None

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    description: str | None = None
    evidence_date: datetime | None = None

    strength: int | None = Field(
        default=None,
        ge=1,
        le=5,
    )

    verification_status: EvidenceVerificationStatus | None = None

    source_url: str | None = None
    source_document_id: str | None = None

    metadata: dict[str, Any] | None = None


class PersonalSkillEvidenceRead(PersonalSkillEvidenceBase):
    model_config = ConfigDict(from_attributes=True)

    evidence_id: UUID
    profile_skill_id: UUID

    # SQLAlchemy cannot use "metadata" as the ORM attribute name.
    # The model maps the DB column "metadata" to evidence_metadata.
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias=AliasChoices(
            "evidence_metadata",
            "metadata",
        ),
    )

    created_at: datetime
    updated_at: datetime


# ============================================================
# Career targets
# ============================================================


CareerTargetStatus = Literal[
    "exploring",
    "active",
    "paused",
    "achieved",
]


class CareerTargetCreate(BaseModel):
    profile_id: UUID

    role_name: str = Field(
        min_length=1,
        max_length=255,
    )

    role_slug: str = Field(
        min_length=1,
        max_length=160,
    )

    description: str | None = None

    priority: int = Field(
        ge=1,
        le=5,
    )

    status: CareerTargetStatus

    target_date: date | None = None


class CareerTargetRead(CareerTargetCreate):
    model_config = ConfigDict(
        from_attributes=True
    )

    career_target_id: UUID

    created_at: datetime
    updated_at: datetime


class CareerTargetSkillSet(BaseModel):
    required_level_id: str = Field(
        min_length=1,
    )

    importance_weight: int = Field(
        ge=1,
        le=5,
    )

    is_required: bool

    rationale: str | None = None


class CareerTargetSkillRead(
    CareerTargetSkillSet
):
    model_config = ConfigDict(
        from_attributes=True
    )

    career_target_skill_id: UUID

    career_target_id: UUID

    skill_id: str

    created_at: datetime
    updated_at: datetime