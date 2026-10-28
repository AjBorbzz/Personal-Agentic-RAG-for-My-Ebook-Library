from uuid import UUID

from pydantic import BaseModel, Field


class SkillGapSummary(BaseModel):
    tracked_skills: int = Field(ge=0)
    target_skills: int = Field(ge=0)
    met_or_exceeded: int = Field(ge=0)
    level_gaps: int = Field(ge=0)
    unknown_current_level: int = Field(ge=0)
    missing_prerequisites: int = Field(ge=0)


class SkillGapItem(BaseModel):
    skill_id: UUID
    skill_name: str

    current_level: str | None = None
    target_level: str

    gap_steps: int | None = Field(default=None, ge=0)

    career_importance: int = Field(ge=1, le=5)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)

    gap_type: str

    missing_prerequisite_skill_ids: list[UUID] = Field(
        default_factory=list
    )

    approved_supporting_book_count: int = Field(ge=0)

    explanation: str


class SkillGapResponse(BaseModel):
    profile_id: UUID
    career_target_id: UUID | None = None

    summary: SkillGapSummary
    gaps: list[SkillGapItem] = Field(default_factory=list)