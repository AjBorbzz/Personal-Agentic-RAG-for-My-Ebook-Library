"""Phase 14 batch evaluation. Uses live endpoints and authoritative document rows."""
from __future__ import annotations
import time
from collections import Counter
from datetime import datetime, timezone
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.evaluation import EvaluationCase, EvaluationResult, EvaluationRun
from app.evaluation.metrics import (
    concept_coverage, normalize_source, page_overlap, requested_filter_issues,
    retrieval_metrics, sources_from_payload,
)


def as_dict(row):
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


def _registry_issues(db: Session, sources: list[dict], filters: dict) -> tuple[list[str], bool]:
    issues: list[str] = []
    valid_citations = True
    for index, src in enumerate(sources):
        document_id = src.get("document_id")
        doc = db.get(Document, str(document_id)) if document_id else None
        if doc is None:
            valid_citations = False
            issues.append(f"source[{index}]:unknown_document")
            continue
        if filters.get("active_only", True) and not getattr(doc, "is_active", True):
            issues.append(f"source[{index}]:inactive_leak")
        if not filters.get("include_deprecated", False) and getattr(doc, "is_deprecated", False):
            issues.append(f"source[{index}]:deprecated_leak")
        for key in ("tool_name", "tool_version", "source_type", "publication_year", "version_major", "version_minor"):
            if filters.get(key) is not None and getattr(doc, key, None) != filters[key]:
                issues.append(f"source[{index}]:registry_{key}_mismatch")
        # PDF pages must be present, positive and ordered; max page count cannot be
        # proven without a document-page table. Support of claims remains human-owned.
        start, end = src.get("page_start"), src.get("page_end")
        if start is None or end is None:
            if str(getattr(doc, "source_type", "")).lower().endswith("pdf"):
                valid_citations = False
                issues.append(f"source[{index}]:pdf_page_missing")
        else:
            try:
                if int(start) < 1 or int(end) < int(start):
                    raise ValueError("invalid page range")
            except (TypeError, ValueError):
                valid_citations = False
                issues.append(f"source[{index}]:invalid_page_range")
    return issues, valid_citations


def _request(client: httpx.Client, url: str, body: dict) -> dict:
    r = client.post(url, json=body)
    if r.status_code >= 400:
        # Bounded error detail, no full question or local book content in diagnostics.
        raise RuntimeError(f"{url.rsplit('/', 1)[-1]} HTTP {r.status_code}: {r.text[:300]}")
    payload = r.json()
    if not isinstance(payload, (dict, list)):
        raise RuntimeError("Unexpected API response structure")
    return payload


def _eval_one(db: Session, client: httpx.Client, case: EvaluationCase, k: int, base_url: str):
    started = time.monotonic()
    result = EvaluationResult(evaluation_case_id=case.evaluation_case_id)
    try:
        filters = dict(case.request_filters or {})
        filters.setdefault("active_only", True)
        filters.setdefault("include_deprecated", False)
        search_req = {"query": case.question, "limit": k, **filters}
        rag_req = {"question": case.question, "limit": k, **filters}
        search_payload = _request(client, f"{base_url}/search", search_req)
        rag_payload = _request(client, f"{base_url}/rag-chat", rag_req)
        if not isinstance(rag_payload, dict) or not isinstance(rag_payload.get("answer"), str):
            raise ValueError("/rag-chat must provide a string 'answer'")
        raw_search = sources_from_payload(search_payload)
        raw_citations = sources_from_payload(rag_payload)
        sources = [normalize_source(x) for x in raw_search]
        citations = [normalize_source(x) for x in raw_citations]
        doc_issues, _ = _registry_issues(db, sources, filters)
        citation_issues, citations_have_valid_identity_and_pages = _registry_issues(db, citations, filters)
        filter_issues = requested_filter_issues(sources, filters)
        forbidden = set(map(str, case.forbidden_document_ids or []))
        forbidden_hits = sorted({str(s.get("document_id")) for s in sources + citations
                                 if s.get("document_id") is not None and str(s["document_id"]) in forbidden})
        metrics = retrieval_metrics(sources, case.expected_document_ids or [], k)
        metrics["page_overlap"] = page_overlap(sources, case.expected_page_ranges or [])
        expected_domains = set(case.expected_domains or [])
        returned_domains = set()
        for source in sources:
            if source.get("primary_domain"):
                returned_domains.add(source["primary_domain"])
            if isinstance(source.get("domains"), list):
                returned_domains.update(source["domains"])
        metrics["domain_coverage"] = (
            round(len(expected_domains & returned_domains) / len(expected_domains), 4)
            if expected_domains and returned_domains else None
        )
        metrics["version_filter_issues_count"] = len([
            issue for issue in filter_issues + doc_issues
            if any(key in issue for key in ("version", "tool_name", "source_type", "publication_year"))
        ])
        metrics["concept_coverage_proxy"] = concept_coverage(rag_payload["answer"], case.expected_concepts or [])
        metrics["insufficient_evidence"] = bool(rag_payload.get("insufficient_evidence", False))
        metrics["refusal_expected"] = bool(case.expected_refusal)
        metrics["citation_identity_page_valid"] = bool(citations_have_valid_identity_and_pages)
        metrics["forbidden_document_hits"] = forbidden_hits
        # Metadata absence is not equivalent to source compliance.
        metrics["filter_metadata_issues"] = filter_issues
        metrics["citation_claim_support"] = "requires_human_review"
        failures = sorted(set(doc_issues + citation_issues + filter_issues))
        if forbidden_hits:
            failures.append("forbidden_source_leak")
        if case.expected_document_ids and metrics["recall_at_k"] != 1.0:
            failures.append("missing_expected_document")
        if metrics["page_overlap"] is False:
            failures.append("missing_expected_page")
        if case.expected_concepts and metrics["concept_coverage_proxy"] < 1.0:
            failures.append("missing_expected_concept_proxy")
        if case.expected_refusal != metrics["insufficient_evidence"]:
            failures.append("refusal_mismatch")
        if not case.expected_refusal and not citations:
            failures.append("missing_citations")
        result.retrieved_sources = sources
        result.answer = rag_payload["answer"][:10000]
        result.citations = citations
        result.metrics = metrics
        result.failure_categories = sorted(set(failures))
        # Human claim review is not inferred. The acceptance flag remains false
        # until explicitly approved through the review endpoint.
        result.passed = False
    except Exception as exc:
        result.error_detail = f"{type(exc).__name__}: {str(exc)[:350]}"
        result.failure_categories = ["evaluation_execution_error"]
        result.metrics = {"citation_claim_support": "not_assessed"}
        result.passed = False
    finally:
        result.latency_ms = int((time.monotonic() - started) * 1000)
    return result


