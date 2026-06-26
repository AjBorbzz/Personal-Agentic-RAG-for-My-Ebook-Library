from typing import Any
from uuid import uuid5, NAMESPACE_URL

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchAny,
    PointStruct,
    VectorParams,
    MatchValue
)

from app.core.config import settings


client = QdrantClient(url=settings.qdrant_url)


def ensure_collection(collection_name: str, vector_size: int) -> None:
    """
    Create the Qdrant collection if it does not exist.
    Vector size must match the embedding model output dimension.
    """
    if client.collection_exists(collection_name=collection_name):
        return

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE,
        ),
    )


def make_point_id(document_id: str, chunk_index: int) -> str:
    """
    Qdrant point IDs can be UUID strings.
    This creates a deterministic UUID for each document chunk.
    """
    return str(uuid5(NAMESPACE_URL, f"{document_id}:{chunk_index}"))


def upsert_chunks(
    collection_name: str,
    points: list[PointStruct],
) -> int:
    if not points:
        return 0

    client.upsert(
        collection_name=collection_name,
        points=points,
    )

    return len(points)


def _build_domain_filter(domains: list[str] | None) -> Filter | None:
    if not domains:
        return None

    cleaned_domains = [
        domain for domain in domains
        if domain and domain != "general"
    ]

    if not cleaned_domains:
        return None

    return Filter(
        must=[
            FieldCondition(
                key="domains",
                match=MatchAny(any=cleaned_domains),
            )
        ]
    )


def search_similar_chunks(
    collection_name: str,
    query_vector: list[float],
    limit: int = 5,
    domains: list[str] | None = None,
    active_only: bool = True,
    include_deprecated: bool = False,
    tool_name: str | None = None,
    tool_version: str | None = None,
    version_major: int | None = None,
    version_minor: int | None = None,
    source_type: str | None = None,
    publication_year: int | None = None,
) -> list[dict[str, Any]]:
    
    must_conditions = []

    query_filter = _build_domain_filter(domains)

    if active_only:
        must_conditions.append(
            FieldCondition(
                key="is_active",
                match=MatchValue(value=True),
            )
        )

    if not include_deprecated:
        must_conditions.append(
            FieldCondition(
                key="is_deprecated",
                match=MatchValue(value=False),
            )
        )

    if tool_name:
        must_conditions.append(
            FieldCondition(
                key="tool_name",
                match=MatchValue(value=tool_name),
            )
        )

    if tool_version:
        must_conditions.append(
            FieldCondition(
                key="tool_version",
                match=MatchValue(value=tool_version),
            )
        )

    if version_major is not None:
        must_conditions.append(
            FieldCondition(
                key="version_major",
                match=MatchValue(value=version_major),
            )
        )

    if version_minor is not None:
        must_conditions.append(
            FieldCondition(
                key="version_minor",
                match=MatchValue(value=version_minor),
            )
        )

    if source_type:
        must_conditions.append(
            FieldCondition(
                key="source_type",
                match=MatchValue(value=source_type),
            )
        )

    if publication_year is not None:
        must_conditions.append(
            FieldCondition(
                key="publication_year",
                match=MatchValue(value=publication_year),
            )
        )

    result = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        query_filter=query_filter,
        limit=limit,
        with_payload=True,
    )

    matches: list[dict[str, Any]] = []

    for point in result.points:
        matches.append(
            {
                "id": str(point.id),
                "score": point.score,
                "payload": point.payload or {},
            }
        )

    return matches


def get_collection_info(collection_name: str) -> dict[str, Any]:
    info = client.get_collection(collection_name=collection_name)
    return info.model_dump()