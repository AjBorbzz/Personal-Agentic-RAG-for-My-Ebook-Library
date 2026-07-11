import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.file_hash import calculate_file_sha256
from app.db.session import get_db
from app.models.document import Document
from app.models.ingestion_job import IngestionJob
from app.schemas.ingestion_job import CancelJobResponse, IngestionJobResponse

router = APIRouter(prefix="/ingestion-jobs", tags=["ingestion-jobs"])

SUPPORTED_EXTENSIONS = {".pdf", ".epub", ".txt"}


def _safe_filename(filename: str) -> str:
    return Path(filename).name.replace(" ", "_")


@router.post("/upload", response_model=IngestionJobResponse)
async def upload_ingestion_job(
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

    job_id = str(uuid4())
    document_id = str(uuid4())

    settings.uploads_dir.mkdir(parents=True, exist_ok=True)

    upload_path = settings.uploads_dir / f"{document_id}_{safe_filename}"

    try:
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
                    "message": "This file has already been ingested as a document.",
                    "document_id": existing_document.document_id,
                    "filename": existing_document.filename,
                    "title": existing_document.title,
                    "content_hash": existing_document.content_hash,
                },
            )

        existing_job = db.scalar(
            select(IngestionJob).where(
                IngestionJob.content_hash == content_hash,
                IngestionJob.status.in_(["queued", "running"]),
            )
        )

        if existing_job:
            upload_path.unlink(missing_ok=True)

            raise HTTPException(
                status_code=409,
                detail={
                    "message": "This file already has a queued or running ingestion job.",
                    "job_id": existing_job.job_id,
                    "document_id": existing_job.document_id,
                    "status": existing_job.status,
                    "content_hash": existing_job.content_hash,
                },
            )

        job = IngestionJob(
            job_id=job_id,
            document_id=document_id,
            status="queued",
            original_filename=original_filename,
            stored_filename=upload_path.name,
            upload_path=str(upload_path),
            file_type=suffix.replace(".", ""),
            content_hash=content_hash,
            source_type=source_type,
            tool_name=tool_name,
            tool_version=tool_version,
            version_major=version_major,
            version_minor=version_minor,
            publication_year=publication_year,
            is_active=is_active,
            is_deprecated=is_deprecated,
            notes=notes,
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        return job

    except HTTPException:
        raise

    except Exception as error:
        db.rollback()
        upload_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail=f"Failed to create ingestion job: {type(error).__name__}: {error}",
        )

    finally:
        await file.close()


@router.get("", response_model=list[IngestionJobResponse])
def list_ingestion_jobs(
    db: Session = Depends(get_db),
    status: str | None = Query(default=None),
    tool_name: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
):
    statement = select(IngestionJob).order_by(IngestionJob.created_at.desc())

    if status:
        statement = statement.where(IngestionJob.status == status)

    if tool_name:
        statement = statement.where(IngestionJob.tool_name == tool_name)

    statement = statement.limit(limit)

    return list(db.scalars(statement).all())


@router.get("/{job_id}", response_model=IngestionJobResponse)
def get_ingestion_job(
    job_id: str,
    db: Session = Depends(get_db),
):
    job = db.get(IngestionJob, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Ingestion job not found.")

    return job


@router.patch("/{job_id}/cancel", response_model=CancelJobResponse)
def cancel_ingestion_job(
    job_id: str,
    db: Session = Depends(get_db),
):
    job = db.get(IngestionJob, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Ingestion job not found.")

    if job.status != "queued":
        raise HTTPException(
            status_code=409,
            detail=f"Only queued jobs can be cancelled. Current status: {job.status}",
        )

    job.status = "cancelled"
    job.error_message = "Cancelled by user."

    db.commit()
    db.refresh(job)

    return CancelJobResponse(
        job_id=job.job_id,
        status=job.status,
        message="Ingestion job cancelled.",
    )