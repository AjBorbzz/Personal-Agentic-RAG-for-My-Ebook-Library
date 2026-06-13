from dataclasses import dataclass 

@dataclass
class TextChunk:
    chunk_index: int 
    text: str 
    char_start: int 
    char_end: int 

def chunk_text(
        text: str,
        chunk_size: int = 2500,
        overlap: int = 300,
) -> list[TextChunk]:
    """
    Character-based chunking for MVP.
    LAter phases will replace this with token-aware and chapter-aware chunking.
    """
    if not text:
        return []
    
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap.")
    
    chunks: list[TextChunk] = []
    start = 0
    index = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(
                TextChunk(
                    chunk_index=index,
                    text=chunk,
                    char_start=start,
                    char_end=end,
                )
            )
            index += 1
        if end >= text_length:
            break
        start = end - overlap 

    return chunks