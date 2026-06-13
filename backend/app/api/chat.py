from pydantic import BaseModel 
from fastapi import APIRouter 
import time

from app.services.ollama import generate_embedding, generate_text 

router = APIRouter() 

class ChatRequest(BaseModel):
    message: str 

class ChatResponse(BaseModel):
    answer: str 
    elapsed_seconds: float
    elapsed_ms: float 

class EmbedTestResponse(BaseModel):
    dimension: int 
    sample: list[float]
    elapsed_seconds: float 
    elapsed_ms: float 

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    start_time = time.perf_counter()
    answer = await generate_text(request.message)
    elapsed_seconds = time.perf_counter() - start_time
    return ChatResponse(answer=answer,
                        elapsed_seconds=round(elapsed_seconds, 3),
                        elapsed_ms=round(elapsed_seconds * 1000, 2))

@router.post("/embed-test")
async def embed_test(request: ChatRequest):
    start_time = time.perf_counter()
    embedding = await generate_embedding(request.message)
    elapsed_seconds = time.perf_counter() - start_time
    return EmbedTestResponse(
        dimension=len(embedding),
        sample=embedding[:5],
        elapsed_seconds=round(elapsed_seconds, 3),
        elapsed_ms=round(elapsed_seconds * 1000, 2)
    )