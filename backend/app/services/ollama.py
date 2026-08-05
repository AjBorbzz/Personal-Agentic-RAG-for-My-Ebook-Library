
from typing import Any

import httpx

from app.core.config import settings
from copy import deepcopy


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

# async def generate_structured_text(
#     prompt: str,
#     json_schema: dict,
#     model:str = None
# ) -> str:
#     payload = {
#         "model": model if model else settings.llm_model,
#         "prompt": prompt,
#         "stream": False,
#         "format": json_schema,
#         "think": False,
#         "options": {
#             "temperature": 0,
#         },
#     }

#     timeout = httpx.Timeout(
#         timeout=300.0,
#         connect=15.0,
#     )

#     async with httpx.AsyncClient(timeout=timeout) as client:
#         response = await client.post(
#             f"{settings.ollama_url}/api/generate",
#             json=payload,
#         )

#         response.raise_for_status()

#         data = response.json()
#         generated_text = data.get("response", "").strip()

#         if not generated_text:
#             done_reason = data.get("done_reason")
#             thinking_text = data.get("thinking", "")

#             raise RuntimeError(
#                 "Ollama returned an empty structured response. "
#                 f"done_reason={done_reason!r}, "
#                 f"thinking_characters={len(thinking_text)}"
#             )

#         return generated_text



def make_ollama_grammar_safe_schema(
    json_schema: dict[str, Any],
) -> dict[str, Any]:
    """
    Return a grammar-safe copy of a Pydantic JSON Schema.

    Ollama only needs the structural shape during generation.
    The original Pydantic model still performs full validation
    after the response is returned.
    """

    cleaned_schema = deepcopy(json_schema)

    def clean_node(node: Any) -> None:
        if isinstance(node, dict):
            # These constraints can generate extremely large or
            # invalid repetition rules in Ollama/llama.cpp grammar.
            node.pop("minLength", None)
            node.pop("maxLength", None)
            node.pop("minItems", None)
            node.pop("maxItems", None)

            # These are descriptive and unnecessary for grammar.
            node.pop("title", None)
            node.pop("examples", None)

            for value in node.values():
                clean_node(value)

        elif isinstance(node, list):
            for item in node:
                clean_node(item)

    clean_node(cleaned_schema)

    return cleaned_schema


async def generate_structured_text(
    prompt: str,
    json_schema: dict[str, Any],
    *,
    model: str | None = None,
    timeout_seconds: float = 300.0,
) -> str:
    selected_model = (
        model
        or getattr(
            settings,
            "book_skill_mapping_model",
            None,
        )
        or settings.llm_model
    )

    base_url = settings.ollama_url.rstrip("/")
    endpoint = f"{base_url}/api/generate"

    grammar_safe_schema = (
        make_ollama_grammar_safe_schema(
            json_schema
        )
    )

    payload = {
        "model": selected_model,
        "prompt": prompt,
        "stream": False,
        "format": grammar_safe_schema,
        "options": {
            "temperature": 0,
            "num_ctx": 8192,
        },
    }

    timeout = httpx.Timeout(
        timeout=timeout_seconds,
        connect=15.0,
    )

    try:
        async with httpx.AsyncClient(
            timeout=timeout,
        ) as client:
            response = await client.post(
                endpoint,
                json=payload,
            )

    except httpx.ConnectError as error:
        raise RuntimeError(
            "Cannot connect to Ollama at "
            f"{base_url}. Confirm that Ollama "
            "is running."
        ) from error

    except httpx.TimeoutException as error:
        raise RuntimeError(
            "Ollama timed out while generating "
            "structured output."
        ) from error

    if response.is_error:
        try:
            error_body = response.json()

            error_detail = str(
                error_body.get(
                    "error",
                    error_body,
                )
            )
        except Exception:
            error_detail = (
                response.text.strip()
                or "No error body returned."
            )

        raise RuntimeError(
            "Ollama rejected the structured-output "
            f"request with HTTP "
            f"{response.status_code}: "
            f"{error_detail}"
        )

    try:
        response_body = response.json()
    except ValueError as error:
        raise RuntimeError(
            "Ollama returned a non-JSON HTTP "
            "response."
        ) from error

    generated_text = response_body.get(
        "response"
    )

    if not isinstance(
        generated_text,
        str,
    ):
        raise RuntimeError(
            "Ollama returned no generated "
            "response text."
        )

    generated_text = generated_text.strip()

    if not generated_text:
        done_reason = response_body.get(
            "done_reason"
        )

        thinking_text = response_body.get(
            "thinking",
            "",
        )

        raise RuntimeError(
            "Ollama returned an empty structured "
            "response. "
            f"done_reason={done_reason!r}, "
            "thinking_characters="
            f"{len(thinking_text)}"
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