from pydantic import BaseModel 
from fastapi import APIRouter 

from app.services.ollama import generate_embedding, generate_text 

router = APIRouter() 

class ChatRequest(BaseModel):
    message: str 

class ChatResponse(BaseModel):
    answer: str 

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    answer = await generate_text(request.message)
    return ChatResponse(answer=answer)

@router.post("/embed-test")
async def embed_test(request: ChatRequest):
    embedding = await generate_embedding(request.message)
    return {
        "dimension": len(embedding),
        "sample": embedding[:5]
    }