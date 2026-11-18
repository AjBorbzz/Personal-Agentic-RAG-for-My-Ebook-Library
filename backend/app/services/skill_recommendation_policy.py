"""13F.1 deterministic, versioned pure functions (never affects RAG ranking)."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from math import isfinite

RULE_VERSION = "13F.1-v1"
WEIGHTS = {
    "gap_severity": Decimal("0.30"),
    "career_importance": Decimal("0.25"),
    "prerequisite_criticality": Decimal("0.15"),
    "resource_fit": Decimal("0.20"),
    "evidence_need": Decimal("0.10"),
}


@dataclass(frozen=True)
class PriorityResult:
    priority_score: Decimal  # 0.00 to 100.00
    score_components: dict  # JSON-safe, reproducible factors, weights and contributions


def _bounded(value: float | int | Decimal) -> Decimal:
    n = Decimal(str(value))
    if not n.is_finite() or n < 0 or n > 1:
        raise ValueError("Score factor must be a finite number from 0 to 1.")
    return n


def prioritize(*, gap_severity, career_importance, prerequisite_criticality,
               resource_fit, evidence_need) -> PriorityResult:
    factors = {
        "gap_severity": _bounded(gap_severity),
        "career_importance": _bounded(career_importance),
        "prerequisite_criticality": _bounded(prerequisite_criticality),
        "resource_fit": _bounded(resource_fit),
        "evidence_need": _bounded(evidence_need),
    }
    score = (sum(WEIGHTS[k] * factors[k] for k in WEIGHTS) * 100).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    return PriorityResult(
        priority_score=score,
        score_components={
            "rule_version": RULE_VERSION,
            "factors": {k: float(v) for k, v in factors.items()},
            "weights": {k: float(v) for k, v in WEIGHTS.items()},
            "contributions": {k: float((factors[k] * WEIGHTS[k] * 100).quantize(Decimal("0.01"))) for k in WEIGHTS},
            "priority_score": float(score),
        },
    )


def gap_severity_factor(gap_steps: int | None, unknown_current: bool) -> float:
    # Explicit baseline: unknown is a review need, NOT an inferred proficiency.
    if unknown_current:
        return 0.75
    if gap_steps is None:
        return 0.0
    if gap_steps < 0:
        raise ValueError("gap_steps cannot be negative")
    return min(gap_steps / 4, 1.0)


def importance_factor(career_importance: int | None) -> float:
    if career_importance is None:
        return 0.20  # no career target supplied: low baseline, not a fabricated target
    if not 1 <= career_importance <= 5:
        raise ValueError("career_importance must be between 1 and 5")
    return career_importance / 5


def evidence_need_factor(confidence: Decimal | None, unknown_current: bool) -> float:
    if unknown_current:
        return 1.0
    if confidence is None:
        return 0.50  # unknown confidence is neutral; no invented staleness threshold
    return float(Decimal("1") - _bounded(confidence))


def trusted_quality_factor(mapping, maxima: dict[str, Decimal]) -> float:
    """Normalize approved mapping scores within the eligible candidate set.

    Do not assume stored mapping numeric ranges are 0..1, 0..5 or 0..10.
    The candidate-set maxima are captured in score_components by the caller.
    """
    dimensions = {"relevance_score": Decimal("0.30"),
                  "coverage_score": Decimal("0.25"),
                  "depth_score": Decimal("0.25"),
                  "practicality_score": Decimal("0.20")}
    total = Decimal("0")
    for key, weight in dimensions.items():
        value = Decimal(str(getattr(mapping, key, None) or 0))
        peak = maxima.get(key, Decimal("0"))
        if value < 0:
            raise ValueError(f"Negative trusted mapping score: {key}")
        total += weight * (min(value / peak, Decimal("1")) if peak > 0 else Decimal("0"))
    return float(total)