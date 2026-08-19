from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.schemas.personal_skill_profile import (
    PersonalSkillEvidenceBase,
    PersonalSkillEvidenceUpdate,
    PersonalSkillProfileCreate,
    PersonalSkillProfileUpdate,
    PersonalSkillStateBase,
)

from app.models.personal_skill_profile import (
    PersonalSkillEvidence,
    PersonalSkillProfile,
    PersonalSkillState,
)

from app.models.document import Document
from app.models.skill_taxonomy import (
    ProficiencyLevel,
    Skill,
)
from app.schemas.personal_skill_profile import (
    PersonalSkillProfileCreate,
    PersonalSkillProfileUpdate,
    PersonalSkillStateBase,
)


# ============================================================
# Internal lookup helpers
# ============================================================


def _get_profile(
    db: Session,
    profile_id: UUID,
) -> PersonalSkillProfile:
    profile = db.get(
        PersonalSkillProfile,
        profile_id,
    )

    if profile is None:
        raise ValueError(
            "Personal skill profile was not found."
        )

    return profile


def _get_active_profile(
    db: Session,
    profile_id: UUID,
) -> PersonalSkillProfile:
    profile = _get_profile(
        db,
        profile_id,
    )

    if not profile.is_active:
        raise ValueError(
            "Personal skill profile is archived."
        )

    return profile


def _get_canonical_skill(
    db: Session,
    skill_id: str,
) -> Skill:
    skill = db.get(
        Skill,
        skill_id,
    )

    if skill is None:
        raise ValueError(
            "Canonical skill was not found."
        )

    return skill


def _get_assignable_skill(
    db: Session,
    skill_id: str,
) -> Skill:
    skill = _get_canonical_skill(
        db,
        skill_id,
    )

    if not skill.is_active:
        raise ValueError(
            "Cannot assign an inactive canonical skill."
        )

    if skill.is_deprecated:
        raise ValueError(
            "Cannot assign a deprecated canonical skill."
        )

    return skill


def _get_proficiency_level(
    db: Session,
    level_id: str,
) -> ProficiencyLevel:
    level = db.get(
        ProficiencyLevel,
        level_id,
    )

    if level is None:
        raise ValueError(
            "Canonical proficiency level was not found: "
            f"'{level_id}'."
        )

    return level


def _default_profile_exists(
    db: Session,
) -> bool:
    profile_id = db.scalar(
        select(
            PersonalSkillProfile.profile_id
        )
        .where(
            PersonalSkillProfile.is_default.is_(
                True
            )
        )
        .limit(1)
    )

    return profile_id is not None


def _clear_other_defaults(
    *,
    db: Session,
    except_profile_id: UUID | None = None,
) -> None:
    statement = (
        update(PersonalSkillProfile)
        .where(
            PersonalSkillProfile.is_default.is_(
                True
            )
        )
    )

    if except_profile_id is not None:
        statement = statement.where(
            PersonalSkillProfile.profile_id
            != except_profile_id
        )

    db.execute(
        statement.values(
            is_default=False,
        )
    )


# ============================================================
# Profile CRUD
# ============================================================


def create_profile(
    *,
    db: Session,
    data: PersonalSkillProfileCreate,
) -> PersonalSkillProfile:
    """
    Create a personal skill profile.

    The first profile becomes the default automatically.

    If a later profile is explicitly created as the default,
    the previous default is cleared in the same transaction.
    """

    is_default = data.is_default

    existing_default = _default_profile_exists(
        db,
    )

    if not existing_default:
        # Phase 13E requires one default profile.
        is_default = True

    if is_default and not data.is_active:
        raise ValueError(
            "The default personal skill profile "
            "must be active."
        )

    try:
        if is_default and existing_default:
            _clear_other_defaults(
                db=db,
            )

        profile = PersonalSkillProfile(
            profile_name=data.profile_name,
            description=data.description,
            is_default=is_default,
            is_active=data.is_active,
        )

        db.add(profile)

        db.commit()
        db.refresh(profile)

        return profile

    except IntegrityError as exc:
        db.rollback()

        raise ValueError(
            "Personal skill profile violates "
            "a database constraint."
        ) from exc

    except Exception:
        db.rollback()
        raise


def list_profiles(
    *,
    db: Session,
    include_archived: bool = False,
) -> list[PersonalSkillProfile]:
    """
    List profiles.

    Active profiles are returned by default.
    Archived profiles are included only when explicitly
    requested.
    """

    statement = select(
        PersonalSkillProfile
    )

    if not include_archived:
        statement = statement.where(
            PersonalSkillProfile.is_active.is_(
                True
            )
        )

    statement = statement.order_by(
        PersonalSkillProfile.is_default.desc(),
        PersonalSkillProfile.created_at.asc(),
    )

    return list(
        db.scalars(
            statement
        ).all()
    )


def get_profile(
    *,
    db: Session,
    profile_id: UUID,
) -> PersonalSkillProfile:
    """
    Return one profile, including an archived profile.

    Archival prevents mutation but does not destroy
    historical visibility.
    """

    return _get_profile(
        db,
        profile_id,
    )


