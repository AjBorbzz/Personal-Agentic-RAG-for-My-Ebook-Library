import hashlib 
import json 
import shutil 
import time 
from pathlib import Path 
from uuid import uuid4 
 
from fastapi import APIRouter, File, HTTPException, UploadFile 
from pydantic import BaseModel 

from app.core.config import settings 
from app.ingestion.chunker import chunk_text 
from app.ingestion.parsers import extract_document 

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

def _safe_filename(filename:str) -> str:
    return Path(filename).name.replace(" ", "_")

def _sha256_file(file_path: Path) -> str:
    hasher = hashlib.sha256() 

    with file_path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(block)

    return hasher.hexdigest()

@router.post("/ingest", response_model=IngestResponse)
async def ingest_ebook(file: UploadFile = File(...)):
    start_time = time.perf_counter() 

    original_filename = file.filename or "upload_file"
    safe_filename = _safe_filename(original_filename)
    suffix = Path(safe_filename).suffix.lower() 

    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Supported: {sorted(SUPPORTED_EXTENSIONS)}"
        )
    
    document_id = str(uuid4())
    upload_path = settings.uploads_dir / f"{document_id}_{safe_filename}"
    try: 
        with upload_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_hash = _sha256_file(upload_path)
        extracted = extract_document(upload_path)

        if not extracted.text.strip():
            raise HTTPException(
                status_code=422,
                detail=("No readable text was extracted."
                        "This may be a scanned PDF or image-only ebook. OCR will be added"),
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

        parsed_payload = {
            "document_id": document_id,
            "filename": original_filename,
            "stored_filename": upload_path.name,
            "file_hash": file_hash,
            "file_type": extracted.file_type,
            "title": extracted.title,
            "author": extracted.author,
            "page_count": extracted.page_count,
            "primary_domain": classification.primary_domain,
            "domains": classification.domains,
            "domain_scores": classification.scores,
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
                }for chunk in chunks
            ],
        }

        parsed_output_path = settings.parsed_dir / f"{document_id}.json"
        chunks_output_path = settings.chunks_dir / f"{document_id}.json"

        parsed_output_path.write_text(
            json.dumps(parsed_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        chunks_output_path.write_text(
            json.dumps(chunks_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

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
            )
                
    except HTTPException:
        raise 

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {error}"
        )
    
    finally:
        await file.close()