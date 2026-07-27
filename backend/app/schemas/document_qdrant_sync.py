from datetime import datetime

from pydantic import BaseModel, Field


class DocumentQdrantSyncRequest(BaseModel):
    force: bool = False
    create_payload_indexes: bool = True


class DocumentQdrantSyncResponse(BaseModel):
    document_id: str
    collection_name: str

    matched_points: int
    payload_keys_set: list[str]
    payload_keys_deleted: list[str]
    created_indexes: list[str]

    metadata_review_status: str
    metadata_reviewed: bool

    synced_at: datetime
    warnings: list[str] = Field(default_factory=list)