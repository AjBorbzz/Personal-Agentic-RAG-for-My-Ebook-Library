from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.personal_skill_profile import (
    LearningStatus,
    PersonalSkillEvidenceBase,
    PersonalSkillEvidenceRead,
    PersonalSkillEvidenceUpdate,
    PersonalSkillProfileCreate,
    PersonalSkillProfileRead,
    PersonalSkillProfileUpdate,
    PersonalSkillStateBase,
    PersonalSkillStateRead,
)

from app.services.personal_skill_profile import (
    add_skill_evidence,
    create_profile,
    delete_skill_evidence,
    get_profile,
    list_profiles,
    list_skill_states,
    update_profile,
    update_skill_evidence,
    upsert_skill_state,
)


router = APIRouter(
    prefix="/personal-skill-profiles",
    tags=["personal-skill-profiles"],
)

evidence_router = APIRouter(
    prefix="/personal-skill-evidence",
    tags=["personal-skill-evidence"],
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


# ============================================================
# Personal skill profiles
# ============================================================


@router.post(
    "",
    response_model=PersonalSkillProfileRead,
    status_code=status.HTTP_201_CREATED,
)
def create_personal_skill_profile(
    payload: PersonalSkillProfileCreate,
    db: Session = Depends(get_db),
) -> PersonalSkillProfileRead:
    try:
        profile = create_profile(
            db=db,
            data=payload,
        )
    except ValueError as exc:
        _raise_service_error(exc)

    return PersonalSkillProfileRead.model_validate(
        profile
    )


@router.get(
    "",
    response_model=list[PersonalSkillProfileRead],
)
def list_personal_skill_profiles(
    include_archived: bool = Query(
        default=False,
    ),
    db: Session = Depends(get_db),
) -> list[PersonalSkillProfileRead]:
    try:
        profiles = list_profiles(
            db=db,
            include_archived=include_archived,
        )
    except ValueError as exc:
        _raise_service_error(exc)

    return [
        PersonalSkillProfileRead.model_validate(
            profile
        )
        for profile in profiles
    ]


@router.get(
    "/{profile_id}",
    response_model=PersonalSkillProfileRead,
)
def get_personal_skill_profile(
    profile_id: UUID,
    db: Session = Depends(get_db),
) -> PersonalSkillProfileRead:
    try:
        profile = get_profile(
            db=db,
            profile_id=profile_id,
        )
    except ValueError as exc:
        _raise_service_error(exc)

    return PersonalSkillProfileRead.model_validate(
        profile
    )


@router.patch(
    "/{profile_id}",
    response_model=PersonalSkillProfileRead,
)
def patch_personal_skill_profile(
    profile_id: UUID,
    payload: PersonalSkillProfileUpdate,
    db: Session = Depends(get_db),
) -> PersonalSkillProfileRead:
    try:
        profile = update_profile(
            db=db,
            profile_id=profile_id,
            data=payload,
        )
    except ValueError as exc:
        _raise_service_error(exc)

    return PersonalSkillProfileRead.model_validate(
        profile
    )


# ============================================================
# Personal skill state
# ============================================================


@router.put(
    "/{profile_id}/skills/{skill_id}",
    response_model=PersonalSkillStateRead,
)
def put_personal_skill_state(
    profile_id: UUID,
    skill_id: str,
    payload: PersonalSkillStateBase,
    db: Session = Depends(get_db),
) -> PersonalSkillStateRead:
    try:
        skill_state = upsert_skill_state(
            db=db,
            profile_id=profile_id,
            skill_id=skill_id,
            data=payload,
        )
    except ValueError as exc:
        _raise_service_error(exc)

    return PersonalSkillStateRead.model_validate(
        skill_state
    )


@router.get(
    "/{profile_id}/skills",
    response_model=list[PersonalSkillStateRead],
)
def list_personal_skill_states(
    profile_id: UUID,
    domain_id: str | None = Query(
        default=None,
    ),
    category_id: str | None = Query(
        default=None,
    ),
    learning_status: LearningStatus | None = Query(
        default=None,
    ),
    db: Session = Depends(get_db),
) -> list[PersonalSkillStateRead]:
    try:
        skill_states = list_skill_states(
            db=db,
            profile_id=profile_id,
            domain_id=domain_id,
            category_id=category_id,
            learning_status=learning_status,
        )
    except ValueError as exc:
        _raise_service_error(exc)

    return [
        PersonalSkillStateRead.model_validate(
            state
        )
        for state in skill_states
    ]

# ============================================================
# Personal skill evidence
# ============================================================


@router.post(
    "/{profile_id}/skills/{skill_id}/evidence",
    response_model=PersonalSkillEvidenceRead,
    status_code=status.HTTP_201_CREATED,
)
def create_personal_skill_evidence(
    profile_id: UUID,
    skill_id: str,
    payload: PersonalSkillEvidenceBase,
    db: Session = Depends(get_db),
) -> PersonalSkillEvidenceRead:
    try:
        evidence = add_skill_evidence(
            db=db,
            profile_id=profile_id,
            skill_id=skill_id,
            data=payload,
        )
    except ValueError as exc:
        _raise_service_error(exc)

    return PersonalSkillEvidenceRead.model_validate(
        evidence
    )


@evidence_router.patch(
    "/{evidence_id}",
    response_model=PersonalSkillEvidenceRead,
)
def patch_personal_skill_evidence(
    evidence_id: UUID,
    payload: PersonalSkillEvidenceUpdate,
    db: Session = Depends(get_db),
) -> PersonalSkillEvidenceRead:
    try:
        evidence = update_skill_evidence(
            db=db,
            evidence_id=evidence_id,
            data=payload,
        )
    except ValueError as exc:
        _raise_service_error(exc)

    return PersonalSkillEvidenceRead.model_validate(
        evidence
    )


@evidence_router.delete(
    "/{evidence_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_personal_skill_evidence(
    evidence_id: UUID,
    db: Session = Depends(get_db),
) -> Response:
    try:
        delete_skill_evidence(
            db=db,
            evidence_id=evidence_id,
        )
    except ValueError as exc:
        _raise_service_error(exc)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )