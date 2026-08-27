from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.personal_skill_profile import (
    CareerTargetCreate,
    CareerTargetRead,
    CareerTargetSkillRead,
    CareerTargetSkillSet,
)
from app.services.personal_skill_profile import (
    create_career_target,
    set_career_target_skill,
)


router = APIRouter(
    prefix="/career-targets",
    tags=["career-targets"],
)


def _raise_service_error(
    exc: ValueError,
) -> None:
    message = str(exc)

    status_code = (
        status.HTTP_404_NOT_FOUND
        if "not found" in message.casefold()
        else status.HTTP_400_BAD_REQUEST
    )

    raise HTTPException(
        status_code=status_code,
        detail=message,
    ) from exc


@router.post(
    "",
    response_model=CareerTargetRead,
    status_code=status.HTTP_201_CREATED,
)
def create_target(
    payload: CareerTargetCreate,
    db: Session = Depends(get_db),
) -> CareerTargetRead:
    try:
        target = create_career_target(
            db=db,
            data=payload,
        )
    except ValueError as exc:
        _raise_service_error(exc)

    return CareerTargetRead.model_validate(
        target
    )


@router.put(
    "/{target_id}/skills/{skill_id}",
    response_model=CareerTargetSkillRead,
)
def put_target_skill(
    target_id: UUID,
    skill_id: str,
    payload: CareerTargetSkillSet,
    db: Session = Depends(get_db),
) -> CareerTargetSkillRead:
    try:
        requirement = (
            set_career_target_skill(
                db=db,
                career_target_id=target_id,
                skill_id=skill_id,
                data=payload,
            )
        )
    except ValueError as exc:
        _raise_service_error(exc)

    return (
        CareerTargetSkillRead.model_validate(
            requirement
        )
    )