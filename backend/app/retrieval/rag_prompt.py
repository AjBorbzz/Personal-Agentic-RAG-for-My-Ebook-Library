from typing import Any 

def build_rag_prompt(question: str, matches: list[dict[str, Any]], max_context_chars: int=12000) -> str:
    """
    Build a grounded RAG prompt using retrieved ebook chunks.
    """

    context_blocks: list[str] = []
    used_chars = 0

    for index, match in enumerate(matches, start=1):
        payload = match.get("payload", {})
        title = payload.get("title") or "Unknown title"
        author = payload.get("author") or "Unknown author"
        filename= payload.get("filename") or "Unknown file"
        page_number = payload.get("page_number")
        chunk_index = payload.get("chunk_index")
        chunk_text = payload.get("chunk_text") or ""

        source_header = (
            f"[Source {index}]\n"
            f"Title: {title}\n"
            f"Author: {author}\n"
            f"File: {filename}\n"
            f"Page: {page_number if page_number is not None else 'N/A'}\n"
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

    return f"""
    You are a technical assistant answering question using the user's private ebook library. 
    Rules:
    1. Use only the provided sources.
    2. If the sources are insufficient, say: "The Provided ebook sources do not containt enough information to answer this fully."
    3. Do not invent book titles, authors, citations, facts or page numbers.
    4. Give a clear technical answer.
    5. Cite sources inline using [Source 1], [Source 2], etc.
    6. Prefer practical engineering explanations.

    User question:
    {question}

    Retrieved ebook sources:
    {context} 

    Answer:
    """.strip()