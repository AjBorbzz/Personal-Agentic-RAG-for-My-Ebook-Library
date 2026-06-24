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