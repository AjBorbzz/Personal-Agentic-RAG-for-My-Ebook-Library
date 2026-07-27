from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.document import Document
from app.schemas.document import (
    DocumentCreate,
    DocumentDeprecateRequest,
    DocumentResponse,
    DocumentUpdate,
)

from datetime import datetime, timezone

from app.schemas.document_enrichment import (
    DocumentEnrichmentRequest,
    DocumentEnrichmentResponse,
)

from app.schemas.metadata_review import (
    MetadataCandidateResponse,
    MetadataReviewRequest,
    MetadataReviewResponse,
    MetadataReviewStateResponse,
    StageMetadataCandidateRequest,
)
from app.services.book_metadata_enrichment import (
    build_metadata_updates,
    generate_metadata_candidate,
)
from app.schemas.document_enrichment import EnrichedBookMetadata

from app.core.config import settings
from app.schemas.document_qdrant_sync import (
    DocumentQdrantSyncRequest,
    DocumentQdrantSyncResponse,
)
from app.services.document_qdrant_sync import (
    sync_document_metadata_to_qdrant,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse)
def create_document(payload: DocumentCreate, db: Session = Depends(get_db)):
    existing = db.get(Document, payload.document_id)

    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Document already exists: {payload.document_id}",
        )

    if payload.content_hash:
        existing_hash = db.scalar(
            select(Document).where(Document.content_hash == payload.content_hash)
        )

        if existing_hash:
            raise HTTPException(
                status_code=409,
                detail=f"Document with same content_hash already exists: {existing_hash.document_id}",
            )

    document = Document(**payload.model_dump())
    db.add(document)
    db.commit()
    db.refresh(document)

    return document


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    db: Session = Depends(get_db),
    tool_name: str | None = Query(default=None),
    version_major: int | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    is_deprecated: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
):
    statement = select(Document).order_by(Document.ingested_at.desc())

    if tool_name:
        statement = statement.where(Document.tool_name == tool_name)

    if version_major is not None:
        statement = statement.where(Document.version_major == version_major)

    if is_active is not None:
        statement = statement.where(Document.is_active == is_active)

    if is_deprecated is not None:
        statement = statement.where(Document.is_deprecated == is_deprecated)

    statement = statement.limit(limit)

    return list(db.scalars(statement).all())


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str, db: Session = Depends(get_db)):
    document = db.get(Document, document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    return document


@router.patch("/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: str,
    payload: DocumentUpdate,
    db: Session = Depends(get_db),
):
    document = db.get(Document, document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(document, field, value)

    db.commit()
    db.refresh(document)

    return document


@router.patch("/{document_id}/deprecate", response_model=DocumentResponse)
def deprecate_document(
    document_id: str,
    payload: DocumentDeprecateRequest,
    db: Session = Depends(get_db),
):
    document = db.get(Document, document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    document.is_active = False
    document.is_deprecated = True
    document.superseded_by_document_id = payload.superseded_by_document_id

    if payload.notes:
        document.notes = payload.notes

    db.commit()
    db.refresh(document)

    return document


@router.post(
    "/{document_id}/enrich",
    response_model=DocumentEnrichmentResponse,
)
async def enrich_document_metadata(
    document_id: str,
    request: DocumentEnrichmentRequest,
    db: Session = Depends(get_db),
):
    document = db.get(Document, document_id)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    warnings: list[str] = []

    try:
        (
            candidate,
            source_characters_used,
            source_was_truncated,
        ) = await generate_metadata_candidate(
            document=document,
            maximum_source_characters=(
                request.max_source_characters
            ),
        )

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except (ValueError, TypeError) as error:
        raise HTTPException(
            status_code=502,
            detail=(
                "Metadata enrichment returned invalid output: "
                f"{error}"
            ),
        ) from error

    proposed_updates = build_metadata_updates(
        document=document,
        candidate=candidate,
        overwrite_existing=request.overwrite_existing,
    )

    if source_was_truncated:
        warnings.append(
            "The book was larger than the enrichment limit. "
            "The beginning, middle, and end were sampled."
        )

    if not proposed_updates:
        warnings.append(
            "No missing metadata fields could be filled from "
            "the model response."
        )

    updated_fields: list[str] = []
    applied = False

    if not request.dry_run and proposed_updates:
        try:
            for field_name, value in proposed_updates.items():
                setattr(document, field_name, value)
                updated_fields.append(field_name)

            document.metadata_source = "llm"
            document.metadata_confidence = (
                candidate.metadata_confidence
            )
            document.metadata_reviewed = False
            document.enriched_at = datetime.now(timezone.utc)

            updated_fields.extend(
                [
                    "metadata_source",
                    "metadata_confidence",
                    "metadata_reviewed",
                    "enriched_at",
                ]
            )

            db.commit()
            db.refresh(document)

            applied = True

        except Exception:
            db.rollback()
            raise

    return DocumentEnrichmentResponse(
        document_id=document.document_id,
        dry_run=request.dry_run,
        applied=applied,
        overwrite_existing=request.overwrite_existing,
        source_characters_used=source_characters_used,
        source_was_truncated=source_was_truncated,
        candidate=candidate,
        proposed_updates=proposed_updates,
        updated_fields=updated_fields,
        warnings=warnings,
        document=document,
    )


@router.post("/{document_id}/metadata-candidate",response_model=MetadataCandidateResponse,)
async def stage_metadata_candidate(
    document_id: str,
    request: StageMetadataCandidateRequest,
    db: Session = Depends(get_db),
):
    document = db.get(Document, document_id)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    warnings: list[str] = []

    try:
        (
            candidate,
            source_characters_used,
            source_was_truncated,
        ) = await generate_metadata_candidate(
            document=document,
            maximum_source_characters=(
                request.max_source_characters
            ),
        )

        proposed_updates = build_metadata_updates(
            document=document,
            candidate=candidate,
            overwrite_existing=request.overwrite_existing,
        )

        if source_was_truncated:
            warnings.append(
                "The beginning, middle, and end of the "
                "document were sampled."
            )

        if not proposed_updates:
            warnings.append(
                "No missing or overwrite-eligible fields "
                "were found."
            )

        document.metadata_candidate = candidate.model_dump()
        document.metadata_proposed_updates = proposed_updates
        document.metadata_review_status = "pending"
        document.metadata_review_notes = None
        document.metadata_reviewed = False
        document.metadata_reviewed_at = None

        document.metadata_source = "llm"
        document.metadata_confidence = (
            candidate.metadata_confidence
        )
        document.enriched_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(document)

        return MetadataCandidateResponse(
            document_id=document.document_id,
            review_status=document.metadata_review_status,
            candidate=candidate,
            proposed_updates=proposed_updates,
            source_characters_used=source_characters_used,
            source_was_truncated=source_was_truncated,
            warnings=warnings,
            document=document,
        )

    except FileNotFoundError as error:
        db.rollback()

        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except (ValueError, TypeError) as error:
        db.rollback()

        raise HTTPException(
            status_code=502,
            detail=(
                "The metadata model returned invalid output: "
                f"{error}"
            ),
        ) from error

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to stage metadata candidate: "
                f"{type(error).__name__}: {error}"
            ),
        ) from error


@router.get(
    "/{document_id}/metadata-review",
    response_model=MetadataReviewStateResponse,
)
def get_metadata_review(
    document_id: str,
    db: Session = Depends(get_db),
):
    document = db.get(Document, document_id)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    candidate = None

    if document.metadata_candidate:
        candidate = EnrichedBookMetadata.model_validate(
            document.metadata_candidate
        )

    return MetadataReviewStateResponse(
        document_id=document.document_id,
        review_status=document.metadata_review_status,
        candidate=candidate,
        proposed_updates=(
            document.metadata_proposed_updates or {}
        ),
        review_notes=document.metadata_review_notes,
        metadata_confidence=document.metadata_confidence,
        enriched_at=document.enriched_at,
        reviewed_at=document.metadata_reviewed_at,
        document=document,
    )


@router.patch(
    "/{document_id}/metadata-review",
    response_model=MetadataReviewResponse,
)
def review_document_metadata(
    document_id: str,
    request: MetadataReviewRequest,
    db: Session = Depends(get_db),
):
    document = db.get(Document, document_id)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    if not document.metadata_candidate:
        raise HTTPException(
            status_code=409,
            detail=(
                "This document does not have a staged "
                "metadata candidate."
            ),
        )

    try:
        if request.edited_candidate is not None:
            candidate = request.edited_candidate
        else:
            candidate = EnrichedBookMetadata.model_validate(
                document.metadata_candidate
            )

        now = datetime.now(timezone.utc)

        if request.action == "reject":
            document.metadata_review_status = "rejected"
            document.metadata_review_notes = (
                request.review_notes
            )
            document.metadata_reviewed = False
            document.metadata_reviewed_at = now

            db.commit()
            db.refresh(document)

            return MetadataReviewResponse(
                    document_id=document.document_id,
                    action="reject",
                    review_status="rejected",
                    applied=False,
                    updated_fields=[],
                    candidate=candidate,
                    proposed_updates=(
                        document.metadata_proposed_updates or {}
                    ),
                    qdrant_sync=None,
                    warnings=[],
                    document=document,
                )

        proposed_updates = build_metadata_updates(
            document=document,
            candidate=candidate,
            overwrite_existing=request.overwrite_existing,
        )

        updated_fields: list[str] = []

        for field_name, value in proposed_updates.items():
            setattr(document, field_name, value)
            updated_fields.append(field_name)

        document.metadata_candidate = candidate.model_dump()
        document.metadata_proposed_updates = proposed_updates
        document.metadata_review_status = "approved"
        document.metadata_review_notes = request.review_notes
        document.metadata_reviewed = True
        document.metadata_reviewed_at = now

        document.metadata_source = "llm_reviewed"
        document.metadata_confidence = (
            candidate.metadata_confidence
        )
        document.enriched_at = now

        db.commit()
        db.refresh(document)

        qdrant_sync = None
        warnings: list[str] = []

        if request.sync_to_qdrant:
            try:
                sync_result = sync_document_metadata_to_qdrant(
                    document=document,
                    collection_name=settings.default_collection,
                    create_payload_indexes=True,
                )

                qdrant_sync = DocumentQdrantSyncResponse(
                    **sync_result
                )

            except Exception as sync_error:
                warnings.append(
                    "Metadata was approved in PostgreSQL, but "
                    "Qdrant synchronization failed: "
                    f"{type(sync_error).__name__}: {sync_error}"
                )

        return MetadataReviewResponse(
            document_id=document.document_id,
            action="approve",
            review_status="approved",
            applied=bool(updated_fields),
            updated_fields=updated_fields,
            candidate=candidate,
            proposed_updates=proposed_updates,
            qdrant_sync=qdrant_sync,
            warnings=warnings,
            document=document,
        )

    except ValueError as error:
        db.rollback()

        raise HTTPException(
            status_code=422,
            detail=f"Invalid metadata candidate: {error}",
        ) from error

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Metadata review failed: "
                f"{type(error).__name__}: {error}"
            ),
        ) from error


@router.post(
    "/{document_id}/sync-qdrant",
    response_model=DocumentQdrantSyncResponse,
)
def sync_document_qdrant_metadata(
    document_id: str,
    request: DocumentQdrantSyncRequest,
    db: Session = Depends(get_db),
):
    document = db.get(Document, document_id)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    if (
        not request.force
        and (
            document.metadata_review_status != "approved"
            or not document.metadata_reviewed
        )
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Only approved metadata can be synchronized "
                "to Qdrant. Use force=true only for an "
                "intentional administrative synchronization."
            ),
        )

    try:
        result = sync_document_metadata_to_qdrant(
            document=document,
            collection_name=settings.default_collection,
            create_payload_indexes=(
                request.create_payload_indexes
            ),
        )

        return DocumentQdrantSyncResponse(
            **result
        )

    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to synchronize metadata to Qdrant: "
                f"{type(error).__name__}: {error}"
            ),
        ) from error