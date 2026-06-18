from dataclasses import dataclass 

from app.core.intents import VALID_INTENTS 


@dataclass
class IntentClassification:
    intent: str 
    score: int 
    scores: dict[str, int]

INTENT_KEYWORDS: dict[str, list[str]] = {
    "concept_explanation": [
        "what is", "explain", "define", "meaning", "concept", "overview",
        "introduction", "fundamentals", "principles",
    ],
    "how_to_guide": [
        "how do i", "how to", "steps", "guide", "walkthrough",
        "implement", "setup", "configure", "build",
    ],
    "architecture_design": [
        "architecture", "design", "system design", "scalable", "reliable",
        "fault tolerant", "high availability", "production-grade",
        "tradeoff", "component", "workflow",
    ],
    "code_help": [
        "code", "function", "class", "script", "bug", "refactor",
        "python", "fastapi", "typescript", "javascript", "error",
        "stack trace",
    ],
    "comparison": [
        "compare", "difference", "versus", "vs", "better", "pros and cons",
        "trade-off", "tradeoff",
    ],
    "troubleshooting": [
        "not working", "failed", "error", "issue", "connection refused",
        "null", "bug", "fix", "debug", "why is", "inaccurate",
    ],
    "learning_path": [
        "roadmap", "learning path", "study plan", "curriculum",
        "learn", "master", "become better", "upskill",
    ],
    "project_idea": [
        "project", "portfolio", "build project", "project idea",
        "github", "resume", "case study", "proof of work",
    ],
}


def classify_intent(text: str) -> IntentClassification:
    lowered = text.lower()
    scores: dict[str, int] = {}

    for intent, keywords in INTENT_KEYWORDS.items():
        score = 0

        for keyword in keywords:
            if keyword in lowered:
                score += 1 

        scores[intent] = score 

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)

    best_intent, best_score = ranked[0]

    if best_score <= 0 or best_intent not in VALID_INTENTS:
        return IntentClassification(
            intent="general_question",
            score=0,
            scores=scores,
        )
    
    return IntentClassification(
        intent=best_intent,
        score=best_score,
        scores=scores
    )