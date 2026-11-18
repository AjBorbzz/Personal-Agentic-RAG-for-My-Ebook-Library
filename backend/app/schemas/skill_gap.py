from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SkillGapSummary(BaseModel):
    """Nonnegative totals derived by the Phase 13E.5 engine."""

    model_config = ConfigDict(extra="forbid")

    tracked_skills: int = Field(ge=0)
    target_skills: int = Field(ge=0)
    met_or_exceeded: int = Field(ge=0)
    level_gaps: int = Field(ge=0)
    unknown_current_level: int = Field(ge=0)
    missing_prerequisites: int = Field(ge=0)


class SkillGapItem(BaseModel):
    """One explainable, canonical skill-gap result."""

    model_config = ConfigDict(extra="forbid")

    skill_id: str = Field(min_length=1)
    skill_name: str = Field(min_length=1)

    current_level: str | None = None
    target_level: str | None = None
    gap_steps: int | None = Field(default=None, ge=0)

    career_importance: int | None = Field(
        default=None,
        ge=1,
        le=5,
    )
    confidence: Decimal | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    # Specific classification/precedence remains a Part 2 engine decision.
    gap_type: str = Field(min_length=1)
    missing_prerequisite_skill_ids: list[str] = Field(
        default_factory=list,
    )
    approved_supporting_book_count: int = Field(ge=0)
    explanation: str = Field(min_length=1)


class SkillGapResponse(BaseModel):
    """Computed response; no changes to PostgreSQL state."""

    model_config = ConfigDict(extra="forbid")

    profile_id: UUID
    career_target_id: UUID | None = None
    summary: SkillGapSummary
    gaps: list[SkillGapItem] = Field(default_factory=list)