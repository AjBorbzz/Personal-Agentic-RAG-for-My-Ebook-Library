from dataclasses import dataclass, field
from typing import Any


@dataclass
class RouterDecision:
    question: str
    intent: str
    detected_domains: list[str]
    search_domains: list[str]
    retrieval_strategy: str

    should_rewrite_query: bool = False
    rewritten_query: str | None = None

    domain_filter_used: bool = False
    fallback_used: bool = False
    retrieval_attempts: int = 0

    notes: list[str] = field(default_factory=list)
    matches: list[dict[str, Any]] = field(default_factory=list)