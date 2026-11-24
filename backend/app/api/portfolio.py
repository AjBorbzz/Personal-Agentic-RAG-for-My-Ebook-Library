"""Phase 15 additive FastAPI router; no changes to existing agent/RAG routes."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.portfolio import PortfolioProject
from app.schemas.portfolio import (
    OpportunityRead, ProjectCreate, ProjectRead, BlueprintSubmit, BlueprintApprove,
    ProjectStatusPatch, MilestoneCreate, MilestonePatch, MilestoneRead,
    ArtifactCreate, ArtifactReview, ArtifactRead, DraftRequest, ReadinessRead,
)
from app.services import portfolio as svc

router = APIRouter(tags=["portfolio-builder"])


def _error(exc: ValueError):
    detail = str(exc)
    code = 404 if detail.endswith("not found.") else 409 if any(
        phrase in detail for phrase in ("already exists", "Invalid project transition", "cannot update", "cannot receive")
    ) else 422
    return HTTPException(status_code=code, detail=detail)


@router.get("/portfolio-opportunities", response_model=list[OpportunityRead])
def portfolio_opportunities(profile_id: UUID, career_target_id: UUID, db: Session = Depends(get_db)):
    try:
        return svc.opportunities(db, profile_id, career_target_id)
    except ValueError as exc:
        raise _error(exc) from exc


@router.post("/portfolio-projects", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def project_create(body: ProjectCreate, db: Session = Depends(get_db)):
    try:
        return svc.create_project(db, body)
    except ValueError as exc:
        raise _error(exc) from exc


@router.get("/portfolio-projects", response_model=list[ProjectRead])
def project_list(profile_id: UUID, career_target_id: UUID | None = None, db: Session = Depends(get_db)):
    try:
        return svc.projects(db, profile_id, career_target_id)
    except ValueError as exc:
        raise _error(exc) from exc


@router.get("/portfolio-projects/{project_id}", response_model=ProjectRead)
def project_detail(project_id: UUID, db: Session = Depends(get_db)):
    try:
        return svc._get(db, PortfolioProject, project_id, "Project")
    except ValueError as exc:
        raise _error(exc) from exc


@router.post("/portfolio-projects/{project_id}/blueprints", response_model=ProjectRead)
def blueprint_submit(project_id: UUID, body: BlueprintSubmit, db: Session = Depends(get_db)):
    try:
        return svc.add_blueprint(db, project_id, body)
    except ValueError as exc:
        raise _error(exc) from exc


@router.post("/portfolio-projects/{project_id}/blueprints/approve", response_model=ProjectRead)
def blueprint_approve(project_id: UUID, body: BlueprintApprove, db: Session = Depends(get_db)):
    try:
        return svc.approve_blueprint(db, project_id, body)
    except ValueError as exc:
        raise _error(exc) from exc


@router.patch("/portfolio-projects/{project_id}", response_model=ProjectRead)
def project_status(project_id: UUID, body: ProjectStatusPatch, db: Session = Depends(get_db)):
    try:
        return svc.change_project_status(db, project_id, body.status)
    except ValueError as exc:
        raise _error(exc) from exc


@router.get("/portfolio-projects/{project_id}/milestones", response_model=list[MilestoneRead])
def milestone_list(project_id: UUID, db: Session = Depends(get_db)):
    try:
        return svc.list_milestones(db, project_id)
    except ValueError as exc:
        raise _error(exc) from exc


@router.post("/portfolio-projects/{project_id}/milestones", response_model=MilestoneRead,
             status_code=status.HTTP_201_CREATED)
def milestone_create(project_id: UUID, body: MilestoneCreate, db: Session = Depends(get_db)):
    try:
        return svc.add_milestone(db, project_id, body)
    except ValueError as exc:
        raise _error(exc) from exc


@router.patch("/portfolio-milestones/{milestone_id}", response_model=MilestoneRead)
def milestone_patch(milestone_id: UUID, body: MilestonePatch, db: Session = Depends(get_db)):
    try:
        return svc.update_milestone(db, milestone_id, body)
    except ValueError as exc:
        raise _error(exc) from exc


@router.get("/portfolio-projects/{project_id}/artifacts", response_model=list[ArtifactRead])
def artifact_list(project_id: UUID, db: Session = Depends(get_db)):
    try:
        return svc.list_artifacts(db, project_id)
    except ValueError as exc:
        raise _error(exc) from exc


@router.post("/portfolio-projects/{project_id}/artifacts", response_model=ArtifactRead,
             status_code=status.HTTP_201_CREATED)
def artifact_create(project_id: UUID, body: ArtifactCreate, db: Session = Depends(get_db)):
    try:
        return svc.add_artifact(db, project_id, body)
    except ValueError as exc:
        raise _error(exc) from exc


@router.patch("/portfolio-artifacts/{artifact_id}/review", response_model=ArtifactRead)
def artifact_review(artifact_id: UUID, body: ArtifactReview, db: Session = Depends(get_db)):
    try:
        return svc.review_artifact(db, artifact_id, body)
    except ValueError as exc:
        raise _error(exc) from exc


@router.post("/portfolio-projects/{project_id}/drafts", response_model=ArtifactRead)
def create_draft(project_id: UUID, body: DraftRequest, db: Session = Depends(get_db)):
    try:
        return svc.draft_career_artifact(db, project_id, body.kind)
    except ValueError as exc:
        raise _error(exc) from exc


@router.get("/portfolio-projects/{project_id}/readiness", response_model=ReadinessRead)
def publication_readiness(project_id: UUID, db: Session = Depends(get_db)):
    try:
        return svc.readiness(db, project_id)
    except ValueError as exc:
        raise _error(exc) from exc


@router.get("/portfolio-projects/{project_id}/evidence-proposals")
def proposed_skill_evidence(project_id: UUID, db: Session = Depends(get_db)):
    try:
        return svc.evidence_proposals(db, project_id)
    except ValueError as exc:
        raise _error(exc) from exc