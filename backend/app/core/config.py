from pydantic import BaseModel 
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]

class Settings(BaseModel):
    ollama_url: str = "http://localhost:11434"
    qdrant_url: str = "http://localhost:6333"
    llm_model: str = "qwen3:8b"
    embedding_model: str = "nomic-embed-text"
    default_collection: str = "ebooks_general"

    data_dir: Path = PROJECT_ROOT / "data"
    uploads_dir: Path = PROJECT_ROOT / "data" / "uploads"
    parsed_dir: Path = PROJECT_ROOT / "data" / "parsed"
    chunks_dir: Path = PROJECT_ROOT / "data" / "chunks"

settings = Settings()

settings.uploads_dir.mkdir(parents=True, exist_ok=True)
settings.parsed_dir.mkdir(parents=True, exist_ok=True)
settings.chunks_dir.mkdir(parents=True, exist_ok=True)