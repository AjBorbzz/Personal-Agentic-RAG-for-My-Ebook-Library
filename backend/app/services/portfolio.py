"""Phase 15 portfolio lifecycle. Human review controls all claim promotion."""
from __future__ import annotations
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.personal_skill_profile import PersonalSkillProfile, CareerTarget
from app.models.book_skill_mapping import BookSkillMapping
from app.models.document import Document
from app.models.portfolio import PortfolioProject, PortfolioMilestone, PortfolioArtifact
from app.services.skill_gap_analysis import analyze_skill_gaps
from app.schemas.portfolio import (
    ProjectCreate, BlueprintSubmit, BlueprintApprove, MilestoneCreate, MilestonePatch,
    ArtifactCreate, ArtifactReview,
)


def _now():
    return datetime.now(timezone.utc)


def _get(db: Session, model, row_id, label: str):
    row = db.get(model, row_id)
    if row is None:
        raise ValueError(f"{label} not found.")
    return row


def _profile_target(db: Session, profile_id: UUID, target_id: UUID):
    profile = _get(db, PersonalSkillProfile, profile_id, "Profile")
    target = _get(db, CareerTarget, target_id, "Career target")
    if not profile.is_active or target.profile_id != profile_id:
        raise ValueError("An active profile and its own career target are required.")
    if target.status != "active":
        raise ValueError("Activate this career target before creating portfolio work.")
    return profile, target


def _approved_sources(db: Session, skill_ids: list[str]):
    if not skill_ids:
        return {}
    rows = db.execute(
        select(BookSkillMapping.skill_id, BookSkillMapping.mapping_id, BookSkillMapping.document_id)
        .join(Document, Document.document_id == BookSkillMapping.document_id)
        .where(
            BookSkillMapping.skill_id.in_(skill_ids),
            BookSkillMapping.mapping_status == "approved",
            Document.is_active.is_(True),
            Document.is_deprecated.is_(False),
        )
        .order_by(BookSkillMapping.skill_id, BookSkillMapping.mapping_id)
    ).all()
    by_skill = {}
    for skill_id, mapping_id, document_id in rows:
        by_skill.setdefault(skill_id, []).append((str(mapping_id), str(document_id)))
    return by_skill


def opportunities(db: Session, profile_id: UUID, target_id: UUID):
    _profile_target(db, profile_id, target_id)
    gap_response = analyze_skill_gaps(db, profile_id, target_id)
    actionable = [x for x in gap_response.gaps
                  if x.gap_type not in {"met_target", "exceeds_target", "no_target"}]
    sources = _approved_sources(db, [x.skill_id for x in actionable])
    output = []
    for gap in actionable:
        mapped = sources.get(gap.skill_id, [])
        output.append({
            "skill_id": gap.skill_id,
            "skill_name": gap.skill_name,
            "gap_type": gap.gap_type,
            "gap_steps": gap.gap_steps,
            "career_importance": gap.career_importance,
            "explanation": gap.explanation,
            "title_suggestion": f"Demonstrate {gap.skill_name} in a practical project",
            "source_document_ids": sorted({document_id for _, document_id in mapped}),
            "source_mapping_ids": sorted({mapping_id for mapping_id, _ in mapped}),
            "no_trusted_book_sources": not bool(mapped),
        })
    return output


