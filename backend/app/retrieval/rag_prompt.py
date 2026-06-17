from typing import Any 

def _format_pages(payload: dict[str, Any]) -> str:
    page_start = payload.get("page_start")
    page_end = payload.get("page_end")
    page_number = payload.get("page_number")

    if page_start is not None and page_end is None:
        if page_start == page_end:
            return str(page_start)
        return f"{page_start}-{page_end}"
    
    if page_number is not None:
        return str(page_number)
    
    return "N/A"

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

    return f"""
    You are a technical assistant answering question using the user's private ebook library. 
    Rules:
    1. Use only the provided sources.
    2. If the sources are insufficient, say: "The Provided ebook sources do not containt enough information to answer this fully."
    3. Do not invent book titles, authors, citations, facts or page numbers.
    4. Give a clear technical answer.
    5. Cite sources inline using [Source 1], [Source 2], etc.
    6. Prefer practical engineering explanations.
    7. Use the PDF page range and chunk metadata when referring to sources.

    User question:
    {question}

    Retrieved ebook sources:
    {context} 

    Answer:
    """.strip()