def _summary(results: list[EvaluationResult]) -> dict:
    n = len(results)
    errors = Counter(category for r in results for category in (r.failure_categories or []))
    def avg(name: str):
        vals = [r.metrics.get(name) for r in results if isinstance(r.metrics, dict)
                and isinstance(r.metrics.get(name), (int, float))]
        return round(sum(vals) / len(vals), 4) if vals else None
    return {
        "case_count": n,
        "passed_count": sum(bool(r.passed) for r in results),
        "pending_human_review_count": sum(r.human_groundedness is None for r in results),
        "error_count": sum(bool(r.error_detail) for r in results),
        "avg_recall_at_k": avg("recall_at_k"),
        "avg_precision_at_k": avg("precision_at_k"),
        "avg_mrr": avg("mrr"),
        "avg_latency_ms": round(sum(r.latency_ms for r in results) / n, 1) if n else 0,
        "failure_categories": dict(errors),
    }


def _update_summary(db: Session, run: EvaluationRun):
    results = list(db.scalars(select(EvaluationResult).where(
        EvaluationResult.evaluation_run_id == run.evaluation_run_id)).all())
    run.summary_metrics = _summary(results)
    db.commit()
    db.refresh(run)


def execute_run(db: Session, *, dataset_name: str, dataset_version: str,
                system_config: dict, baseline_run_id: UUID | None = None,
                k: int = 5, max_cases: int = 20, base_url: str = "http://127.0.0.1:8000"):
    cases = list(db.scalars(select(EvaluationCase).where(
        EvaluationCase.dataset_name == dataset_name,
        EvaluationCase.dataset_version == dataset_version,
        EvaluationCase.is_active.is_(True)
    ).order_by(EvaluationCase.case_id).limit(max_cases)).all())
    if not cases:
        raise ValueError("No active cases in requested dataset/version")
    if baseline_run_id:
        baseline = db.get(EvaluationRun, baseline_run_id)
        if baseline is None or baseline.status != "completed":
            raise ValueError("Baseline run not found or not completed")
        if (baseline.dataset_name, baseline.dataset_version) != (dataset_name, dataset_version):
            raise ValueError("Baseline must use the identical dataset and version")
    run = EvaluationRun(dataset_name=dataset_name, dataset_version=dataset_version,
                        system_config={**system_config, "top_k": k},
                        baseline_run_id=baseline_run_id, status="running")
    db.add(run)
    db.commit()
    db.refresh(run)
    try:
        with httpx.Client(timeout=120.0) as client:
            for case in cases:
                result = _eval_one(db, client, case, k, base_url.rstrip("/"))
                result.evaluation_run_id = run.evaluation_run_id
                db.add(result)
                db.commit()
        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)
        _update_summary(db, run)
    except Exception as exc:
        db.rollback()
        run.status = "failed"
        run.error_detail = f"{type(exc).__name__}: {str(exc)[:300]}"
        run.completed_at = datetime.now(timezone.utc)
        db.commit()
    return run


def comparison(db: Session, run: EvaluationRun) -> dict | None:
    if not run.baseline_run_id:
        return None
    base = db.get(EvaluationRun, run.baseline_run_id)
    if base is None:
        return {"status": "baseline_missing"}
    before, after = base.summary_metrics or {}, run.summary_metrics or {}
    deltas = {}
    for key in ("avg_recall_at_k", "avg_precision_at_k", "avg_mrr", "avg_latency_ms"):
        if isinstance(before.get(key), (int, float)) and isinstance(after.get(key), (int, float)):
            deltas[key] = round(after[key] - before[key], 4)
    safety_categories = ("forbidden_source_leak", "deprecated_leak", "inactive_leak", "unknown_document", "invalid_page_range")
    unsafe_increase = any(
        sum(v for k, v in (after.get("failure_categories") or {}).items() if category in k) >
        sum(v for k, v in (before.get("failure_categories") or {}).items() if category in k)
        for category in safety_categories
    )
    quality_regression = any(deltas.get(key, 0) < 0 for key in
                             ("avg_recall_at_k", "avg_precision_at_k", "avg_mrr"))
    return {"baseline_run_id": str(base.evaluation_run_id), "delta": deltas,
            "blocked": unsafe_increase or quality_regression,
            "reason": "safety_or_retrieval_regression" if unsafe_increase or quality_regression else None,
            "decision": "REJECT" if unsafe_increase or quality_regression else "HUMAN_APPROVAL_REQUIRED"}