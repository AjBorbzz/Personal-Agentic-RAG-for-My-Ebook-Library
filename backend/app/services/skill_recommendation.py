"""Phase 13F: recommendation generation, human decisions, queue and agent seeds."""
from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.book_skill_mapping import BookSkillMapping
from app.models.document import Document
from app.models.personal_skill_profile import PersonalSkillProfile, PersonalSkillState
from app.models.skill_recommendation import RecommendationRun, ReadingQueueItem, SkillRecommendation
from app.models.skill_taxonomy import ProficiencyLevel, Skill
from app.schemas.skill_gap import SkillGapItem
from app.schemas.skill_recommendation import (
    GenerateRecommendationsRequest, RecommendationDecisionPatch,
    ReadingQueueCreate, ReadingQueuePatch,
)
from app.services.skill_gap_analysis import analyze_skill_gaps
from app.services.skill_recommendation_policy import (
    RULE_VERSION, evidence_need_factor, gap_severity_factor,
    importance_factor, prioritize, trusted_quality_factor,
)

_DECISION_EDGES = {
    "new": {"accepted", "deferred", "dismissed"},
    "accepted": {"deferred", "dismissed", "completed"},
    "deferred": {"accepted", "dismissed"},
    "dismissed": {"accepted"},
    "completed": {"accepted"},
}
_QUEUE_EDGES = {
    "queued": {"active", "paused", "completed", "removed"},
    "active": {"paused", "completed", "removed"},
    "paused": {"queued", "active", "removed"},
    "completed": {"active"},
    "removed": {"queued"},
}


def _profile(db: Session, profile_id: UUID) -> PersonalSkillProfile:
    value = db.get(PersonalSkillProfile, profile_id)
    if value is None or not value.is_active:
        raise ValueError("Active personal profile not found.")
    return value


def _gap_factors(gap: SkillGapItem, resource_fit: float):
    return prioritize(
        gap_severity=gap_severity_factor(gap.gap_steps, gap.gap_type == "unknown_current_level"),
        career_importance=importance_factor(gap.career_importance),
        prerequisite_criticality=1.0 if gap.missing_prerequisite_skill_ids else 0.0,
        resource_fit=resource_fit,
        evidence_need=evidence_need_factor(gap.confidence, gap.gap_type == "unknown_current_level"),
    )


def _eligible_books(db: Session, skill_id: str, current_order: int | None,
                    level_orders: dict[str, int]) -> list[tuple[BookSkillMapping, Document]]:
    rows = db.execute(
        select(BookSkillMapping, Document)
        .join(Document, Document.document_id == BookSkillMapping.document_id)
        .where(
            BookSkillMapping.skill_id == skill_id,
            BookSkillMapping.mapping_status == "approved",
            Document.is_active.is_(True),
            Document.is_deprecated.is_(False),
        )
        .order_by(BookSkillMapping.mapping_id)
    ).all()
    eligible = []
    for mapping, document in rows:
        entry_id = mapping.recommended_entry_level_id
        exit_id = mapping.recommended_exit_level_id
        if entry_id is not None and entry_id not in level_orders:
            raise ValueError(f"Unknown entry level on approved mapping {mapping.mapping_id}")
        if exit_id is not None and exit_id not in level_orders:
            raise ValueError(f"Unknown exit level on approved mapping {mapping.mapping_id}")
        if current_order is None and (entry_id is not None or exit_id is not None):
            continue  # cannot assert proficiency compatibility for an unassessed user
        if current_order is not None:
            if entry_id is not None and current_order < level_orders[entry_id]:
                continue
            if exit_id is not None and current_order >= level_orders[exit_id]:
                continue
        # A mapping that has no usable approved quality values cannot establish fit.
        if not any(Decimal(str(getattr(mapping, name, None) or 0)) > 0
                   for name in ("relevance_score", "coverage_score", "depth_score", "practicality_score")):
            continue
        eligible.append((mapping, document))
    return eligible


def _proposal(gap: SkillGapItem, item_type: str, title: str, explanation: str,
              resource_fit: float = 0.0, mapping_id: str | None = None,
              document_id: str | None = None, metadata: dict | None = None) -> dict:
    value = _gap_factors(gap, resource_fit)
    components = dict(value.score_components)
    components["source_gap_type"] = gap.gap_type
    components["gap_steps"] = gap.gap_steps
    components["missing_prerequisite_skill_ids"] = gap.missing_prerequisite_skill_ids
    components["approved_supporting_book_count"] = gap.approved_supporting_book_count
    components["resource_fit_details"] = metadata or {}
    return dict(
        skill_id=gap.skill_id,
        recommendation_type=item_type,
        title=title,
        explanation=explanation,
        priority_score=value.priority_score,
        score_components=components,
        source_mapping_ids=[mapping_id] if mapping_id is not None else [],
        recommended_document_id=document_id,
    )


