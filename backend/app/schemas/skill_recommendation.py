"""Phase 13F public API contracts (Pydantic v2)."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


DecisionStatus = Literal["new", "accepted", "deferred", "dismissed", "completed"]
QueueStatus = Literal["queued", "active", "paused", "completed", "removed"]
RecommendationType = Literal["prerequisite", "book", "project", "evidence", "review", "learning_path"]


class GenerateRecommendationsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile_id: UUID
    career_target_id: UUID | None = None
    domain_slug: str | None = Field(default=None, min_length=1)
    max_books_per_skill: int = Field(default=2, ge=0, le=5)


class RecommendationRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    recommendation_run_id: UUID
    profile_id: UUID
    career_target_id: UUID | None
    rule_version: str
    input_snapshot: dict
    status: str
    generated_at: datetime
    error_detail: str | None


class SkillRecommendationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    recommendation_id: UUID
    recommendation_run_id: UUID
    skill_id: str
    recommendation_type: RecommendationType
    priority_score: Decimal
    score_components: dict
    source_mapping_ids: list[str]
    recommended_document_id: str | None
    title: str
    explanation: str
    decision_status: DecisionStatus
    decision_notes: str | None
    created_at: datetime
    updated_at: datetime


class RecommendationRunDetail(BaseModel):
    run: RecommendationRunRead
    items: list[SkillRecommendationRead]


class RecommendationDecisionPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision_status: DecisionStatus
    decision_notes: str | None = Field(default=None, max_length=2000)


class ReadingQueueCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile_id: UUID
    recommendation_id: UUID | None = None
    document_id: str | None = Field(default=None, min_length=1)
    skill_id: str | None = Field(default=None, min_length=1)
    priority: int = Field(default=3, ge=1, le=5)
    planned_start: date | None = None
    target_finish: date | None = None
    notes: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def check_target_and_dates(self):
        if not (self.recommendation_id or self.document_id or self.skill_id):
            raise ValueError("A recommendation, document or skill must be supplied.")
        if self.planned_start and self.target_finish and self.target_finish < self.planned_start:
            raise ValueError("target_finish must be on or after planned_start.")
        return self


class ReadingQueuePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: QueueStatus | None = None
    priority: int | None = Field(default=None, ge=1, le=5)
    planned_start: date | None = None
    target_finish: date | None = None
    progress_percent: int | None = Field(default=None, ge=0, le=100)
    notes: str | None = Field(default=None, max_length=4000)


class ReadingQueueRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    reading_queue_item_id: UUID
    profile_id: UUID
    document_id: str | None
    skill_id: str | None
    recommendation_id: UUID | None
    status: QueueStatus
    priority: int
    planned_start: date | None
    target_finish: date | None
    progress_percent: int
    notes: str | None
    created_at: datetime
    updated_at: datetime


class AgentSeedRead(BaseModel):
    """Structured seed only; NOT a call to an existing agent API."""
    agent_type: Literal["project", "learning_path"]
    profile_id: UUID
    career_target_id: UUID | None
    recommendation_id: UUID
    primary_skill_id: str
    skill_ids: list[str]
    source_document_ids: list[str]
    source_mapping_ids: list[str]
    title: str
    objective: str