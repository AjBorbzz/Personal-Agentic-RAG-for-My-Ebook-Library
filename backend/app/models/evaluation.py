from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from app.db.base import Base


def now_utc():
    return datetime.now(timezone.utc)


class EvaluationCase(Base):
    __tablename__ = "evaluation_cases"
    __table_args__ = (
        UniqueConstraint("dataset_name", "dataset_version", "case_id", name="uq_evaluation_case_version"),
        Index("ix_evaluation_case_dataset", "dataset_name", "dataset_version", "is_active"),
    )
    evaluation_case_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    case_id = Column(String(160), nullable=False)
    dataset_name = Column(String(120), nullable=False)
    dataset_version = Column(String(80), nullable=False)
    question = Column(Text, nullable=False)
    expected_intent = Column(String(120))
    expected_domains = Column(JSONB, default=list, nullable=False)
    expected_document_ids = Column(JSONB, default=list, nullable=False)
    expected_page_ranges = Column(JSONB, default=list, nullable=False)
    expected_concepts = Column(JSONB, default=list, nullable=False)
    forbidden_document_ids = Column(JSONB, default=list, nullable=False)
    request_filters = Column(JSONB, default=dict, nullable=False)
    expected_refusal = Column(Boolean, default=False, nullable=False)
    tags = Column(JSONB, default=list, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    __table_args__ = (
        CheckConstraint("status IN ('queued','running','completed','failed','cancelled')", name="ck_eval_run_status"),
        Index("ix_eval_runs_dataset_started", "dataset_name", "dataset_version", "started_at"),
    )
    evaluation_run_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    dataset_name = Column(String(120), nullable=False)
    dataset_version = Column(String(80), nullable=False)
    system_config = Column(JSONB, default=dict, nullable=False)
    status = Column(String(32), nullable=False, default="queued")
    started_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    completed_at = Column(DateTime(timezone=True))
    summary_metrics = Column(JSONB, default=dict, nullable=False)
    baseline_run_id = Column(UUID(as_uuid=True), ForeignKey("evaluation_runs.evaluation_run_id", ondelete="SET NULL"))
    error_detail = Column(Text)


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"
    __table_args__ = (
        UniqueConstraint("evaluation_run_id", "evaluation_case_id", name="uq_evaluation_run_case"),
        CheckConstraint("latency_ms >= 0", name="ck_eval_result_latency"),
        Index("ix_eval_result_run", "evaluation_run_id"),
    )
    evaluation_result_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    evaluation_run_id = Column(UUID(as_uuid=True), ForeignKey("evaluation_runs.evaluation_run_id", ondelete="CASCADE"), nullable=False)
    evaluation_case_id = Column(UUID(as_uuid=True), ForeignKey("evaluation_cases.evaluation_case_id", ondelete="RESTRICT"), nullable=False)
    retrieved_sources = Column(JSONB, default=list, nullable=False)
    answer = Column(Text)
    citations = Column(JSONB, default=list, nullable=False)
    metrics = Column(JSONB, default=dict, nullable=False)
    passed = Column(Boolean, default=False, nullable=False)
    failure_categories = Column(JSONB, default=list, nullable=False)
    human_groundedness = Column(Boolean)
    human_relevance = Column(Boolean)
    human_completeness = Column(Boolean)
    human_notes = Column(Text)
    latency_ms = Column(Integer, nullable=False, default=0)
    error_detail = Column(Text)


class RagRunHistory(Base):
    __tablename__ = "rag_run_history"
    __table_args__ = (
        CheckConstraint("latency_ms >= 0", name="ck_rag_run_latency"),
        Index("ix_rag_run_history_created", "created_at"),
    )
    rag_run_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    request_type = Column(String(100), nullable=False)
    question = Column(Text)
    request_payload = Column(JSONB, default=dict, nullable=False)
    intent = Column(String(120))
    strategy = Column(String(120))
    domains = Column(JSONB, default=list, nullable=False)
    rewritten_queries = Column(JSONB, default=list, nullable=False)
    attempts = Column(JSONB, default=list, nullable=False)
    retrieved_sources = Column(JSONB, default=list, nullable=False)
    answer = Column(Text)
    citations = Column(JSONB, default=list, nullable=False)
    fallback_used = Column(Boolean)
    weak_source = Column(Boolean)
    status_code = Column(Integer)
    latency_ms = Column(Integer, nullable=False, default=0)
    error_detail = Column(Text)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)