def generate_recommendations(db: Session, payload: GenerateRecommendationsRequest) -> UUID:
    """Synchronous, deterministic generation. New runs are explicit snapshots."""
    _profile(db, payload.profile_id)
    # Gap engine owns canonical target/profile validation; run not created until it passes.
    gaps = analyze_skill_gaps(db, payload.profile_id, payload.career_target_id, payload.domain_slug)
    level_orders = {
        level.level_id: level.level_order
        for level in db.scalars(select(ProficiencyLevel)).all()
    }
    current_level_by_skill = {
        row.skill_id: row.current_level_id
        for row in db.scalars(select(PersonalSkillState).where(
            PersonalSkillState.profile_id == payload.profile_id
        )).all()
    }
    snapshot = {
        "rule_version": RULE_VERSION,
        "filters": {"domain_slug": payload.domain_slug, "max_books_per_skill": payload.max_books_per_skill},
        "gap_response": gaps.model_dump(mode="json"),
    }
    run = RecommendationRun(
        profile_id=payload.profile_id,
        career_target_id=payload.career_target_id,
        rule_version=RULE_VERSION,
        input_snapshot=snapshot,
        status="running",
    )
    db.add(run)
    db.commit()  # persist a run even if generation subsequently fails
    db.refresh(run)
    run_id = run.recommendation_run_id

    try:
        proposals: list[dict] = []
        deficits = [g for g in gaps.gaps if g.gap_type not in ("met_target", "exceeds_target", "no_target")]
        for gap in deficits:
            if gap.missing_prerequisite_skill_ids:
                proposals.append(_proposal(
                    gap, "prerequisite", f"Review prerequisites for {gap.skill_name}",
                    "Canonical missing prerequisites: " + ", ".join(gap.missing_prerequisite_skill_ids)
                    + ". Assess these skills before assuming readiness.",
                ))
            if gap.gap_type == "unknown_current_level":
                proposals.append(_proposal(
                    gap, "evidence", f"Assess your {gap.skill_name} proficiency",
                    "Current level is unassessed. Record a human-reviewed assessment; do not infer proficiency from books.",
                ))
                continue
            # An unmet prerequisite blocks advancement books for the target skill;
            # keep only prerequisite repair, not an over-confident resource match.
            if gap.missing_prerequisite_skill_ids:
                continue

            if gap.gap_type in ("level_gap", "missing_prerequisite"):
                level_id = current_level_by_skill.get(gap.skill_id)
                if level_id is not None and level_id not in level_orders:
                    raise ValueError(f"Unknown proficiency level in profile: {level_id}")
                order = level_orders.get(level_id)
                eligible = _eligible_books(db, gap.skill_id, order, level_orders)
                max_values: dict[str, Decimal] = {}
                for key in ("relevance_score", "coverage_score", "depth_score", "practicality_score"):
                    max_values[key] = max(
                        (Decimal(str(getattr(m, key, None) or 0)) for m, _ in eligible),
                        default=Decimal("0"),
                    )
                ranked = []
                for mapping, doc in eligible:
                    quality = trusted_quality_factor(mapping, max_values)
                    # All eligible books pass entry/exit gate. Unknown bounds are disclosed.
                    level_fit = 1.0 if (
                        mapping.recommended_entry_level_id is not None
                        and mapping.recommended_exit_level_id is not None
                    ) else 0.5
                    fit = round(0.8 * quality + 0.2 * level_fit, 6)
                    if fit <= 0.15:
                        continue
                    ranked.append((fit, str(mapping.mapping_id), mapping, doc, quality, level_fit))
                ranked.sort(key=lambda x: (-x[0], x[1]))
                for fit, mapping_id, mapping, doc, quality, level_fit in ranked[:payload.max_books_per_skill]:
                    title = getattr(doc, "title", None) or getattr(doc, "filename", None) or str(doc.document_id)
                    proposals.append(_proposal(
                        gap, "book", f"Read {title} for {gap.skill_name}",
                        f"Approved mapping {mapping_id} for skill {gap.skill_id}; "
                        f"trusted relative quality={quality:.3f}, proficiency-fit={level_fit:.2f}. "
                        "The resource is active and not deprecated.",
                        fit, mapping_id, str(doc.document_id),
                        {"relative_score_maxima": {k: str(v) for k, v in max_values.items()},
                         "quality": quality, "level_fit": level_fit,
                         "approved_trusted_scores": {
                             k: str(getattr(mapping, k, None) or 0)
                             for k in ("relevance_score", "coverage_score", "depth_score", "practicality_score")
                         },
                         "recommended_entry_level_id": mapping.recommended_entry_level_id,
                         "recommended_exit_level_id": mapping.recommended_exit_level_id,
                         "current_level_id": level_id},
                    ))
                if not ranked:
                    proposals.append(_proposal(
                        gap, "project", f"Practice {gap.skill_name} without a matched book",
                        "No eligible approved, active, non-deprecated book fits this assessment. "
                        "Use an evidence-producing project instead; do not substitute pending mappings.",
                    ))
                elif (gap.gap_steps or 0) >= 2:
                    proposals.append(_proposal(
                        gap, "project", f"Build a project demonstrating {gap.skill_name}",
                        "A multi-level gap warrants practical evidence; seed the existing Project Generator, "
                        "then review its output before creating a project.",
                    ))
        if len(deficits) >= 2:
            first = sorted(deficits, key=lambda g: (g.skill_id, g.skill_name))[0]
            proposals.append(_proposal(
                first, "learning_path", "Plan a sequence across skill gaps",
                "Several related target deficits are present. Seed the existing Learning Path Agent "
                "with canonical skill IDs and the captured gap snapshot.",
                metadata={"skill_ids": sorted({g.skill_id for g in deficits})},
            ))

        proposals.sort(key=lambda p: (
            -p["priority_score"], p["skill_id"], p["recommendation_type"],
            p["recommended_document_id"] or "", ",".join(p["source_mapping_ids"])
        ))
        for proposed in proposals:
            db.add(SkillRecommendation(recommendation_run_id=run_id, **proposed))
        current_run = db.get(RecommendationRun, run_id)
        current_run.status = "completed"
        db.commit()
    except Exception as exc:
        db.rollback()
        failed = db.get(RecommendationRun, run_id)
        if failed is not None:
            failed.status = "failed"
            failed.error_detail = f"{type(exc).__name__}: {str(exc)}"[:2000]
            db.commit()
        raise
    return run_id


