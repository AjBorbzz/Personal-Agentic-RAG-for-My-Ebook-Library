from typing import Any

def has_reasonable_sources(
        matches: list[dict[str, Any]],
        minimum_score: float = 0.35,
) -> bool:
    """
    Basic source quality gate.
    Similarity scores vary by embedding model and data.
    Tune this later after testing
    """

    if not matches:
        return False 
    
    best_score = matches[0].get("score", 0)
    return best_score >= minimum_score