def update_profile(
    *,
    db: Session,
    profile_id: UUID,
    data: PersonalSkillProfileUpdate,
) -> PersonalSkillProfile:
    """
    Patch an existing personal skill profile.

    Exactly one profile remains the default.

    To move the default:
        PATCH another profile with is_default=true.

    The service clears the former default transactionally.
    """

    profile = _get_profile(
        db,
        profile_id,
    )

    changes = data.model_dump(
        exclude_unset=True,
    )

    if not changes:
        return profile

    if (
        "profile_name" in changes
        and changes["profile_name"] is None
    ):
        raise ValueError(
            "profile_name cannot be null."
        )

    if (
        "is_default" in changes
        and changes["is_default"] is None
    ):
        raise ValueError(
            "is_default cannot be null."
        )

    if (
        "is_active" in changes
        and changes["is_active"] is None
    ):
        raise ValueError(
            "is_active cannot be null."
        )

    requested_default = changes.get(
        "is_default",
        profile.is_default,
    )

    requested_active = changes.get(
        "is_active",
        profile.is_active,
    )

    if (
        profile.is_default
        and changes.get("is_default") is False
    ):
        raise ValueError(
            "The current default profile cannot "
            "be unset directly. Set another profile "
            "as the default instead."
        )

    if (
        profile.is_default
        and changes.get("is_active") is False
    ):
        raise ValueError(
            "The current default profile cannot "
            "be archived. Set another profile as "
            "the default first."
        )

    if requested_default and not requested_active:
        raise ValueError(
            "The default personal skill profile "
            "must be active."
        )

    try:
        if changes.get("is_default") is True:
            _clear_other_defaults(
                db=db,
                except_profile_id=profile.profile_id,
            )

        for field_name, value in changes.items():
            setattr(
                profile,
                field_name,
                value,
            )

        db.commit()
        db.refresh(profile)

        return profile

    except IntegrityError as exc:
        db.rollback()

        raise ValueError(
            "Personal skill profile update "
            "violates a database constraint."
        ) from exc

    except Exception:
        db.rollback()
        raise


# ============================================================
# Personal skill state
# ============================================================


def upsert_skill_state(
    *,
    db: Session,
    profile_id: UUID,
    skill_id: str,
    data: PersonalSkillStateBase,
) -> PersonalSkillState:
    """
    Create or replace the human-owned state for one
    canonical skill.

    PUT semantics are intentional:
    fields omitted by the request schema use that schema's
    defined defaults.

    This function never mutates the canonical taxonomy.
    """

    _get_active_profile(
        db,
        profile_id,
    )

    _get_assignable_skill(
        db,
        skill_id,
    )

    if data.current_level_id is not None:
        _get_proficiency_level(
            db,
            data.current_level_id,
        )

    if data.target_level_id is not None:
        _get_proficiency_level(
            db,
            data.target_level_id,
        )

    state = db.scalar(
        select(
            PersonalSkillState
        ).where(
            PersonalSkillState.profile_id
            == profile_id,
            PersonalSkillState.skill_id
            == skill_id,
        )
    )

    values = data.model_dump()

    try:
        if state is None:
            state = PersonalSkillState(
                profile_id=profile_id,
                skill_id=skill_id,
                **values,
            )

            db.add(state)

        else:
            for field_name, value in values.items():
                setattr(
                    state,
                    field_name,
                    value,
                )

        db.commit()
        db.refresh(state)

        return state

    except IntegrityError as exc:
        db.rollback()

        raise ValueError(
            "Personal skill state violates "
            "a database constraint."
        ) from exc

    except Exception:
        db.rollback()
        raise


def list_skill_states(
    *,
    db: Session,
    profile_id: UUID,
    domain_id: str | None = None,
    category_id: str | None = None,
    learning_status: str | None = None,
) -> list[PersonalSkillState]:
    """
    List tracked skill states for one profile.

    Historical rows remain readable even when the
    referenced canonical skill later becomes inactive
    or deprecated.

    Optional filters:
        domain_id
        category_id
        learning_status
    """

    _get_profile(
        db,
        profile_id,
    )

    statement = (
        select(
            PersonalSkillState
        )
        .join(
            Skill,
            Skill.skill_id
            == PersonalSkillState.skill_id,
        )
        .where(
            PersonalSkillState.profile_id
            == profile_id
        )
    )

    if domain_id is not None:
        statement = statement.where(
            Skill.domain_id == domain_id
        )

    if category_id is not None:
        statement = statement.where(
            Skill.category_id == category_id
        )

    if learning_status is not None:
        statement = statement.where(
            PersonalSkillState.learning_status
            == learning_status
        )

    statement = statement.order_by(
        PersonalSkillState.career_priority.desc(),
        Skill.name.asc(),
        PersonalSkillState.created_at.asc(),
    )

    return list(
        db.scalars(
            statement
        ).all()
    )

# ============================================================
# Personal skill evidence
# ============================================================