def get_run_detail(db: Session, run_id: UUID):
    run = db.get(RecommendationRun, run_id)
    if run is None:
        raise ValueError("Recommendation run not found.")
    items = list(db.scalars(
        select(SkillRecommendation)
        .where(SkillRecommendation.recommendation_run_id == run_id)
        .order_by(SkillRecommendation.priority_score.desc(),
                  SkillRecommendation.skill_id, SkillRecommendation.recommendation_type,
                  SkillRecommendation.recommended_document_id, SkillRecommendation.recommendation_id)
    ).all())
    return run, items


def current_recommendations(db: Session, profile_id: UUID, career_target_id: UUID | None,
                            decision_status: str | None, limit: int):
    _profile(db, profile_id)
    statement = select(RecommendationRun).where(
        RecommendationRun.profile_id == profile_id,
        RecommendationRun.status == "completed",
    )
    if career_target_id is None:
        statement = statement.where(RecommendationRun.career_target_id.is_(None))
    else:
        statement = statement.where(RecommendationRun.career_target_id == career_target_id)
    run = db.scalar(statement.order_by(
        RecommendationRun.generated_at.desc(), RecommendationRun.recommendation_run_id.desc()
    ).limit(1))
    if run is None:
        return []
    q = select(SkillRecommendation).where(
        SkillRecommendation.recommendation_run_id == run.recommendation_run_id
    )
    if decision_status is not None:
        q = q.where(SkillRecommendation.decision_status == decision_status)
    return list(db.scalars(q.order_by(
        SkillRecommendation.priority_score.desc(), SkillRecommendation.skill_id,
        SkillRecommendation.recommendation_type, SkillRecommendation.recommendation_id
    ).limit(limit)).all())


def decide_recommendation(db: Session, recommendation_id: UUID, payload: RecommendationDecisionPatch):
    rec = db.get(SkillRecommendation, recommendation_id)
    if rec is None:
        raise ValueError("Recommendation not found.")
    desired = payload.decision_status
    if desired != rec.decision_status and desired not in _DECISION_EDGES[rec.decision_status]:
        raise ValueError(f"Invalid decision transition: {rec.decision_status} -> {desired}.")
    rec.decision_status = desired
    rec.decision_notes = payload.decision_notes
    db.commit()
    db.refresh(rec)
    return rec


def _active_document(db: Session, document_id: str) -> Document:
    doc = db.get(Document, document_id)
    if doc is None or not doc.is_active or doc.is_deprecated:
        raise ValueError("Active non-deprecated document not found.")
    return doc


def _active_skill(db: Session, skill_id: str) -> Skill:
    skill = db.get(Skill, skill_id)
    if skill is None or not skill.is_active or skill.is_deprecated:
        raise ValueError("Active canonical skill not found.")
    return skill


