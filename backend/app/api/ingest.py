import json
import shutil
import time
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.file_hash import calculate_file_sha256
from app.db.session import get_db
from app.ingestion.chunker import chunk_text
from app.ingestion.parsers import extract_document
from app.models.document import Document
from app.services.domain_classifier import classify_domains

router = APIRouter()

SUPPORTED_EXTENSIONS = {".pdf", ".epub", ".txt"}


class IngestResponse(BaseModel):
    document_id: str
    filename: str
    saved_path: str
    file_type: str
    title: str | None
    author: str | None
    page_count: int | None
    text_characters: int
    chunk_count: int
    primary_domain: str
    domains: list[str]
    parsed_output_path: str
    chunks_output_path: str
    elapsed_seconds: float
    elapsed_ms: float
    content_hash: str
    registry_created: bool = True


def _safe_filename(filename: str) -> str:
    return Path(filename).name.replace(" ", "_")


@router.post("/ingest", response_model=IngestResponse)
async def ingest_ebook(
    file: UploadFile = File(...),
    source_type: str | None = Form(default=None),
    tool_name: str | None = Form(default=None),
    tool_version: str | None = Form(default=None),
    version_major: int | None = Form(default=None),
    version_minor: int | None = Form(default=None),
    publication_year: int | None = Form(default=None),
    is_active: bool = Form(default=True),
    is_deprecated: bool = Form(default=False),
    notes: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    start_time = time.perf_counter()

    original_filename = file.filename or "uploaded_file"
    safe_filename = _safe_filename(original_filename)
    suffix = Path(safe_filename).suffix.lower()

    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{suffix}'. "
                f"Supported: {sorted(SUPPORTED_EXTENSIONS)}"
            ),
        )

    document_id = str(uuid4())
    upload_path = settings.uploads_dir / f"{document_id}_{safe_filename}"

    try:
        settings.uploads_dir.mkdir(parents=True, exist_ok=True)
        settings.parsed_dir.mkdir(parents=True, exist_ok=True)
        settings.chunks_dir.mkdir(parents=True, exist_ok=True)

        with upload_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        content_hash = calculate_file_sha256(upload_path)

        existing_document = db.scalar(
            select(Document).where(Document.content_hash == content_hash)
        )

        if existing_document:
            upload_path.unlink(missing_ok=True)

            raise HTTPException(
                status_code=409,
                detail={
                    "message": "This file has already been ingested.",
                    "document_id": existing_document.document_id,
                    "filename": existing_document.filename,
                    "title": existing_document.title,
                    "content_hash": existing_document.content_hash,
                },
            )

        extracted = extract_document(upload_path)

        if not extracted.text.strip():
            raise HTTPException(
                status_code=422,
                detail=(
                    "No readable text was extracted. "
                    "This may be a scanned PDF or image-only ebook. "
                    "OCR will be added later."
                ),
            )

        classification_text = "\n".join(
            [
                extracted.title or "",
                extracted.author or "",
                extracted.file_type or "",
                extracted.text[:6000],
            ]
        )

        classification = classify_domains(classification_text)

        chunks = chunk_text(
            extracted.text,
            page_spans=extracted.page_spans,
        )

        parsed_output_path = settings.parsed_dir / f"{document_id}.json"
        chunks_output_path = settings.chunks_dir / f"{document_id}.json"

        document_metadata = {
            "source_type": source_type,
            "tool_name": tool_name,
            "tool_version": tool_version,
            "version_major": version_major,
            "version_minor": version_minor,
            "publication_year": publication_year,
            "is_active": is_active,
            "is_deprecated": is_deprecated,
            "notes": notes,
        }

        parsed_payload = {
            "document_id": document_id,
            "filename": original_filename,
            "stored_filename": upload_path.name,
            "file_hash": content_hash,
            "content_hash": content_hash,
            "file_type": extracted.file_type,
            "title": extracted.title,
            "author": extracted.author,
            "page_count": extracted.page_count,
            "page_spans": [
                {
                    "page_number": span.page_number,
                    "start": span.start,
                    "end": span.end,
                }
                for span in extracted.page_spans or []
            ],
            "primary_domain": classification.primary_domain,
            "domains": classification.domains,
            "domain_scores": classification.scores,
            "document_metadata": document_metadata,
            "text": extracted.text,
        }

        chunks_payload = {
            "document_id": document_id,
            "filename": original_filename,
            "title": extracted.title,
            "author": extracted.author,
            "file_type": extracted.file_type,
            "primary_domain": classification.primary_domain,
            "domains": classification.domains,
            "domain_scores": classification.scores,
            "content_hash": content_hash,
            "document_metadata": document_metadata,
            "chunks": [
                {
                    "chunk_index": chunk.chunk_index,
                    "page_number": chunk.page_number,
                    "page_start": chunk.page_start,
                    "page_end": chunk.page_end,
                    "page_numbers": chunk.page_numbers,
                    "text": chunk.text,
                    "char_start": chunk.char_start,
                    "char_end": chunk.char_end,
                }
                for chunk in chunks
            ],
        }

        parsed_output_path.write_text(
            json.dumps(parsed_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        chunks_output_path.write_text(
            json.dumps(chunks_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        document = Document(
            document_id=document_id,
            filename=original_filename,
            title=extracted.title,
            author=extracted.author,
            file_type=extracted.file_type,
            source_type=source_type,
            tool_name=tool_name,
            tool_version=tool_version,
            version_major=version_major,
            version_minor=version_minor,
            publication_year=publication_year,
            primary_domain=classification.primary_domain,
            domains=classification.domains,
            page_count=extracted.page_count,
            chunk_count=len(chunks),
            text_characters=len(extracted.text),
            content_hash=content_hash,
            is_active=is_active,
            is_deprecated=is_deprecated,
            saved_path=str(upload_path),
            parsed_output_path=str(parsed_output_path),
            chunks_output_path=str(chunks_output_path),
            notes=notes,
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        elapsed_seconds = time.perf_counter() - start_time

        return IngestResponse(
            document_id=document_id,
            filename=original_filename,
            saved_path=str(upload_path),
            file_type=extracted.file_type,
            title=extracted.title,
            author=extracted.author,
            page_count=extracted.page_count,
            primary_domain=classification.primary_domain,
            domains=classification.domains,
            text_characters=len(extracted.text),
            chunk_count=len(chunks),
            parsed_output_path=str(parsed_output_path),
            chunks_output_path=str(chunks_output_path),
            elapsed_seconds=round(elapsed_seconds, 3),
            elapsed_ms=round(elapsed_seconds * 1000, 2),
            content_hash=content_hash,
            registry_created=True,
        )

    except HTTPException:
        raise

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {type(error).__name__}: {error}",
        )

    finally:
        await file.close()