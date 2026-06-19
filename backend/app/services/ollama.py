import httpx 

from app.core.config import settings 

async def generate_text(prompt: str) -> str:
    payload = {
        "model": settings.llm_model,
        "prompt": prompt,
        "stream": False,
    }

    timeout = httpx.Timeout(
        connect=10.0,
        read=1800.0,
        write=120.0,
        pool=10.0,
    )

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            f"{settings.ollama_url}/api/generate",
            json=payload,
        )
        response.raise_for_status()
        data = response.json() 
        return data.get("response", "")
    
async def generate_embedding(text: str) -> list[float]:
    payload = {
        "model": settings.embedding_model,
        "input": text,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{settings.ollama_url}/api/embed",
            json=payload,
        )
        response.raise_for_status()
        data = response.json() 

    embeddings = data.get("embeddings", [])
    if not embeddings:
        raise ValueError("No embeddings returned from Ollama.")
    
    return embeddings[0]