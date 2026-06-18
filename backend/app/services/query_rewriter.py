from app.services.ollama import generate_text


def _fallback_rewrite(question: str) -> str:
    return question.strip()


async def rewrite_query_for_retrieval(
    question: str,
    domains: list[str],
) -> str:
    domain_text = ", ".join(domains) if domains else "general"

    prompt = f"""
Rewrite the user's question into a concise semantic search query for retrieving ebook chunks.

Rules:
- Return only the rewritten query.
- Do not answer the question.
- Keep important technical terms.
- Remove filler words.
- Include domain hints if useful.
- Maximum 40 words.

Detected domains:
{domain_text}

User question:
{question}

Rewritten search query:
""".strip()

    try:
        rewritten = await generate_text(prompt)
        rewritten = rewritten.strip().strip('"').strip("'")

        if not rewritten:
            return _fallback_rewrite(question)

        if len(rewritten) > 500:
            return _fallback_rewrite(question)

        return rewritten

    except Exception:
        return _fallback_rewrite(question)