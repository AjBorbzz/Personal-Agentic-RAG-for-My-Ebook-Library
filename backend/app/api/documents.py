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
from app.services.book_metadata_enrichment import (
    build_metadata_updates,
    generate_metadata_candidate,
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