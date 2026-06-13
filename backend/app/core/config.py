from pydantic import BaseModel 


class Settings(BaseModel):
    ollama_url: str = "http://localhost:11434"
    qdrant_url: str = "http://localhost:6333"
    llm_model: str = "qwen3:8b"
    embedding_model: str = "nomic-embed-text"
    default_collection: str = "ebooks_general"

settings = Settings()