from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.book_skill_mapping import BookSkillMapping
from app.models.document import Document
from app.models.personal_skill_profile import (
    CareerTarget,
    CareerTargetSkill,
    PersonalSkillProfile,
    PersonalSkillState,
)
from app.models.skill_taxonomy import (
    ProficiencyLevel,
    Skill,
    SkillDomain,
    SkillRelationship,
)
from app.schemas.skill_gap import (
    SkillGapItem,
    SkillGapResponse,
    SkillGapSummary,
)


# The canonical Phase 13C relationship edge points FROM a skill
# TO its required prerequisite. Do not reverse it.
PREREQUISITE_RELATIONSHIP_TYPE = "prerequisite"

# This is a display-order policy, not a numerical recommendation score.
_GAP_TYPE_PRIORITY = {
    "unknown_current_level": 0,
    "level_gap": 1,
    "missing_prerequisite": 2,
    "met_target": 3,
    "exceeds_target": 4,
    "no_target": 5,
}


def level_gap_steps(current_order: int | None, target_order: int | None) -> int | None:
    """Return nonnegative canonical proficiency steps; unknown stays unknown."""
    if current_order is None or target_order is None:
        return None
    return max(0, target_order - current_order)


def prerequisite_ids_for_skill(
    skill_id: str,
    edges: dict[str, tuple[str, ...]],
) -> tuple[str, ...]:
    """Traverse outgoing prerequisite edges, safely handling repeated/cyclic edges."""
    visited: set[str] = set()
    pending = list(edges.get(skill_id, ()))
    while pending:
        prerequisite_id = pending.pop()
        if prerequisite_id == skill_id:
            # A cycle returning to the origin is invalid taxonomy data.
            raise ValueError(f"Prerequisite cycle reaches skill '{skill_id}'.")
        if prerequisite_id in visited:
            continue
        visited.add(prerequisite_id)
        pending.extend(edges.get(prerequisite_id, ()))
    return tuple(sorted(visited))


def _level_by_id(level_id: str | None, levels: dict[str, ProficiencyLevel]) -> ProficiencyLevel | None:
    if level_id is None:
        return None
    level = levels.get(level_id)
    if level is None:
        raise ValueError(f"Unknown canonical proficiency level: {level_id}")
    return level


