"""Phase 14 local-only evaluation and operational history endpoints."""
from __future__ import annotations
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.evaluation.service import as_dict, comparison, execute_run, _update_summary
from app.models.evaluation import EvaluationCase, EvaluationResult, EvaluationRun, RagRunHistory

router = APIRouter(tags=["evaluation"])


class CaseCreate(BaseModel):
    case_id: str = Field(min_length=1, max_length=160)
    dataset_name: str = Field(min_length=1, max_length=120)
    dataset_version: str = Field(min_length=1, max_length=80)
    question: str = Field(min_length=1)
    expected_intent: str | None = None
    expected_domains: list[str] = Field(default_factory=list)
    expected_document_ids: list[str] = Field(default_factory=list)
    expected_page_ranges: list[dict] = Field(default_factory=list)
    expected_concepts: list[str] = Field(default_factory=list)
    forbidden_document_ids: list[str] = Field(default_factory=list)
    request_filters: dict = Field(default_factory=dict)
    expected_refusal: bool = False
    tags: list[str] = Field(default_factory=list)
    is_active: bool = True


class RunRequest(BaseModel):
    dataset_name: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    system_config: dict = Field(default_factory=dict)
    baseline_run_id: UUID | None = None
    top_k: int = Field(default=5, ge=1, le=20)
    max_cases: int = Field(default=20, ge=1, le=50)


class HumanReview(BaseModel):
    grounded: bool
    relevant: bool
    complete: bool
    notes: str = Field(min_length=1, max_length=4000)


@router.post("/evaluation-cases", status_code=201)
def create_case(payload: CaseCreate, db: Session = Depends(get_db)):
    previous = db.scalar(select(EvaluationCase).where(
        EvaluationCase.dataset_name == payload.dataset_name,
        EvaluationCase.dataset_version == payload.dataset_version,
        EvaluationCase.case_id == payload.case_id))
    if previous:
        raise HTTPException(409, "Case ID already exists within dataset version")
    case = EvaluationCase(**payload.model_dump())
    db.add(case)
    db.commit()
    db.refresh(case)
    return jsonable_encoder(as_dict(case))


@router.get("/evaluation-cases")
def list_cases(dataset_name: str | None = None, dataset_version: str | None = None,
               tag: str | None = None, active_only: bool = True,
               db: Session = Depends(get_db)):
    stmt = select(EvaluationCase)
    if dataset_name:
        stmt = stmt.where(EvaluationCase.dataset_name == dataset_name)
    if dataset_version:
        stmt = stmt.where(EvaluationCase.dataset_version == dataset_version)
    if active_only:
        stmt = stmt.where(EvaluationCase.is_active.is_(True))
    cases = db.scalars(stmt.order_by(EvaluationCase.case_id).limit(200)).all()
    return jsonable_encoder([as_dict(c) for c in cases if not tag or tag in (c.tags or [])])


@router.post("/evaluation-runs", status_code=201)
def start_run(payload: RunRequest, db: Session = Depends(get_db)):
    try:
        run = execute_run(db, dataset_name=payload.dataset_name,
                          dataset_version=payload.dataset_version,
                          system_config=payload.system_config,
                          baseline_run_id=payload.baseline_run_id,
                          k=payload.top_k, max_cases=payload.max_cases)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return jsonable_encoder({**as_dict(run), "comparison": comparison(db, run)})


@router.get("/evaluation-runs")
def list_runs(limit: int = Query(default=20, ge=1, le=100), db: Session = Depends(get_db)):
    rows = db.scalars(select(EvaluationRun)
                      .order_by(EvaluationRun.started_at.desc()).limit(limit)).all()
    return jsonable_encoder([{**as_dict(r), "comparison": comparison(db, r)} for r in rows])


@router.get("/evaluation-runs/{run_id}")
def get_run(run_id: UUID, db: Session = Depends(get_db)):
    r = db.get(EvaluationRun, run_id)
    if r is None:
        raise HTTPException(404, "Evaluation run not found")
    return jsonable_encoder({**as_dict(r), "comparison": comparison(db, r)})


@router.get("/evaluation-runs/{run_id}/results")
def get_results(run_id: UUID, db: Session = Depends(get_db)):
    if db.get(EvaluationRun, run_id) is None:
        raise HTTPException(404, "Evaluation run not found")
    rows = db.scalars(select(EvaluationResult).where(
        EvaluationResult.evaluation_run_id == run_id)
        .order_by(EvaluationResult.evaluation_case_id)).all()
    return jsonable_encoder([as_dict(x) for x in rows])


@router.patch("/evaluation-results/{result_id}/review")
def review_result(result_id: UUID, payload: HumanReview, db: Session = Depends(get_db)):
    result = db.get(EvaluationResult, result_id)
    if result is None:
        raise HTTPException(404, "Evaluation result not found")
    result.human_groundedness = payload.grounded
    result.human_relevance = payload.relevant
    result.human_completeness = payload.complete
    result.human_notes = payload.notes
    result.passed = (not result.failure_categories and not result.error_detail
                     and payload.grounded and payload.relevant and payload.complete)
    db.commit()
    run = db.get(EvaluationRun, result.evaluation_run_id)
    _update_summary(db, run)
    db.refresh(result)
    return jsonable_encoder(as_dict(result))


@router.get("/rag-runs")
def list_rag_runs(limit: int = Query(default=30, ge=1, le=100),
                  request_type: str | None = None, errors_only: bool = False,
                  db: Session = Depends(get_db)):
    stmt = select(RagRunHistory)
    if request_type:
        stmt = stmt.where(RagRunHistory.request_type == request_type)
    if errors_only:
        stmt = stmt.where(RagRunHistory.error_detail.is_not(None))
    rows = db.scalars(stmt.order_by(RagRunHistory.created_at.desc()).limit(limit)).all()
    return jsonable_encoder([as_dict(x) for x in rows])


@router.get("/evaluation-dashboard")
def evaluation_dashboard(db: Session = Depends(get_db)):
    runs = db.scalars(select(EvaluationRun)
                      .order_by(EvaluationRun.started_at.desc()).limit(15)).all()
    recent = db.scalars(select(RagRunHistory)
                        .order_by(RagRunHistory.created_at.desc()).limit(100)).all()
    known_fallback = [x.fallback_used for x in recent if x.fallback_used is not None]
    known_weak = [x.weak_source for x in recent if x.weak_source is not None]
    fallback_rate = round(sum(known_fallback) / len(known_fallback), 4) if known_fallback else None
    weak_rate = round(sum(known_weak) / len(known_weak), 4) if known_weak else None
    return jsonable_encoder({
        "recent_evaluation_runs": [
            {"evaluation_run_id": r.evaluation_run_id, "status": r.status,
             "dataset_name": r.dataset_name, "dataset_version": r.dataset_version,
             "summary_metrics": r.summary_metrics, "comparison": comparison(db, r)}
            for r in runs
        ],
        "operational_sample_size": len(recent),
        "fallback_rate_recent": fallback_rate,
        "weak_source_rate_recent": weak_rate,
        "recent_errors": sum(bool(x.error_detail) or (x.status_code or 200) >= 400 for x in recent),
        "avg_latency_ms_recent": round(sum(x.latency_ms for x in recent) / len(recent), 1) if recent else None,
    })