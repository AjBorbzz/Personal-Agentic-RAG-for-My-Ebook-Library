from typing import Any


def _format_pages(payload: dict[str, Any]) -> str:
    page_start = payload.get("page_start")
    page_end = payload.get("page_end")
    page_number = payload.get("page_number")

    if page_start is not None and page_end is not None:
        if page_start == page_end:
            return str(page_start)

        return f"{page_start}-{page_end}"

    if page_number is not None:
        return str(page_number)

    return "N/A"


def build_agentic_rag_prompt(
    question: str,
    matches: list[dict[str, Any]],
    intent: str,
    retrieval_strategy: str,
    detected_domains: list[str],
    search_domains: list[str],
    rewritten_query: str | None = None,
    max_context_chars: int = 14000,
) -> str:
    context_blocks: list[str] = []
    used_chars = 0

    for index, match in enumerate(matches, start=1):
        payload = match.get("payload", {})

        title = payload.get("title") or "Unknown title"
        author = payload.get("author") or "Unknown author"
        filename = payload.get("filename") or "Unknown file"
        primary_domain = payload.get("primary_domain") or "general"
        domains = payload.get("domains") or ["general"]
        pages = _format_pages(payload)
        chunk_index = payload.get("chunk_index")
        chunk_text = payload.get("chunk_text") or ""

        source_header = (
            f"[Source {index}]\n"
            f"Title: {title}\n"
            f"Author: {author}\n"
            f"File: {filename}\n"
            f"Primary Domain: {primary_domain}\n"
            f"Domains: {', '.join(domains)}\n"
            f"PDF Pages: {pages}\n"
            f"Chunk: {chunk_index}\n"
        )

        block = f"{source_header}\nContent:\n{chunk_text}\n"

        if used_chars + len(block) > max_context_chars:
            remaining = max_context_chars - used_chars

            if remaining > 1000:
                context_blocks.append(block[:remaining])

            break

        context_blocks.append(block)
        used_chars += len(block)

    context = "\n\n---\n\n".join(context_blocks)

    rewrite_section = ""
    if rewritten_query:
        rewrite_section = f"\nRewritten retrieval query:\n{rewritten_query}\n"

    return f"""
You are a technical assistant answering questions using the user's private ebook library.

Routing metadata:
- Intent: {intent}
- Retrieval strategy: {retrieval_strategy}
- Detected domains: {", ".join(detected_domains)}
- Search domains: {", ".join(search_domains) if search_domains else "all"}
{rewrite_section}

Rules:
1. Use only the provided ebook sources.
2. If the sources are insufficient, say exactly: "The provided ebook sources do not contain enough information to answer this fully."
3. Do not invent book titles, authors, citations, facts, or page numbers.
4. Cite sources inline using [Source 1], [Source 2], etc.
5. Prefer practical engineering explanations.
6. Use PDF page ranges and chunk metadata when referring to sources.
7. If the intent is architecture_design, structure the answer around components, tradeoffs, risks, and implementation steps.
8. If the intent is how_to_guide, structure the answer as clear steps.
9. If the intent is comparison, compare using a compact table when useful.
10. If the intent is troubleshooting, prioritize likely causes and fixes.

User question:
{question}

Retrieved ebook sources:
{context}

Answer:
""".strip()