def analyze_skill_gaps(
    db: Session,
    profile_id: UUID,
    career_target_id: UUID | None = None,
    domain_slug: str | None = None,
) -> SkillGapResponse:
    """Compute a read-only, deterministic skill-gap view.

    When a career target is supplied, its target-skill requirements define
    the comparison set. Otherwise, all tracked profile skills are listed,
    including skills without a target level (gap_type='no_target').
    """
    profile = db.get(PersonalSkillProfile, profile_id)
    if profile is None or not profile.is_active:
        raise ValueError("An active personal skill profile was not found.")

    domain_id: str | None = None
    if domain_slug is not None:
        domain_slug = domain_slug.strip()
        if not domain_slug:
            raise ValueError("domain_slug must not be empty.")
        domain = db.scalar(select(SkillDomain).where(SkillDomain.slug == domain_slug))
        if domain is None:
            raise ValueError("The requested canonical skill domain was not found.")
        domain_id = domain.domain_id

    states = list(db.scalars(
        select(PersonalSkillState).where(PersonalSkillState.profile_id == profile_id)
    ).all())
    state_by_skill = {state.skill_id: state for state in states}

    target_by_skill: dict[str, CareerTargetSkill] = {}
    if career_target_id is not None:
        career_target = db.get(CareerTarget, career_target_id)
        if career_target is None or career_target.profile_id != profile_id:
            raise ValueError("Career target not found for this personal profile.")
        requirements = list(db.scalars(
            select(CareerTargetSkill).where(
                CareerTargetSkill.career_target_id == career_target_id
            )
        ).all())
        target_by_skill = {item.skill_id: item for item in requirements}
        selected_ids = set(target_by_skill)
    else:
        selected_ids = set(state_by_skill)

    # Do not silently substitute a deprecated skill with a successor.
    skill_by_id: dict[str, Skill] = {}
    if selected_ids:
        skill_by_id = {
            skill.skill_id: skill
            for skill in db.scalars(select(Skill).where(Skill.skill_id.in_(selected_ids))).all()
        }
        if missing := (selected_ids - set(skill_by_id)):
            raise ValueError(f"Missing canonical skill references: {sorted(missing)}")

    if domain_id is not None:
        selected_ids = {
            skill_id for skill_id in selected_ids
            if skill_by_id[skill_id].domain_id == domain_id
        }

    # Profile states are the source of truth for prerequisite assessments,
    # including prerequisite skills outside the filtered domain.
    levels = {
        level.level_id: level
        for level in db.scalars(select(ProficiencyLevel)).all()
    }

    edge_rows = list(db.execute(
        select(SkillRelationship.source_skill_id, SkillRelationship.target_skill_id)
        .where(SkillRelationship.relationship_type == PREREQUISITE_RELATIONSHIP_TYPE)
    ).all())
    outgoing: dict[str, set[str]] = defaultdict(set)
    for source_id, target_id in edge_rows:
        outgoing[source_id].add(target_id)
    edges = {source: tuple(sorted(targets)) for source, targets in outgoing.items()}

    prereqs_by_skill = {
        skill_id: prerequisite_ids_for_skill(skill_id, edges)
        for skill_id in selected_ids
    }
    all_prerequisite_ids = {
        p for prerequisites in prereqs_by_skill.values() for p in prerequisites
    }
    prerequisite_skills = {
        skill.skill_id: skill
        for skill in db.scalars(
            select(Skill).where(Skill.skill_id.in_(all_prerequisite_ids))
        ).all()
    } if all_prerequisite_ids else {}
    if missing := (all_prerequisite_ids - set(prerequisite_skills)):
        raise ValueError(f"Missing prerequisite taxonomy skill references: {sorted(missing)}")

    # Count distinct trusted BOOKS, never pending mapping proposals.
    # Exclude inactive/deprecated books consistently with Phase 12 defaults.
    approved_book_count: dict[str, int] = {}
    if selected_ids:
        count_rows = db.execute(
            select(
                BookSkillMapping.skill_id,
                func.count(func.distinct(BookSkillMapping.document_id)),
            )
            .join(Document, Document.document_id == BookSkillMapping.document_id)
            .where(
                BookSkillMapping.skill_id.in_(selected_ids),
                BookSkillMapping.mapping_status == "approved",
                Document.is_active.is_(True),
                Document.is_deprecated.is_(False),
            )
            .group_by(BookSkillMapping.skill_id)
        ).all()
        approved_book_count = {skill_id: int(count) for skill_id, count in count_rows}

    items: list[SkillGapItem] = []
    met_count = 0
    level_gap_count = 0
    unknown_count = 0
    missing_prerequisite_count = 0
    targeted_count = 0

    for skill_id in sorted(selected_ids):
        skill = skill_by_id[skill_id]
        state = state_by_skill.get(skill_id)
        requirement = target_by_skill.get(skill_id)
        current_level = _level_by_id(
            state.current_level_id if state is not None else None, levels
        )
        target_level_id = (
            requirement.required_level_id if career_target_id is not None
            else state.target_level_id if state is not None else None
        )
        target_level = _level_by_id(target_level_id, levels)
        steps = level_gap_steps(
            current_level.level_order if current_level is not None else None,
            target_level.level_order if target_level is not None else None,
        )

        missing_prereqs: list[str] = []
        if target_level is not None:
            targeted_count += 1
            for prerequisite_id in prereqs_by_skill[skill_id]:
                prerequisite_state = state_by_skill.get(prerequisite_id)
                prerequisite_skill = prerequisite_skills[prerequisite_id]
                if (
                    prerequisite_state is None
                    or prerequisite_state.current_level_id is None
                    or not prerequisite_skill.is_active
                    or prerequisite_skill.is_deprecated
                ):
                    missing_prereqs.append(prerequisite_id)
            if missing_prereqs:
                missing_prerequisite_count += 1

        if target_level is None:
            gap_type = "no_target"
            description = "No target proficiency is recorded for this tracked skill."
        elif current_level is None:
            gap_type = "unknown_current_level"
            unknown_count += 1
            description = "Current proficiency has not been assessed; no numeric gap is inferred."
        elif steps is not None and steps > 0:
            gap_type = "level_gap"
            level_gap_count += 1
            description = (
                f"Current proficiency '{current_level.code}' is {steps} canonical level "
                f"step(s) below required '{target_level.code}'."
            )
        elif missing_prereqs:
            gap_type = "missing_prerequisite"
            description = "The target level is met, but prerequisite assessments are missing."
        else:
            met_count += 1
            if current_level.level_order > target_level.level_order:
                gap_type = "exceeds_target"
                description = "Current proficiency exceeds the target level."
            else:
                gap_type = "met_target"
                description = "Current proficiency meets the target level."

        if missing_prereqs:
            description += (
                " Unmet or deprecated prerequisites: "
                + ", ".join(missing_prereqs)
                + "."
            )
        if not skill.is_active or skill.is_deprecated:
            description += " This canonical skill is inactive/deprecated; review its historical reference."
        if requirement is not None and not requirement.is_required:
            description += " This is a beneficial, not mandatory, career-target skill."
        if state is not None and current_level is not None and state.last_assessed_at is None:
            description += " Assessment review date is not recorded."

        items.append(SkillGapItem(
            skill_id=skill_id,
            skill_name=skill.name,
            current_level=current_level.code if current_level is not None else None,
            target_level=target_level.code if target_level is not None else None,
            gap_steps=steps,
            career_importance=(requirement.importance_weight if requirement is not None else None),
            confidence=state.confidence if state is not None else None,
            gap_type=gap_type,
            missing_prerequisite_skill_ids=missing_prereqs,
            approved_supporting_book_count=approved_book_count.get(skill_id, 0),
            explanation=description,
        ))

    items.sort(key=lambda item: (
        -(item.career_importance or 0),
        _GAP_TYPE_PRIORITY[item.gap_type],
        item.skill_name.casefold(),
        item.skill_id,
    ))

    tracked_skill_rows = db.execute(
        select(PersonalSkillState.skill_id, Skill.domain_id)
        .join(Skill, Skill.skill_id == PersonalSkillState.skill_id)
        .where(PersonalSkillState.profile_id == profile_id)
    ).all()
    tracked_count = sum(
        1 for _, tracked_domain_id in tracked_skill_rows
        if domain_id is None or tracked_domain_id == domain_id
    )

    return SkillGapResponse(
        profile_id=profile_id,
        career_target_id=career_target_id,
        summary=SkillGapSummary(
            tracked_skills=tracked_count,
            target_skills=targeted_count,
            met_or_exceeded=met_count,
            level_gaps=level_gap_count,
            unknown_current_level=unknown_count,
            missing_prerequisites=missing_prerequisite_count,
        ),
        gaps=items,
    )