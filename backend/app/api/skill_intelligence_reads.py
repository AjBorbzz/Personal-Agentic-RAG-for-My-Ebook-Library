"""Phase 13G UI read-only adapters over the existing canonical 13E/13C tables."""
from __future__ import annotations

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.personal_skill_profile import (
    PersonalSkillProfile, PersonalSkillState, PersonalSkillEvidence,
    CareerTarget, CareerTargetSkill,
)
from app.models.skill_taxonomy import ProficiencyLevel

router = APIRouter(tags=["skill-intelligence-reads"])


def _present(row, *fields):
    """Allow only intended columns; stringify UUID/decimal/datetime via FastAPI encoder."""
    return {name: getattr(row, name) for name in fields}


@router.get("/skill-intelligence/proficiency-levels")
def proficiency_levels(db: Session = Depends(get_db)):
    levels = db.scalars(
        select(ProficiencyLevel).order_by(ProficiencyLevel.level_order)
    ).all()
    return [_present(r, "level_id", "code", "name", "level_order") for r in levels]


@router.get("/career-targets")
def career_targets(profile_id: UUID, db: Session = Depends(get_db)):
    profile = db.get(PersonalSkillProfile, profile_id)
    if profile is None:
        raise HTTPException(404, "Personal profile not found.")
    rows = db.scalars(
        select(CareerTarget)
        .where(CareerTarget.profile_id == profile_id)
        .order_by(CareerTarget.created_at.desc(), CareerTarget.career_target_id)
    ).all()
    return [_present(r, "career_target_id", "profile_id", "role_name",
                     "role_slug", "description", "priority", "status",
                     "target_date", "created_at", "updated_at") for r in rows]


@router.get("/career-targets/{target_id}")
def career_target_detail(target_id: UUID, profile_id: UUID,
                         db: Session = Depends(get_db)):
    r = db.get(CareerTarget, target_id)
    if r is None or r.profile_id != profile_id:
        raise HTTPException(404, "Career target not found for profile.")
    return _present(r, "career_target_id", "profile_id", "role_name",
                    "role_slug", "description", "priority", "status",
                    "target_date", "created_at", "updated_at")


@router.get("/career-targets/{target_id}/skills")
def career_target_skills(target_id: UUID, profile_id: UUID,
                         db: Session = Depends(get_db)):
    target = db.get(CareerTarget, target_id)
    if target is None or target.profile_id != profile_id:
        raise HTTPException(404, "Career target not found for profile.")
    rows = db.scalars(
        select(CareerTargetSkill)
        .where(CareerTargetSkill.career_target_id == target_id)
        .order_by(CareerTargetSkill.skill_id)
    ).all()
    return [_present(r, "career_target_skill_id", "career_target_id", "skill_id",
                     "required_level_id", "importance_weight", "is_required",
                     "rationale") for r in rows]


@router.get("/personal-skill-profiles/{profile_id}/skills/{skill_id}/evidence")
def skill_evidence(profile_id: UUID, skill_id: str, db: Session = Depends(get_db)):
    state = db.scalar(
        select(PersonalSkillState).where(
            PersonalSkillState.profile_id == profile_id,
            PersonalSkillState.skill_id == skill_id,
        )
    )
    if state is None:
        return []
    rows = db.scalars(
        select(PersonalSkillEvidence)
        .where(PersonalSkillEvidence.profile_skill_id == state.profile_skill_id)
        .order_by(PersonalSkillEvidence.created_at.desc())
    ).all()
    return [_present(r, "evidence_id", "profile_skill_id", "evidence_type",
                     "title", "description", "verification_status", "source_url",
                     "source_document_id", "created_at", "updated_at") for r in rows]