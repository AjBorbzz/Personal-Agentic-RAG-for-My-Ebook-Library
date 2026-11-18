"""Phase 13F SQLAlchemy models (new module; no changes to old models)."""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import CheckConstraint, Column, Date, DateTime, ForeignKey, Index, Numeric, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.base import Base


class RecommendationRun(Base):
    __tablename__ = "recommendation_runs"

    recommendation_run_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("personal_skill_profiles.profile_id", ondelete="CASCADE"), nullable=False)
    career_target_id = Column(UUID(as_uuid=True), ForeignKey("career_targets.career_target_id", ondelete="SET NULL"), nullable=True)
    rule_version = Column(String(40), nullable=False)
    input_snapshot = Column(JSONB, nullable=False, default=dict)
    status = Column(String(16), nullable=False, default="running")
    generated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    error_detail = Column(Text)
    __table_args__ = (
        CheckConstraint("status IN ('running','completed','failed')", name="recommendation_runs_status_check"),
        Index("ix_recommendation_runs_profile_date", profile_id, generated_at.desc()),
    )


class SkillRecommendation(Base):
    __tablename__ = "skill_recommendations"

    recommendation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recommendation_run_id = Column(UUID(as_uuid=True), ForeignKey("recommendation_runs.recommendation_run_id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(String(100), ForeignKey("skills.skill_id"), nullable=False)
    recommendation_type = Column(String(32), nullable=False)
    priority_score = Column(Numeric(7, 2), nullable=False)
    score_components = Column(JSONB, nullable=False, default=dict)
    source_mapping_ids = Column(JSONB, nullable=False, default=list)
    recommended_document_id = Column(String(100), ForeignKey("documents.document_id"), nullable=True)
    title = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    decision_status = Column(String(16), nullable=False, default="new")
    decision_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    __table_args__ = (
        CheckConstraint("recommendation_type IN ('prerequisite','book','project','evidence','review','learning_path')", name="skill_recommendations_recommendation_type_check"),
        CheckConstraint("priority_score BETWEEN 0 AND 100", name="skill_recommendations_priority_score_check"),
        CheckConstraint("decision_status IN ('new','accepted','deferred','dismissed','completed')", name="skill_recommendations_decision_status_check"),
        Index("ix_skill_recommendations_run_priority", recommendation_run_id, priority_score.desc(), skill_id),
        Index("ix_skill_recommendations_skill", "skill_id"),
    )


class ReadingQueueItem(Base):
    __tablename__ = "reading_queue_items"

    reading_queue_item_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("personal_skill_profiles.profile_id", ondelete="CASCADE"), nullable=False)
    document_id = Column(String(100), ForeignKey("documents.document_id"), nullable=True)
    skill_id = Column(String(100), ForeignKey("skills.skill_id"), nullable=True)
    recommendation_id = Column(UUID(as_uuid=True), ForeignKey("skill_recommendations.recommendation_id", ondelete="SET NULL"), nullable=True)
    status = Column(String(16), nullable=False, default="queued")
    priority = Column(SmallInteger, nullable=False, default=3)
    planned_start = Column(Date)
    target_finish = Column(Date)
    progress_percent = Column(SmallInteger, nullable=False, default=0)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    __table_args__ = (
        CheckConstraint("status IN ('queued','active','paused','completed','removed')", name="reading_queue_items_status_check"),
        CheckConstraint("priority BETWEEN 1 AND 5", name="reading_queue_items_priority_check"),
        CheckConstraint("progress_percent BETWEEN 0 AND 100", name="reading_queue_items_progress_percent_check"),
        CheckConstraint("recommendation_id IS NOT NULL OR document_id IS NOT NULL OR skill_id IS NOT NULL", name="ck_reading_queue_has_target"),
        CheckConstraint("planned_start IS NULL OR target_finish IS NULL OR target_finish >= planned_start", name="ck_reading_queue_date_order"),
        Index("ix_reading_queue_profile_status", "profile_id", "status", "priority"),
    )