"""Public Phase 15 contracts (Pydantic v2); do not infer evidence or proficiency."""
from __future__ import annotations
from datetime import datetime
from typing import Any, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator

ProjectStatus = Literal["idea", "approved", "planned", "in_progress", "blocked", "completed", "published", "archived"]
MilestoneStatus = Literal["planned", "active", "blocked", "completed", "skipped"]
ArtifactType = Literal["repository", "architecture", "README", "test_report", "demo", "case_study", "resume_bullet", "interview_story", "publication"]
ClaimScope = Literal["planned", "implemented", "tested", "measured", "published"]
VerificationStatus = Literal["draft", "reviewed", "verified", "published"]


class OpportunityRead(BaseModel):
    skill_id: str
    skill_name: str
    gap_type: str
    gap_steps: int | None
    career_importance: int | None
    explanation: str
    title_suggestion: str
    source_document_ids: list[str]
    source_mapping_ids: list[str]
    no_trusted_book_sources: bool


class ProjectCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile_id: UUID
    career_target_id: UUID
    title: str = Field(min_length=3, max_length=240)
    slug: str = Field(min_length=3, max_length=160, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    problem_statement: str = Field(min_length=10)
    target_skill_ids: list[str] = Field(min_length=1)

    @field_validator("target_skill_ids")
    @classmethod
    def distinct_skills(cls, items: list[str]):
        if not all(x.strip() for x in items) or len(items) != len(set(items)):
            raise ValueError("target_skill_ids must be distinct nonempty canonical IDs")
        return items


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    portfolio_project_id: UUID
    profile_id: UUID
    career_target_id: UUID
    title: str
    slug: str
    problem_statement: str
    status: ProjectStatus
    scope: dict[str, Any]
    architecture: dict[str, Any]
    tech_stack: list[Any]
    target_skill_ids: list[str]
    source_document_ids: list[str]
    source_mapping_ids: list[str]
    blueprint_versions: list[dict[str, Any]]
    approved_blueprint_version: int | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


class BlueprintSubmit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    specification: dict[str, Any] = Field(description="Paste exact POST /project-generator response, without inventing fields")
    review_notes: str | None = Field(default=None, max_length=2000)


class BlueprintApprove(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: int = Field(ge=1)
    review_notes: str = Field(min_length=3, max_length=2000)


class ProjectStatusPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: ProjectStatus


class MilestoneCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=3)
    description: str = ""
    sequence_order: int = Field(ge=1)
    acceptance_criteria: list[str] = Field(min_length=1)


class MilestonePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: MilestoneStatus
    completion_notes: str | None = Field(default=None, max_length=4000)


class MilestoneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    milestone_id: UUID
    portfolio_project_id: UUID
    title: str
    description: str
    status: MilestoneStatus
    sequence_order: int
    acceptance_criteria: list[str]
    completion_notes: str | None
    started_at: datetime | None
    completed_at: datetime | None


class ArtifactCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    milestone_id: UUID | None = None
    artifact_type: ArtifactType
    title: str = Field(min_length=3)
    content: str = ""
    file_path: str | None = None
    source_url: str | None = None


class ArtifactReview(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claim_scope: ClaimScope
    verification_status: VerificationStatus
    evidence: dict[str, Any] = Field(default_factory=dict)
    review_notes: str = Field(min_length=3)
    content: str | None = None
    file_path: str | None = None
    source_url: str | None = None


class ArtifactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    artifact_id: UUID
    portfolio_project_id: UUID
    milestone_id: UUID | None
    artifact_type: ArtifactType
    title: str
    content: str
    file_path: str | None
    source_url: str | None
    verification_status: VerificationStatus
    claim_scope: ClaimScope
    evidence: dict[str, Any]
    version: int
    revision_history: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class DraftRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["README", "architecture", "case_study", "resume_bullet", "interview_story"]


class ReadinessRead(BaseModel):
    portfolio_project_id: UUID
    approved_blueprint: bool
    milestone_count: int
    completed_milestones: int
    verified_artifact_count: int
    missing: list[str]
    publication_ready: bool