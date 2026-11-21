"""Deterministic signals; never present keyword coverage as proof of grounding."""
from __future__ import annotations
from typing import Any


def sources_from_payload(payload: Any) -> list[dict]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if not isinstance(payload, dict):
        raise ValueError("API response is neither an object nor a list")
    for key in ("sources", "results", "matches", "retrieved_sources", "chunks"):
        value = payload.get(key)
        if isinstance(value, list):
            return [x for x in value if isinstance(x, dict)]
    raise ValueError("Source list absent: inspect live /search or /rag-chat response schema")


def normalize_source(item: dict) -> dict:
    """Preserve essential retrieval metadata without logging chunk text."""
    obj = item.get("source") if isinstance(item.get("source"), dict) else item
    metadata = obj.get("metadata") if isinstance(obj.get("metadata"), dict) else {}
    def val(name):
        value = obj.get(name)
        return value if value is not None else metadata.get(name)
    return {key: val(key) for key in (
        "document_id", "page_start", "page_end", "score", "source_file", "primary_domain",
        "domains", "is_active", "is_deprecated", "tool_name", "tool_version",
        "version_major", "version_minor", "source_type", "publication_year"
    )}


def retrieval_metrics(sources: list[dict], expected_docs: list[str], k: int) -> dict:
    if k < 1:
        raise ValueError("k must be positive")
    top = [str(x.get("document_id")) for x in sources[:k] if x.get("document_id") is not None]
    relevant = set(map(str, expected_docs))
    hits = sum(doc in relevant for doc in top)
    first_rank = next((i for i, doc in enumerate(top, 1) if doc in relevant), None)
    # No expected labels => not measurable, never report a fabricated perfect score.
    return {
        "recall_at_k": round(len(set(top) & relevant) / len(relevant), 4) if relevant else None,
        "precision_at_k": round(hits / len(top), 4) if relevant and top else (0.0 if relevant else None),
        "mrr": round(1 / first_rank, 4) if first_rank else (0.0 if relevant else None),
        "expected_doc_count": len(relevant),
        "retrieved_count": len(top),
    }


def concept_coverage(answer: str, expected_concepts: list[str]) -> float | None:
    if not expected_concepts:
        return None
    s = " ".join(answer.casefold().split())
    return round(sum(c.casefold() in s for c in expected_concepts) / len(expected_concepts), 4)


def page_overlap(sources: list[dict], expected_ranges: list[dict]) -> bool | None:
    if not expected_ranges:
        return None
    for expected in expected_ranges:
        for s in sources:
            if str(s.get("document_id")) != str(expected.get("document_id")):
                continue
            try:
                start, end = int(s["page_start"]), int(s["page_end"])
                a, b = int(expected["page_start"]), int(expected["page_end"])
                if start <= b and a <= end:
                    return True
            except (KeyError, TypeError, ValueError):
                pass
    return False


def requested_filter_issues(sources: list[dict], filters: dict) -> list[str]:
    """Unknown metadata is a verification gap; never call it a successful filter."""
    issues: list[str] = []
    for i, s in enumerate(sources):
        if filters.get("active_only", True) and s.get("is_active") is False:
            issues.append(f"source[{i}]:inactive_leak")
        if not filters.get("include_deprecated", False) and s.get("is_deprecated") is True:
            issues.append(f"source[{i}]:deprecated_leak")
        for key in ("tool_name", "tool_version", "source_type", "publication_year", "version_major", "version_minor"):
            if filters.get(key) is not None and s.get(key) != filters[key]:
                issues.append(f"source[{i}]:{key}_mismatch_or_missing")
    return issues