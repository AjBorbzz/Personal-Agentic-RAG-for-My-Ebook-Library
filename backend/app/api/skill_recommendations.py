"""Phase 13F routes; leave Phase 13E and default RAG routers unchanged."""
from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.skill_recommendation import (
    AgentSeedRead, GenerateRecommendationsRequest, RecommendationDecisionPatch,
    RecommendationRunDetail, ReadingQueueCreate, ReadingQueuePatch, ReadingQueueRead,
    SkillRecommendationRead,
)
from app.services.skill_recommendation import (
    agent_seed, create_queue_item, current_recommendations,
    decide_recommendation, generate_recommendations, get_queue_item,
    get_run_detail, list_queue_items, update_queue_item,
)

router = APIRouter(tags=["skill-recommendations"])


def _user_error(exc: ValueError) -> HTTPException:
    detail = str(exc)
    if detail.endswith("not found.") or detail in {
        "Active personal profile not found.",
    }:
        return HTTPException(status_code=404, detail=detail)
    if detail.startswith(("Invalid decision transition:", "Invalid queue transition:")):
        return HTTPException(status_code=409, detail=detail)
    return HTTPException(status_code=422, detail=detail)


@router.post("/skill-recommendations/generate", response_model=RecommendationRunDetail,
             status_code=status.HTTP_201_CREATED)
def generate(body: GenerateRecommendationsRequest, db: Session = Depends(get_db)):
    try:
        run_id = generate_recommendations(db, body)
        run, items = get_run_detail(db, run_id)
        return {"run": run, "items": items}
    except ValueError as exc:
        raise _user_error(exc) from exc


@router.get("/skill-recommendations/runs/{run_id}", response_model=RecommendationRunDetail)
def get_run(run_id: UUID, db: Session = Depends(get_db)):
    try:
        run, items = get_run_detail(db, run_id)
        return {"run": run, "items": items}
    except ValueError as exc:
        raise _user_error(exc) from exc


@router.get("/personal-skill-profiles/{profile_id}/recommendations",
            response_model=list[SkillRecommendationRead])
def list_current(profile_id: UUID, career_target_id: UUID | None = None,
                 decision_status: Literal["new", "accepted", "deferred", "dismissed", "completed"] | None = None,
                 limit: int = Query(default=100, ge=1, le=250),
                 db: Session = Depends(get_db)):
    try:
        return current_recommendations(db, profile_id, career_target_id, decision_status, limit)
    except ValueError as exc:
        raise _user_error(exc) from exc


@router.patch("/skill-recommendations/{recommendation_id}",
              response_model=SkillRecommendationRead)
def decide(recommendation_id: UUID, body: RecommendationDecisionPatch,
           db: Session = Depends(get_db)):
    try:
        return decide_recommendation(db, recommendation_id, body)
    except ValueError as exc:
        raise _user_error(exc) from exc


@router.post("/reading-queue", response_model=ReadingQueueRead,
             status_code=status.HTTP_201_CREATED)
def enqueue(body: ReadingQueueCreate, db: Session = Depends(get_db)):
    try:
        return create_queue_item(db, body)
    except ValueError as exc:
        raise _user_error(exc) from exc


@router.get("/reading-queue", response_model=list[ReadingQueueRead])
def queue_for_profile(profile_id: UUID, limit: int = Query(default=100, ge=1, le=250),
                      db: Session = Depends(get_db)):
    try:
        return list_queue_items(db, profile_id, limit)
    except ValueError as exc:
        raise _user_error(exc) from exc


@router.get("/reading-queue/{item_id}", response_model=ReadingQueueRead)
def queue_detail(item_id: UUID, db: Session = Depends(get_db)):
    try:
        return get_queue_item(db, item_id)
    except ValueError as exc:
        raise _user_error(exc) from exc


@router.patch("/reading-queue/{item_id}", response_model=ReadingQueueRead)
def queue_update(item_id: UUID, body: ReadingQueuePatch, db: Session = Depends(get_db)):
    try:
        return update_queue_item(db, item_id, body)
    except ValueError as exc:
        raise _user_error(exc) from exc


@router.post("/skill-recommendations/{recommendation_id}/project-seed",
             response_model=AgentSeedRead)
def project_seed(recommendation_id: UUID, db: Session = Depends(get_db)):
    try:
        return agent_seed(db, recommendation_id, "project")
    except ValueError as exc:
        raise _user_error(exc) from exc


@router.post("/skill-recommendations/{recommendation_id}/learning-path-seed",
             response_model=AgentSeedRead)
def learning_path_seed(recommendation_id: UUID, db: Session = Depends(get_db)):
    try:
        return agent_seed(db, recommendation_id, "learning_path")
    except ValueError as exc:
        raise _user_error(exc) from exc