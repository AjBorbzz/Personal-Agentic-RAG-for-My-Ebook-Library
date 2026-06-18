from app.agents.router_state import RouterDecision
from app.core.domains import normalize_domain
from app.retrieval.source_quality import has_reasonable_sources
from app.services.domain_classifier import classify_domains
from app.services.intent_classifier import classify_intent
from app.services.ollama import generate_embedding
from app.services.qdrant_store import search_similar_chunks
from app.services.query_rewriter import rewrite_query_for_retrieval


def _clean_domains(domains: list[str] | None) -> list[str]:
    if not domains:
        return []

    cleaned = [
        normalize_domain(domain)
        for domain in domains
    ]

    cleaned = [
        domain
        for domain in cleaned
        if domain
    ]

    return list(dict.fromkeys(cleaned))


def _should_use_domain_filter(domains: list[str]) -> bool:
    return bool(domains and domains != ["general"])


def _strategy_for_intent(intent: str) -> str:
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


async def route_and_retrieve(
                                question: str,
                                collection_name: str,
                                limit: int,
                                manual_domains: list[str] | None = None,
                                auto_detect_domains: bool = True,
                            ) -> RouterDecision:
    intent_result = classify_intent(question)
    domain_result = classify_domains(question)

    detected_domains = domain_result.domains

    if manual_domains:
        search_domains = _clean_domains(manual_domains)
    elif auto_detect_domains:
        search_domains = detected_domains
    else:
        search_domains = []

    retrieval_strategy = _strategy_for_intent(intent_result.intent)
    domain_filter_used = _should_use_domain_filter(search_domains)

    decision = RouterDecision(
        question=question,
        intent=intent_result.intent,
        detected_domains=detected_domains,
        search_domains=search_domains,
        retrieval_strategy=retrieval_strategy,
        domain_filter_used=domain_filter_used,
    )

    query_vector = await generate_embedding(question)

    matches = search_similar_chunks(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=limit,
        domains=search_domains,
    )

    decision.retrieval_attempts += 1
    decision.matches = matches

    if matches and has_reasonable_sources(matches):
        decision.notes.append("Initial retrieval returned reasonable sources.")
        return decision

    decision.notes.append("Initial retrieval was weak or empty.")
    decision.should_rewrite_query = True

    rewritten_query = await rewrite_query_for_retrieval(
        question=question,
        domains=search_domains or detected_domains,
    )

    decision.rewritten_query = rewritten_query

    rewritten_vector = await generate_embedding(rewritten_query)

    rewritten_matches = search_similar_chunks(
        collection_name=collection_name,
        query_vector=rewritten_vector,
        limit=limit,
        domains=search_domains,
    )

    decision.retrieval_attempts += 1

    if rewritten_matches and has_reasonable_sources(rewritten_matches):
        decision.matches = rewritten_matches
        decision.notes.append("Rewritten query improved retrieval.")
        return decision

    decision.notes.append("Rewritten query retrieval was still weak or empty.")

    if decision.domain_filter_used:
        fallback_matches = search_similar_chunks(
            collection_name=collection_name,
            query_vector=rewritten_vector,
            limit=limit,
            domains=None,
        )

        decision.retrieval_attempts += 1
        decision.fallback_used = True
        decision.domain_filter_used = False

        if fallback_matches:
            decision.matches = fallback_matches
            decision.notes.append("Fallback to full collection was used.")
            return decision

    decision.notes.append("No strong retrieval result found.")
    return decision