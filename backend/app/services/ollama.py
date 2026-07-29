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

async def generate_structured_text(
    prompt: str,
    json_schema: dict,
) -> str:
    payload = {
        "model": settings.llm_model,
        "prompt": prompt,
        "stream": False,
        "format": json_schema,
        "think": False,
        "options": {
            "temperature": 0,
        },
    }

    timeout = httpx.Timeout(
        timeout=300.0,
        connect=15.0,
    )

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            f"{settings.ollama_url}/api/generate",
            json=payload,
        )

        response.raise_for_status()

        data = response.json()
        generated_text = data.get("response", "").strip()

        if not generated_text:
            done_reason = data.get("done_reason")
            thinking_text = data.get("thinking", "")

            raise RuntimeError(
                "Ollama returned an empty structured response. "
                f"done_reason={done_reason!r}, "
                f"thinking_characters={len(thinking_text)}"
            )

        return generated_text
    
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