from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.skill_gap import SkillGapResponse
from app.services.skill_gap_analysis import analyze_skill_gaps


router = APIRouter(tags=["skill-gaps"])


@router.get(
    "/personal-skill-profiles/{profile_id}/gaps",
    response_model=SkillGapResponse,
)
def get_skill_gaps(
    profile_id: UUID,
    career_target_id: UUID | None = Query(default=None),
    domain_slug: str | None = Query(default=None, min_length=1),
    db: Session = Depends(get_db),
) -> SkillGapResponse:
    """Return computed gaps without updating any profile or mapping state."""
    try:
        return analyze_skill_gaps(
            db=db,
            profile_id=profile_id,
            career_target_id=career_target_id,
            domain_slug=domain_slug,
        )
    except ValueError as exc:
        # Translate the known Part 2 service errors without modifying them.
        detail = str(exc)

        if detail in {
            "An active personal skill profile was not found.",
            "Career target not found for this personal profile.",
            "The requested canonical skill domain was not found.",
        }:
            raise HTTPException(status_code=404, detail=detail) from exc

        if detail == "domain_slug must not be empty.":
            raise HTTPException(status_code=422, detail=detail) from exc

        if detail.startswith((
            "Unknown canonical proficiency level:",
            "Missing canonical skill references:",
            "Missing prerequisite taxonomy skill references:",
            "Prerequisite cycle reaches skill",
        )):
            # Inconsistent canonical references are not client input errors.
            raise HTTPException(status_code=409, detail=detail) from exc

        # Do not disguise an unclassified validation error as a successful gap.
        raise HTTPException(status_code=400, detail=detail) from exc