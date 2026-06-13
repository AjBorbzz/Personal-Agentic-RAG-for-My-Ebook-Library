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
    parsed_output_path: str 
    chunks_output_path: str 
    elapsed_seconds: float 
    elapsed_ms: float 

def _safe_filename(filename:str) -> str:
    return Path(filename).name.replace(" ", "_")