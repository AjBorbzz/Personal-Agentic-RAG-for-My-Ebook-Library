import mimetypes
import os
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.ingestion_job import IngestionJob


API_BASE_URL = os.getenv(
    "INTERNAL_API_BASE_URL",
    "http://localhost:8000",
)

POLL_INTERVAL_SECONDS = float(
    os.getenv("INGESTION_WORKER_POLL_SECONDS", "3")
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def claim_next_job() -> str | None:
    """
    Atomically claims the oldest available queued job.

    SELECT FOR UPDATE SKIP LOCKED allows multiple workers to run
    without processing the same job.
    """

    with SessionLocal() as db:
        with db.begin():
            statement = (
                select(IngestionJob)
                .where(
                    IngestionJob.status == "queued",
                    IngestionJob.attempt_count
                    < IngestionJob.max_attempts,
                )
                .order_by(IngestionJob.created_at.asc())
                .with_for_update(skip_locked=True)
                .limit(1)
            )

            job = db.scalar(statement)

            if not job:
                return None

            job.status = "running"
            job.current_step = "claimed"
            job.progress_percent = 1
            job.started_at = utc_now()
            job.completed_at = None
            job.error_message = None
            job.attempt_count += 1

            db.flush()

            return job.job_id


def get_job_snapshot(job_id: str) -> dict[str, Any]:
    """
    Returns the job as a plain dictionary so it remains usable
    after the SQLAlchemy session is closed.
    """

    with SessionLocal() as db:
        job = db.get(IngestionJob, job_id)

        if not job:
            raise RuntimeError(
                f"Ingestion job not found: {job_id}"
            )

        return {
            "job_id": job.job_id,
            "document_id": job.document_id,
            "status": job.status,
            "original_filename": job.original_filename,
            "upload_path": job.upload_path,
            "file_type": job.file_type,
            "source_type": job.source_type,
            "tool_name": job.tool_name,
            "tool_version": job.tool_version,
            "version_major": job.version_major,
            "version_minor": job.version_minor,
            "publication_year": job.publication_year,
            "is_active": job.is_active,
            "is_deprecated": job.is_deprecated,
            "index_after_ingest": job.index_after_ingest,
            "notes": job.notes,
            "attempt_count": job.attempt_count,
            "max_attempts": job.max_attempts,
        }


def update_job(
    job_id: str,
    *,
    status: str | None = None,
    current_step: str | None = None,
    progress_percent: int | None = None,
    document_id: str | None = None,
    result: dict[str, Any] | None = None,
    error_message: str | None = None,
    completed_at: datetime | None = None,
    clear_error: bool = False,
) -> None:
    with SessionLocal() as db:
        job = db.get(IngestionJob, job_id)

        if not job:
            raise RuntimeError(
                f"Ingestion job not found: {job_id}"
            )

        if status is not None:
            job.status = status

        if current_step is not None:
            job.current_step = current_step

        if progress_percent is not None:
            job.progress_percent = max(
                0,
                min(progress_percent, 100),
            )

        if document_id is not None:
            job.document_id = document_id

        if result is not None:
            job.result = result

        if error_message is not None:
            job.error_message = error_message

        if clear_error:
            job.error_message = None

        if completed_at is not None:
            job.completed_at = completed_at

        db.commit()


def build_ingest_form(job: dict[str, Any]) -> dict[str, str]:
    """
    Converts job metadata into multipart form values expected by
    the existing POST /ingest endpoint.
    """

    form_data: dict[str, str] = {
        "is_active": str(job["is_active"]).lower(),
        "is_deprecated": str(
            job["is_deprecated"]
        ).lower(),
    }

    optional_fields = [
        "source_type",
        "tool_name",
        "tool_version",
        "version_major",
        "version_minor",
        "publication_year",
        "notes",
    ]

    for field_name in optional_fields:
        value = job.get(field_name)

        if value is not None:
            form_data[field_name] = str(value)

    return form_data


def extract_document_id_from_ingest_response(
    response: httpx.Response,
) -> tuple[str, dict[str, Any]]:
    """
    Handles both:
    - successful new ingestion
    - duplicate-document response during a retry
    """

    response_data = response.json()

    if response.status_code in {200, 201}:
        document_id = response_data.get("document_id")

        if not document_id:
            raise RuntimeError(
                "The /ingest response did not contain document_id."
            )

        return document_id, response_data

    if response.status_code == 409:
        detail = response_data.get(
            "detail",
            response_data,
        )

        if not isinstance(detail, dict):
            response.raise_for_status()

        document_id = detail.get("document_id")

        if not document_id:
            response.raise_for_status()

        duplicate_result = {
            "duplicate_document_reused": True,
            **detail,
        }

        return document_id, duplicate_result

    response.raise_for_status()

    raise RuntimeError(
        f"Unexpected ingest response: {response.status_code}"
    )


def process_job(job_id: str) -> None:
    job = get_job_snapshot(job_id)

    upload_path_value = job.get("upload_path")

    if not upload_path_value:
        raise RuntimeError(
            "The ingestion job does not have an upload_path."
        )

    upload_path = Path(upload_path_value)

    if not upload_path.exists():
        raise FileNotFoundError(
            f"Queued upload file does not exist: {upload_path}"
        )

    original_filename = (
        job.get("original_filename")
        or upload_path.name
    )

    mime_type = (
        mimetypes.guess_type(original_filename)[0]
        or "application/octet-stream"
    )

    ingest_result: dict[str, Any]
    index_result: dict[str, Any] | None = None

    timeout = httpx.Timeout(
        timeout=1800.0,
        connect=15.0,
    )

    with httpx.Client(
        base_url=API_BASE_URL,
        timeout=timeout,
        follow_redirects=True,
    ) as client:
        update_job(
            job_id,
            status="running",
            current_step="ingesting",
            progress_percent=10,
            clear_error=True,
        )

        with upload_path.open("rb") as file_handle:
            files = {
                "file": (
                    original_filename,
                    file_handle,
                    mime_type,
                )
            }

            ingest_response = client.post(
                "/ingest",
                files=files,
                data=build_ingest_form(job),
            )

        document_id, ingest_result = (
            extract_document_id_from_ingest_response(
                ingest_response
            )
        )

        update_job(
            job_id,
            document_id=document_id,
            current_step="ingested",
            progress_percent=70,
            result={
                "ingest": ingest_result,
                "index": None,
            },
        )

        if job["index_after_ingest"]:
            update_job(
                job_id,
                current_step="indexing",
                progress_percent=75,
            )

            index_response = client.post(
                f"/index/{document_id}"
            )

            index_response.raise_for_status()
            index_result = index_response.json()

            update_job(
                job_id,
                current_step="indexed",
                progress_percent=95,
                result={
                    "ingest": ingest_result,
                    "index": index_result,
                },
            )

    update_job(
        job_id,
        status="completed",
        current_step="completed",
        progress_percent=100,
        result={
            "ingest": ingest_result,
            "index": index_result,
        },
        completed_at=utc_now(),
        clear_error=True,
    )

    # The normal /ingest endpoint has already stored the permanent
    # document copy, so this queued temporary upload can be removed.
    upload_path.unlink(missing_ok=True)


def mark_job_failed_or_retry(
    job_id: str,
    error: Exception,
) -> None:
    error_details = (
        f"{type(error).__name__}: {error}\n\n"
        f"{traceback.format_exc()}"
    )

    with SessionLocal() as db:
        job = db.get(IngestionJob, job_id)

        if not job:
            print(
                f"Unable to mark missing job as failed: {job_id}"
            )
            return

        job.error_message = error_details[:10000]

        if job.attempt_count < job.max_attempts:
            job.status = "queued"
            job.current_step = "retry_waiting"
            job.progress_percent = 0
            job.started_at = None
            job.completed_at = None

            print(
                f"Job {job_id} returned to queue. "
                f"Attempt {job.attempt_count}/"
                f"{job.max_attempts}"
            )
        else:
            job.status = "failed"
            job.current_step = "failed"
            job.completed_at = utc_now()

            print(
                f"Job {job_id} failed after "
                f"{job.attempt_count} attempts."
            )

        db.commit()


def run_worker() -> None:
    print("Ingestion worker started.")
    print(f"API base URL: {API_BASE_URL}")
    print(
        f"Polling every {POLL_INTERVAL_SECONDS} seconds."
    )

    try:
        while True:
            job_id = claim_next_job()

            if not job_id:
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            print(f"Processing ingestion job: {job_id}")

            try:
                process_job(job_id)
                print(f"Completed ingestion job: {job_id}")

            except Exception as error:
                print(
                    f"Error processing job {job_id}: "
                    f"{type(error).__name__}: {error}"
                )

                mark_job_failed_or_retry(
                    job_id,
                    error,
                )

    except KeyboardInterrupt:
        print("\nIngestion worker stopped.")


if __name__ == "__main__":
    run_worker()