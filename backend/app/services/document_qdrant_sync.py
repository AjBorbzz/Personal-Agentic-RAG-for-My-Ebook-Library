from datetime import datetime, timezone
from typing import Any

from app.models.document import Document
from app.services.qdrant_store import (
    count_document_chunks,
    ensure_document_metadata_indexes,
    update_document_payload,
)


def _isoformat(value: datetime | None) -> str | None:
    if value is None:
        return None

    return value.isoformat()


def build_document_qdrant_payload(
    document: Document,
    synced_at: datetime,
) -> dict[str, Any]:
    """
    Build the trusted document-level metadata copied to every
    Qdrant chunk.

    Pending metadata candidates are intentionally excluded.
    """

    return {
        # Core document metadata
        "document_id": document.document_id,
        "filename": document.filename,
        "title": document.title,
        "author": document.author,
        "subtitle": document.subtitle,
        "publisher": document.publisher,
        "edition": document.edition,
        "isbn_10": document.isbn_10,
        "isbn_13": document.isbn_13,
        "language": document.language,
        "description": document.description,

        # Domain and classification metadata
        "primary_domain": document.primary_domain,
        "domains": document.domains or [],
        "difficulty_level": document.difficulty_level,
        "topics": document.topics or [],
        "technologies": document.technologies or [],
        "tags": document.tags or [],
        "prerequisite_skills": (
            document.prerequisite_skills or []
        ),

        # Source and version metadata
        "source_type": document.source_type,
        "tool_name": document.tool_name,
        "tool_version": document.tool_version,
        "version_major": document.version_major,
        "version_minor": document.version_minor,
        "publication_year": document.publication_year,
        "publication_date": (
            document.publication_date.isoformat()
            if document.publication_date
            else None
        ),

        # Document lifecycle
        "is_active": document.is_active,
        "is_deprecated": document.is_deprecated,
        "superseded_by_document_id": (
            document.superseded_by_document_id
        ),

        # Metadata trust information
        "metadata_source": document.metadata_source,
        "metadata_confidence": (
            document.metadata_confidence
        ),
        "metadata_reviewed": document.metadata_reviewed,
        "metadata_review_status": (
            document.metadata_review_status
        ),
        "metadata_reviewed_at": _isoformat(
            document.metadata_reviewed_at
        ),
        "enriched_at": _isoformat(document.enriched_at),

        # Synchronization metadata
        "document_metadata_schema_version": 1,
        "document_metadata_synced_at": (
            synced_at.isoformat()
        ),
    }


def sync_document_metadata_to_qdrant(
    *,
    document: Document,
    collection_name: str,
    create_payload_indexes: bool = True,
) -> dict[str, Any]:
    matched_points = count_document_chunks(
        collection_name=collection_name,
        document_id=document.document_id,
    )

    if matched_points == 0:
        raise ValueError(
            "No Qdrant chunks were found for document "
            f"{document.document_id}. Index the document first."
        )

    created_indexes: list[str] = []

    if create_payload_indexes:
        created_indexes = ensure_document_metadata_indexes(
            collection_name=collection_name
        )

    synced_at = datetime.now(timezone.utc)

    payload = build_document_qdrant_payload(
        document=document,
        synced_at=synced_at,
    )

    update_result = update_document_payload(
        collection_name=collection_name,
        document_id=document.document_id,
        payload=payload,
    )

    return {
        "document_id": document.document_id,
        "collection_name": collection_name,
        "matched_points": update_result["matched_points"],
        "payload_keys_set": (
            update_result["payload_keys_set"]
        ),
        "payload_keys_deleted": (
            update_result["payload_keys_deleted"]
        ),
        "created_indexes": created_indexes,
        "metadata_review_status": (
            document.metadata_review_status
        ),
        "metadata_reviewed": document.metadata_reviewed,
        "synced_at": synced_at,
        "warnings": [],
    }