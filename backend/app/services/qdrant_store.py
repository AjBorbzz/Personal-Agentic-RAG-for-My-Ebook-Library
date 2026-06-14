from typing import Any 
from uuid import uuid5, NAMESPACE_URL 

from qdrant_client import QdrantClient 
from qdrant_client.models import Distance, PointStruct, VectorParams 

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

def upsert_chunks(collection_name: str, points: list[PointStruct],) -> int:
    if not points:
        return 0 
    
    client.upsert(
        collection_name=collection_name,
        points=points,
    )

    return len(points)

def search_similar_chunks(
            collection_name: str,
            query_vector: list[float],
            limit: int = 5,
        ) -> list[dict[str, Any]]: 
    result = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=limit,
        with_payload=True,
    )
    matches: list[dict[str, Any]] = []
    for point in result.points:
        matches.append(
            {
                "id": str(point.id),
                "score": point.score,
                "payload": point.payload or {}
            }
        )
    return matches 

def get_collection_info(collection_name: str) -> dict[str, Any]:
    info = client.get_collection(collection_name=collection_name)
    return info.model_dump() 

