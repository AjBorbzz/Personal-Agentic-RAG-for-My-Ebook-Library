from datetime import datetime, timezone
from typing import Any

from app.models.book_curation import BookCuration
from app.models.book_relationship import BookRelationship
from app.models.document import Document
from app.services.book_ranking import (
    calculate_book_ranking,
)
from app.services.qdrant_store import (
    ensure_document_metadata_indexes,
    update_document_payload,
)


def sync_book_ranking_to_qdrant(
                                    *,
                                    document: Document,
                                    curation: BookCuration,
                                    relationships: list[BookRelationship],
                                    collection_name: str,
                                ) -> dict[str, Any]:
    if curation.evaluation_status != "approved":
        raise ValueError(
            "Only approved curator evaluations "
            "can be synchronized to Qdrant."
        )

    ranking = calculate_book_ranking(
        document=document,
        curation=curation,
        relationships=relationships,
        purpose="general",
    )

    synced_at = datetime.now(timezone.utc)

    payload = {
        "curation_status": (
            curation.evaluation_status
        ),
        "curator_overall_score": (
            curation.overall_score
        ),
        "curator_rank_score": (
            ranking.ranking_score
        ),
        "curator_technical_depth_score": (
            curation.technical_depth_score
        ),
        "curator_practicality_score": (
            curation.practicality_score
        ),
        "curator_freshness_score": (
            curation.freshness_score
        ),
        "curator_authority_score": (
            curation.authority_score
        ),
        "curator_clarity_score": (
            curation.clarity_score
        ),
        "curator_outdated_risk_score": (
            curation.outdated_risk_score
        ),
        "curator_audience_level": (
            curation.audience_level
        ),
        "curator_recommended_role": (
            curation.recommended_role
        ),
        "curator_library_priority": (
            curation.library_priority
        ),
        "curator_confidence": (
            curation.confidence
        ),
        "curator_ranking_version": 1,
        "curator_ranking_synced_at": (
            synced_at.isoformat()
        ),
    }

    ensure_document_metadata_indexes(
        collection_name=collection_name
    )

    update_result = update_document_payload(
        collection_name=collection_name,
        document_id=document.document_id,
        payload=payload,
    )

    return {
        "document_id": document.document_id,
        "collection_name": collection_name,
        "matched_points": (
            update_result["matched_points"]
        ),
        "payload_keys_set": (
            update_result["payload_keys_set"]
        ),
        "payload_keys_deleted": (
            update_result["payload_keys_deleted"]
        ),
        "ranking_score": ranking.ranking_score,
        "ranking_purpose": "general",
        "synced_at": synced_at,
        "warnings": [],
    }