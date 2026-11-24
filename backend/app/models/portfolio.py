from __future__ import annotations

import uuid
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from app.db.base import Base


class PortfolioProject(Base):
    __tablename__ = "portfolio_projects"
    portfolio_project_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("personal_skill_profiles.profile_id", ondelete="RESTRICT"), nullable=False)
    career_target_id = Column(UUID(as_uuid=True), ForeignKey("career_targets.career_target_id", ondelete="RESTRICT"), nullable=False)
    title = Column(Text, nullable=False)
    slug = Column(String(160), nullable=False)
    problem_statement = Column(Text, nullable=False)
    status = Column(String(24), nullable=False, default="idea")
    scope = Column(JSONB, nullable=False, default=dict)
    architecture = Column(JSONB, nullable=False, default=dict)
    tech_stack = Column(JSONB, nullable=False, default=list)
    target_skill_ids = Column(JSONB, nullable=False, default=list)
    source_document_ids = Column(JSONB, nullable=False, default=list)
    source_mapping_ids = Column(JSONB, nullable=False, default=list)
    blueprint_versions = Column(JSONB, nullable=False, default=list)
    approved_blueprint_version = Column(Integer)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("profile_id", "slug", name="uq_portfolio_projects_profile_slug"),)


class PortfolioMilestone(Base):
    __tablename__ = "portfolio_milestones"
    milestone_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_project_id = Column(UUID(as_uuid=True), ForeignKey("portfolio_projects.portfolio_project_id", ondelete="CASCADE"), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False, default="")
    status = Column(String(16), nullable=False, default="planned")
    sequence_order = Column(Integer, nullable=False)
    acceptance_criteria = Column(JSONB, nullable=False, default=list)
    completion_notes = Column(Text)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("portfolio_project_id", "sequence_order", name="uq_portfolio_milestone_order"),)


class PortfolioArtifact(Base):
    __tablename__ = "portfolio_artifacts"
    artifact_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_project_id = Column(UUID(as_uuid=True), ForeignKey("portfolio_projects.portfolio_project_id", ondelete="CASCADE"), nullable=False)
    milestone_id = Column(UUID(as_uuid=True), ForeignKey("portfolio_milestones.milestone_id", ondelete="SET NULL"))
    artifact_type = Column(String(32), nullable=False)
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False, default="")
    file_path = Column(Text)
    source_url = Column(Text)
    verification_status = Column(String(16), nullable=False, default="draft")
    claim_scope = Column(String(16), nullable=False, default="planned")
    evidence = Column(JSONB, nullable=False, default=dict)
    version = Column(Integer, nullable=False, default=1)
    revision_history = Column(JSONB, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())