def create_queue_item(db: Session, data: ReadingQueueCreate):
    _profile(db, data.profile_id)
    doc_id = data.document_id
    skill_id = data.skill_id
    rec = None
    if data.recommendation_id is not None:
        rec = db.get(SkillRecommendation, data.recommendation_id)
        if rec is None:
            raise ValueError("Recommendation not found.")
        run = db.get(RecommendationRun, rec.recommendation_run_id)
        if run.profile_id != data.profile_id:
            raise ValueError("Recommendation belongs to a different profile.")
        if rec.decision_status == "dismissed":
            raise ValueError("Accept a dismissed recommendation before queuing it.")
        if data.document_id and rec.recommended_document_id != data.document_id:
            raise ValueError("Document does not match the linked recommendation.")
        if data.skill_id and rec.skill_id != data.skill_id:
            raise ValueError("Skill does not match the linked recommendation.")
        doc_id = rec.recommended_document_id
        skill_id = rec.skill_id
    if doc_id is not None:
        _active_document(db, doc_id)
    if skill_id is not None:
        _active_skill(db, skill_id)
    item = ReadingQueueItem(
        profile_id=data.profile_id, recommendation_id=data.recommendation_id,
        document_id=doc_id, skill_id=skill_id, priority=data.priority,
        planned_start=data.planned_start, target_finish=data.target_finish, notes=data.notes,
        status="queued", progress_percent=0,
    )
    db.add(item)
    if rec is not None and rec.decision_status in ("new", "deferred"):
        rec.decision_status = "accepted"
    db.commit()
    db.refresh(item)
    return item


def get_queue_item(db: Session, item_id: UUID):
    row = db.get(ReadingQueueItem, item_id)
    if row is None:
        raise ValueError("Reading queue item not found.")
    return row


def list_queue_items(db: Session, profile_id: UUID, limit: int):
    _profile(db, profile_id)
    return list(db.scalars(
        select(ReadingQueueItem).where(ReadingQueueItem.profile_id == profile_id)
        .order_by(ReadingQueueItem.priority.desc(), ReadingQueueItem.created_at, ReadingQueueItem.reading_queue_item_id)
        .limit(limit)
    ).all())


def update_queue_item(db: Session, item_id: UUID, data: ReadingQueuePatch):
    item = get_queue_item(db, item_id)
    changes = data.model_dump(exclude_unset=True)
    if "status" in changes:
        new_status = changes["status"]
        if new_status is None:
            raise ValueError("status cannot be null.")
        if new_status != item.status and new_status not in _QUEUE_EDGES[item.status]:
            raise ValueError(f"Invalid queue transition: {item.status} -> {new_status}.")
    if "priority" in changes and changes["priority"] is None:
        raise ValueError("priority cannot be null.")
    if "progress_percent" in changes and changes["progress_percent"] is None:
        raise ValueError("progress_percent cannot be null.")
    start = changes.get("planned_start", item.planned_start)
    end = changes.get("target_finish", item.target_finish)
    if start is not None and end is not None and end < start:
        raise ValueError("target_finish must be on or after planned_start.")
    for key, value in changes.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


def agent_seed(db: Session, recommendation_id: UUID, agent_type: str) -> dict:
    rec = db.get(SkillRecommendation, recommendation_id)
    if rec is None:
        raise ValueError("Recommendation not found.")
    if rec.recommendation_type != agent_type:
        raise ValueError(f"This is not a {agent_type} recommendation.")
    run = db.get(RecommendationRun, rec.recommendation_run_id)
    gaps = run.input_snapshot.get("gap_response", {}).get("gaps", [])
    if agent_type == "learning_path":
        skill_ids = sorted({g["skill_id"] for g in gaps
                            if g.get("gap_type") not in ("met_target", "exceeds_target", "no_target")})
    else:
        gap = next((g for g in gaps if g["skill_id"] == rec.skill_id), {})
        skill_ids = sorted(set([rec.skill_id] + gap.get("missing_prerequisite_skill_ids", [])))
    # Even for action seeds, supporting documents must come from approved mappings.
    rows = db.execute(
        select(BookSkillMapping.mapping_id, BookSkillMapping.document_id)
        .join(Document, Document.document_id == BookSkillMapping.document_id)
        .where(
            BookSkillMapping.skill_id.in_(skill_ids),
            BookSkillMapping.mapping_status == "approved",
            Document.is_active.is_(True), Document.is_deprecated.is_(False),
        )
    ).all()
    return {
        "agent_type": agent_type,
        "profile_id": run.profile_id,
        "career_target_id": run.career_target_id,
        "recommendation_id": rec.recommendation_id,
        "primary_skill_id": rec.skill_id,
        "skill_ids": skill_ids,
        "source_document_ids": sorted({str(doc_id) for _, doc_id in rows}),
        "source_mapping_ids": sorted({str(mapping_id) for mapping_id, _ in rows}),
        "title": rec.title,
        "objective": rec.explanation,
    }