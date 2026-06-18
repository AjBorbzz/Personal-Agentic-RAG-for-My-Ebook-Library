from fastapi import APIRouter
from pydantic import BaseModel

from app.core.domains import normalize_domain
from app.services.domain_classifier import classify_domains
from app.services.intent_classifier import classify_intent

router = APIRouter()


class RouterPreviewRequest(BaseModel):
    question: str
    domains: list[str] | None = None
    auto_detect_domains: bool = True


class RouterPreviewResponse(BaseModel):
    question: str
    intent: str
    intent_score: int
    detected_domains: list[str]
    search_domains: list[str]
    retrieval_strategy: str
    domain_filter_used: bool
    intent_scores: dict[str, int]
    domain_scores: dict[str, int]


def strategy_for_intent(intent: str) -> str:
    if intent in {
        "architecture_design",
        "how_to_guide",
        "learning_path",
        "project_idea",
    }:
        return "multi_source_synthesis"

    if intent in {
        "code_help",
        "troubleshooting",
    }:
        return "precise_retrieval"

    if intent == "comparison":
        return "comparative_retrieval"

    return "standard_rag"


def clean_domains(domains: list[str] | None) -> list[str]:
    if not domains:
        return []

    normalized = [
        normalize_domain(domain)
        for domain in domains
    ]

    return list(dict.fromkeys(normalized))


@router.post("/router-preview", response_model=RouterPreviewResponse)
def router_preview(request: RouterPreviewRequest):
    intent_result = classify_intent(request.question)
    domain_result = classify_domains(request.question)

    detected_domains = domain_result.domains

    if request.domains:
        search_domains = clean_domains(request.domains)
    elif request.auto_detect_domains:
        search_domains = detected_domains
    else:
        search_domains = []

    retrieval_strategy = strategy_for_intent(intent_result.intent)

    domain_filter_used = bool(
        search_domains and search_domains != ["general"]
    )

    return RouterPreviewResponse(
        question=request.question,
        intent=intent_result.intent,
        intent_score=intent_result.score,
        detected_domains=detected_domains,
        search_domains=search_domains,
        retrieval_strategy=retrieval_strategy,
        domain_filter_used=domain_filter_used,
        intent_scores=intent_result.scores,
        domain_scores=domain_result.scores,
    )