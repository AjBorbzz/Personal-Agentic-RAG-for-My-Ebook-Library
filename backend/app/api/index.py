import json
import time 

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel 
from qdrant_client.models import PointStruct

from app.core.config import settings 
from app.services.ollama import generate_embedding 
from app.services.qdrant_store import (
    ensure_collection,
    get_collection_info,
    make_point_id, 
    upsert_chunks
)

from app.services.domain_classifier import classify_domains
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.document import Document


router = APIRouter() 

class IndexDocumentResponse(BaseModel):
    document_id : str 
    collection_name: str 
    filename: str | None 
    title: str | None 
    primary_domain: str
    domains: list[str]
    chunk_count: int 
    indexed_count: int 
    embedding_dimension: int 
    elapsed_seconds: float 
    elapsed_ms: float 
    source_type: str | None = None
    tool_name: str | None = None
    tool_version: str | None = None
    version_major: int | None = None
    version_minor: int | None = None
    publication_year: int | None = None
    is_active: bool
    is_deprecated: bool
    content_hash: str | None = None

class CollectionInfoResponse(BaseModel):
    collection_name: str 
    info:dict 

@router.post("/index/{document_id}", response_model=IndexDocumentResponse)
async def index_document(document_id: str, db: Session = Depends(get_db)):
    start_time = time.perf_counter() 
    chunks_path = settings.chunks_dir / f"{document_id}.json"
    if not chunks_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No chunks file found for document_id: {document_id}"
        )
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(
            status_code=404,
            detail=(
                "Document registry record not found. "
                "Re-ingest this document so it can be registered before indexing."
            ),
        )
    registry_metadata = {
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
        "content_hash": document.content_hash,
        "is_active": document.is_active,
        "is_deprecated": document.is_deprecated,
        "superseded_by_document_id": document.superseded_by_document_id,
        "ingested_at": document.ingested_at.isoformat() if document.ingested_at else None,
    }

    try:
        payload = json.loads(chunks_path.read_text(encoding="utf-8"))
        chunks = payload.get("chunks", [])
        if not chunks:
            raise HTTPException(
                status_code=422,
                detail="Chunks file exists but contains no chunks."
            )

        classification_text = "\n".join(
                        [
                            payload.get("title") or "",
                            payload.get("author") or "",
                            payload.get("filename") or "",
                            chunks[0].get("text", "")[:6000],
                        ]
                    )

        classification = classify_domains(classification_text)

        primary_domain = payload.get("primary_domain") or classification.primary_domain
        domains = payload.get("domains") or classification.domains
        domain_scores = payload.get("domain_scores") or classification.scores
        first_embedding = await generate_embedding(chunks[0]["text"])
        embedding_dimension = len(first_embedding)

        collection_name = settings.default_collection 
        ensure_collection(collection_name, embedding_dimension)

        points: list[PointStruct] = []

        for chunk in chunks:
            chunk_index = int(chunk["chunk_index"])
            chunk_text = chunk["text"]

            if chunk_index == 0:
                vector = first_embedding 

            else: 
                vector = await generate_embedding(chunk_text)

            point_payload = {
                                "document_id": document_id,
                                "filename": payload.get("filename"),
                                "title": payload.get("title"),
                                "author": payload.get("author"),
                                "file_type": payload.get("file_type"),
                                "primary_domain": primary_domain,
                                "domains": domains,
                                "domain_scores": domain_scores,

                                **registry_metadata,

                                "chunk_index": chunk_index,
                                "page_number": chunk.get("page_number"),
                                "page_start": chunk.get("page_start"),
                                "page_end": chunk.get("page_end"),
                                "page_numbers": chunk.get("page_numbers"),
                                "char_start": chunk.get("char_start"),
                                "char_end": chunk.get("char_end"),

                                "text": chunk_text,
                                "chunk_text": chunk_text,
                            }
            points.append(
                PointStruct(
                    id=make_point_id(document_id, chunk_index),
                    vector=vector,
                    payload=point_payload,
                )
            )

        indexed_count = upsert_chunks(collection_name, points)
        elapsed_seconds = time.perf_counter() - start_time 

        return IndexDocumentResponse(
            document_id=document_id,
            collection_name=collection_name,
            filename=payload.get("filename"),
            title=payload.get("title"),
            chunk_count=len(chunks),
            indexed_count=indexed_count,
            primary_domain=primary_domain,
            domains=domains,
            embedding_dimension=embedding_dimension,
            elapsed_seconds=round(elapsed_seconds, 3),
            elapsed_ms=round(elapsed_seconds * 1000, 2),
            source_type=document.source_type,
            tool_name=document.tool_name,
            tool_version=document.tool_version,
            version_major=document.version_major,
            version_minor=document.version_minor,
            publication_year=document.publication_year,
            is_active=document.is_active,
            is_deprecated=document.is_deprecated,
            content_hash=document.content_hash,
        )
    except HTTPException:
        raise 
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"indexing failed: {error}"
        )

@router.get("/collections/{collection_name}", response_model=CollectionInfoResponse)
def collection_info(collection_name: str):
    try:
        return CollectionInfoResponse(
            collection_name=collection_name,
            info=get_collection_info(collection_name)
        )
    except Exception as error:
        raise HTTPException(
            status_code=404,
            detail=f"Collection not found or unavailable: {error}"
        )