def _get_skill_state(
    *,
    db: Session,
    profile_id: UUID,
    skill_id: str,
) -> PersonalSkillState:
    state = db.scalar(
        select(
            PersonalSkillState
        ).where(
            PersonalSkillState.profile_id
            == profile_id,
            PersonalSkillState.skill_id
            == skill_id,
        )
    )

    if state is None:
        raise ValueError(
            "Personal skill state was not found."
        )

    return state


def _get_evidence(
    *,
    db: Session,
    evidence_id: UUID,
) -> PersonalSkillEvidence:
    evidence = db.get(
        PersonalSkillEvidence,
        evidence_id,
    )

    if evidence is None:
        raise ValueError(
            "Personal skill evidence was not found."
        )

    return evidence


def _get_evidence_profile(
    *,
    db: Session,
    evidence: PersonalSkillEvidence,
) -> PersonalSkillProfile:
    state = db.get(
        PersonalSkillState,
        evidence.profile_skill_id,
    )

    if state is None:
        raise ValueError(
            "Personal skill state was not found."
        )

    return _get_profile(
        db,
        state.profile_id,
    )


def _validate_source_document(
    *,
    db: Session,
    document_id: str,
) -> Document:
    document = db.get(
        Document,
        document_id,
    )

    if document is None:
        raise ValueError(
            "Evidence source document was not found."
        )

    return document


def add_skill_evidence(
    *,
    db: Session,
    profile_id: UUID,
    skill_id: str,
    data: PersonalSkillEvidenceBase,
) -> PersonalSkillEvidence:
    """
    Add evidence supporting one existing personal skill state.

    Evidence is deliberately separate from proficiency.
    Creating evidence never changes:
        current_level_id
        target_level_id
        confidence
        career_priority
        learning_status
    """

    _get_active_profile(
        db,
        profile_id,
    )

    state = _get_skill_state(
        db=db,
        profile_id=profile_id,
        skill_id=skill_id,
    )

    if data.source_document_id is not None:
        _validate_source_document(
            db=db,
            document_id=data.source_document_id,
        )

    values = data.model_dump()

    evidence_metadata = values.pop(
        "metadata",
        {},
    )

    try:
        evidence = PersonalSkillEvidence(
            profile_skill_id=(
                state.profile_skill_id
            ),
            evidence_metadata=(
                evidence_metadata
            ),
            **values,
        )

        db.add(evidence)

        db.commit()
        db.refresh(evidence)

        return evidence

    except IntegrityError as exc:
        db.rollback()

        raise ValueError(
            "Personal skill evidence violates "
            "a database constraint."
        ) from exc

    except Exception:
        db.rollback()
        raise


def update_skill_evidence(
    *,
    db: Session,
    evidence_id: UUID,
    data: PersonalSkillEvidenceUpdate,
) -> PersonalSkillEvidence:
    """
    Update or review an evidence record.

    Verification status is human-owned.

    Updating evidence never updates the associated
    personal proficiency state.
    """

    evidence = _get_evidence(
        db=db,
        evidence_id=evidence_id,
    )

    profile = _get_evidence_profile(
        db=db,
        evidence=evidence,
    )

    if not profile.is_active:
        raise ValueError(
            "Personal skill profile is archived."
        )

    changes = data.model_dump(
        exclude_unset=True,
    )

    if not changes:
        return evidence

    if (
        "evidence_type" in changes
        and changes["evidence_type"] is None
    ):
        raise ValueError(
            "evidence_type cannot be null."
        )

    if (
        "title" in changes
        and changes["title"] is None
    ):
        raise ValueError(
            "title cannot be null."
        )

    if (
        "verification_status" in changes
        and changes["verification_status"]
        is None
    ):
        raise ValueError(
            "verification_status cannot be null."
        )

    if (
        "metadata" in changes
        and changes["metadata"] is None
    ):
        raise ValueError(
            "metadata cannot be null."
        )

    if (
        "source_document_id" in changes
        and changes["source_document_id"]
        is not None
    ):
        _validate_source_document(
            db=db,
            document_id=(
                changes[
                    "source_document_id"
                ]
            ),
        )

    if "metadata" in changes:
        changes[
            "evidence_metadata"
        ] = changes.pop(
            "metadata"
        )

    try:
        for field_name, value in changes.items():
            setattr(
                evidence,
                field_name,
                value,
            )

        db.commit()
        db.refresh(evidence)

        return evidence

    except IntegrityError as exc:
        db.rollback()

        raise ValueError(
            "Personal skill evidence update "
            "violates a database constraint."
        ) from exc

    except Exception:
        db.rollback()
        raise


def delete_skill_evidence(
    *,
    db: Session,
    evidence_id: UUID,
) -> None:
    """
    Remove one evidence record.

    The current evidence model has no archive/lifecycle
    column, so Phase 13E.3 uses a direct delete.

    Deleting evidence does not change proficiency.
    """

    evidence = _get_evidence(
        db=db,
        evidence_id=evidence_id,
    )

    profile = _get_evidence_profile(
        db=db,
        evidence=evidence,
    )

    if not profile.is_active:
        raise ValueError(
            "Personal skill profile is archived."
        )

    try:
        db.delete(evidence)
        db.commit()

    except Exception:
        db.rollback()
        raise