def create_project(db: Session, body: ProjectCreate):
    _profile_target(db, body.profile_id, body.career_target_id)
    available = {x["skill_id"]: x for x in opportunities(db, body.profile_id, body.career_target_id)}
    unknown = set(body.target_skill_ids) - set(available)
    if unknown:
        raise ValueError(f"Skills must be current actionable gaps for this target: {sorted(unknown)}")
    if db.scalar(select(PortfolioProject.portfolio_project_id).where(
        PortfolioProject.profile_id == body.profile_id,
        PortfolioProject.slug == body.slug,
    )) is not None:
        raise ValueError("Project slug already exists for this profile.")
    ids = sorted({doc_id for sid in body.target_skill_ids for doc_id in available[sid]["source_document_ids"]})
    mappings = sorted({mid for sid in body.target_skill_ids for mid in available[sid]["source_mapping_ids"]})
    project = PortfolioProject(
        profile_id=body.profile_id, career_target_id=body.career_target_id,
        title=body.title.strip(), slug=body.slug, problem_statement=body.problem_statement.strip(),
        status="idea", target_skill_ids=sorted(body.target_skill_ids),
        source_document_ids=ids, source_mapping_ids=mappings,
        blueprint_versions=[], scope={}, architecture={}, tech_stack=[],
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def projects(db: Session, profile_id: UUID, career_target_id: UUID | None = None):
    _get(db, PersonalSkillProfile, profile_id, "Profile")
    query = select(PortfolioProject).where(PortfolioProject.profile_id == profile_id)
    if career_target_id is not None:
        query = query.where(PortfolioProject.career_target_id == career_target_id)
    return list(db.scalars(query.order_by(PortfolioProject.created_at.desc())).all())


def add_blueprint(db: Session, project_id: UUID, body: BlueprintSubmit):
    project = _get(db, PortfolioProject, project_id, "Project")
    if project.status in {"published", "archived"}:
        raise ValueError("Published or archived projects cannot receive new blueprints.")
    spec = body.specification
    required = ("title", "problem_statement", "architecture", "implementation_phases")
    missing = [field for field in required if not spec.get(field)]
    if missing:
        raise ValueError(f"Project Generator specification lacks required sections: {missing}")
    next_version = len(project.blueprint_versions or []) + 1
    history = list(project.blueprint_versions or [])
    history.append({
        "version": next_version, "specification": spec, "review_notes": body.review_notes,
        "approved": False, "created_at": _now().isoformat(),
        "origin": "existing_project_generator_reviewed_submission",
    })
    project.blueprint_versions = history
    db.commit()
    db.refresh(project)
    return project


def approve_blueprint(db: Session, project_id: UUID, body: BlueprintApprove):
    project = _get(db, PortfolioProject, project_id, "Project")
    if project.status in {"completed", "published", "archived"}:
        raise ValueError("Completed/published/archived blueprints cannot be changed.")
    history = list(project.blueprint_versions or [])
    selected = next((x for x in history if x["version"] == body.version), None)
    if selected is None:
        raise ValueError("Blueprint version not found.")
    spec = selected["specification"]
    # Persist approved, human-reviewed snapshot without generating or inferring claims.
    for item in history:
        item["approved"] = item["version"] == body.version
        if item["approved"]:
            item["approval_notes"] = body.review_notes
            item["approved_at"] = _now().isoformat()
    project.blueprint_versions = history
    project.approved_blueprint_version = body.version
    project.scope = spec.get("scope") if isinstance(spec.get("scope"), dict) else {"summary": spec.get("scope", "")}
    project.architecture = spec.get("architecture") if isinstance(spec.get("architecture"), dict) else {"summary": spec.get("architecture", "")}
    stack = spec.get("technology_stack", [])
    project.tech_stack = stack if isinstance(stack, list) else [str(stack)]
    if project.status == "idea":
        project.status = "approved"
    db.commit()
    db.refresh(project)
    return project


_PROJECT_EDGES = {
    "approved": {"planned", "archived"}, "planned": {"in_progress", "blocked", "archived"},
    "in_progress": {"blocked", "completed", "archived"},
    "blocked": {"in_progress", "archived"},
    "completed": {"published", "archived"},
    "published": {"archived"}, "idea": {"archived"}, "archived": set(),
}


def change_project_status(db: Session, project_id: UUID, new_status: str):
    project = _get(db, PortfolioProject, project_id, "Project")
    if new_status == project.status:
        return project
    if new_status not in _PROJECT_EDGES[project.status]:
        raise ValueError(f"Invalid project transition: {project.status} -> {new_status}.")
    if new_status in {"planned", "in_progress", "completed", "published"} and not project.approved_blueprint_version:
        raise ValueError("Approved blueprint required.")
    if new_status == "published" and not readiness(db, project_id)["publication_ready"]:
        raise ValueError("Project is not publication-ready; inspect readiness results.")
    if new_status == "completed":
        milestones = list_milestones(db, project_id)
        if not milestones or any(x.status not in {"completed", "skipped"} for x in milestones):
            raise ValueError("Complete or explicitly skip all milestones before project completion.")
        project.completed_at = _now()
    project.status = new_status
    db.commit()
    db.refresh(project)
    return project


def list_milestones(db: Session, project_id: UUID):
    _get(db, PortfolioProject, project_id, "Project")
    return list(db.scalars(select(PortfolioMilestone)
        .where(PortfolioMilestone.portfolio_project_id == project_id)
        .order_by(PortfolioMilestone.sequence_order)).all())


def add_milestone(db: Session, project_id: UUID, body: MilestoneCreate):
    project = _get(db, PortfolioProject, project_id, "Project")
    if project.approved_blueprint_version is None or project.status in {"completed", "published", "archived"}:
        raise ValueError("An approved, open project blueprint is required.")
    milestone = PortfolioMilestone(portfolio_project_id=project_id, **body.model_dump())
    db.add(milestone)
    db.commit()
    db.refresh(milestone)
    return milestone


def update_milestone(db: Session, milestone_id: UUID, body: MilestonePatch):
    milestone = _get(db, PortfolioMilestone, milestone_id, "Milestone")
    project = _get(db, PortfolioProject, milestone.portfolio_project_id, "Project")
    if project.status in {"completed", "published", "archived"}:
        raise ValueError("Finished projects cannot update milestones.")
    if body.status == "completed" and not (body.completion_notes or "").strip():
        raise ValueError("Completion requires user-authored acceptance notes.")
    if body.status == "active" and milestone.started_at is None:
        milestone.started_at = _now()
    milestone.status = body.status
    milestone.completion_notes = body.completion_notes
    milestone.completed_at = _now() if body.status == "completed" else None
    db.commit()
    db.refresh(milestone)
    return milestone


def list_artifacts(db: Session, project_id: UUID):
    _get(db, PortfolioProject, project_id, "Project")
    return list(db.scalars(select(PortfolioArtifact)
        .where(PortfolioArtifact.portfolio_project_id == project_id)
        .order_by(PortfolioArtifact.created_at.desc())).all())


def add_artifact(db: Session, project_id: UUID, body: ArtifactCreate):
    project = _get(db, PortfolioProject, project_id, "Project")
    if project.status in {"published", "archived"}:
        raise ValueError("Cannot add artifacts to published/archived projects.")
    if body.milestone_id is not None:
        milestone = _get(db, PortfolioMilestone, body.milestone_id, "Milestone")
        if milestone.portfolio_project_id != project_id:
            raise ValueError("Artifact milestone belongs to a different project.")
    artifact = PortfolioArtifact(
        portfolio_project_id=project_id, **body.model_dump(),
        claim_scope="planned", verification_status="draft", evidence={}, revision_history=[], version=1,
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return artifact


def _validate_claim(body: ArtifactReview):
    scope, status, evidence = body.claim_scope, body.verification_status, body.evidence
    if scope == "planned":
        return
    if status == "draft" or not body.review_notes.strip():
        raise ValueError("Promotion needs explicit human review and evidence.")
    required = {
        "implemented": ("repository_ref",),
        "tested": ("repository_ref", "command", "result"),
        "measured": ("repository_ref", "baseline", "method", "measurement"),
        "published": ("repository_ref", "publication_url"),
    }[scope]
    missing = [name for name in required if not str(evidence.get(name, "")).strip()]
    if missing:
        raise ValueError(f"Cannot claim {scope}; missing evidence: {missing}.")
    if scope in {"tested", "measured"} and status not in {"verified", "published"}:
        raise ValueError("Tested/measured claims require human-verified evidence.")
    if scope == "published" and (status != "published" or not (body.source_url or "").strip()):
        raise ValueError("Published claims need a reviewed, reachable publication URL.")


def review_artifact(db: Session, artifact_id: UUID, body: ArtifactReview):
    artifact = _get(db, PortfolioArtifact, artifact_id, "Artifact")
    project = _get(db, PortfolioProject, artifact.portfolio_project_id, "Project")
    if project.status == "archived":
        raise ValueError("Archived projects cannot change artifacts.")
    _validate_claim(body)
    history = list(artifact.revision_history or [])
    history.append({
        "version": artifact.version, "claim_scope": artifact.claim_scope,
        "verification_status": artifact.verification_status, "evidence": artifact.evidence,
        "content": artifact.content, "file_path": artifact.file_path,
        "source_url": artifact.source_url, "saved_at": _now().isoformat(),
    })
    artifact.revision_history = history
    artifact.version += 1
    artifact.claim_scope = body.claim_scope
    artifact.verification_status = body.verification_status
    artifact.evidence = {**body.evidence, "review_notes": body.review_notes}
    if body.content is not None:
        artifact.content = body.content
    if body.file_path is not None:
        artifact.file_path = body.file_path
    if body.source_url is not None:
        artifact.source_url = body.source_url
    db.commit()
    db.refresh(artifact)
    return artifact


def readiness(db: Session, project_id: UUID):
    project = _get(db, PortfolioProject, project_id, "Project")
    milestones = list_milestones(db, project_id)
    artifacts = list_artifacts(db, project_id)
    verified = [a for a in artifacts if a.verification_status in {"verified", "published"}]
    missing = []
    if not project.approved_blueprint_version:
        missing.append("Human-approved project blueprint")
    if not milestones:
        missing.append("Milestones with acceptance criteria")
    if any(m.status not in {"completed", "skipped"} for m in milestones):
        missing.append("Outstanding milestones")
    if not any(a.artifact_type == "repository" and a.claim_scope in {"implemented", "tested", "measured", "published"} for a in verified):
        missing.append("Verified implementation/repository artifact")
    if not any(a.artifact_type == "test_report" and a.claim_scope in {"tested", "measured", "published"} for a in verified):
        missing.append("Verified test report")
    if project.completed_at is None:
        missing.append("Human-confirmed project completion")
    return {
        "portfolio_project_id": project_id,
        "approved_blueprint": bool(project.approved_blueprint_version),
        "milestone_count": len(milestones),
        "completed_milestones": sum(m.status == "completed" for m in milestones),
        "verified_artifact_count": len(verified),
        "missing": missing,
        "publication_ready": not missing,
    }


def draft_career_artifact(db: Session, project_id: UUID, kind: str):
    project = _get(db, PortfolioProject, project_id, "Project")
    verified = [a for a in list_artifacts(db, project_id)
                if a.verification_status in {"verified", "published"} and a.claim_scope != "planned"]
    # Deliberately no LLM: human-visible evidence is the only source for career claims.
    evidence_lines = [f"- {a.title} [{a.claim_scope}]: {a.file_path or a.source_url or a.evidence.get('repository_ref', 'reviewed evidence')}"
                      for a in verified]
    proof = "\n".join(evidence_lines) if evidence_lines else "- No verified implementation artifacts recorded."
    blocks = {
        "README": f"# {project.title}\n\n## Problem\n{project.problem_statement}\n\n## Evidence\n{proof}\n\n## Run instructions\n[Human author required]\n",
        "architecture": f"# Architecture — {project.title}\n\nApproved architecture snapshot:\n{project.architecture}\n\n## Evidence\n{proof}\n",
        "case_study": f"# Case study — {project.title}\n\n## Challenge\n{project.problem_statement}\n\n## Decisions and tradeoffs\n[Human author required]\n\n## Demonstrated outcomes\n{proof}\n",
        "resume_bullet": f"# Resume evidence — {project.title}\n\nVerified supporting records:\n{proof}\n\n[Human: write a bullet restricted to demonstrated work; no invented metrics.]\n",
        "interview_story": f"# STAR — {project.title}\n\nSituation: {project.problem_statement}\nTask: [Human author]\nAction: [Use verified artifacts below]\nResult: [Only observed, evidenced outcome]\n\n{proof}\n\nTradeoffs / demo: [Human author]\n",
    }
    if kind not in blocks:
        raise ValueError("Unsupported draft kind.")
    return add_artifact(db, project_id, ArtifactCreate(artifact_type=kind, title=f"Draft {kind}: {project.title}", content=blocks[kind]))


def evidence_proposals(db: Session, project_id: UUID):
    project = _get(db, PortfolioProject, project_id, "Project")
    verified = [a for a in list_artifacts(db, project_id)
                if a.verification_status in {"verified", "published"} and a.claim_scope != "planned"]
    # Export review candidates only; NEVER insert or update personal_skill_evidence/state.
    return [
        {"artifact_id": str(a.artifact_id), "profile_id": str(project.profile_id),
         "skill_ids_for_human_review": project.target_skill_ids,
         "source_reference": a.file_path or a.source_url or a.evidence.get("repository_ref"),
         "claim_scope": a.claim_scope, "verification_status": a.verification_status,
         "review_required": True}
        for a in verified
    ]