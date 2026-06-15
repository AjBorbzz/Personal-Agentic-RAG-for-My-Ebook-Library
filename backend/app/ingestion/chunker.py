from dataclasses import dataclass 
import re

@dataclass
class TextChunk:
    chunk_index: int 
    text: str 
    char_start: int 
    char_end: int 
    page_number: int | None = None

def infer_page_number(text: str, char_position: int) -> int | None:
    """
    Infer the current PDF page number by finding the latest [Page x]
    marker before the chunk start position.
    """
    text_before_chunk = text[:char_position]
    matches = list(re.finditer(r"\[Page\s+(d\+)\]", text_before_chunk))
    if not matches:
        return None 
    
    latest_match = matches[-1]
    return int(latest_match.group(1))

def chunk_text(
        text: str,
        chunk_size: int = 2500,
        overlap: int = 300,
        infer_pages: bool = True,
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
            page_number = infer_page_number(text, start) if infer_pages else None
            chunks.append(
                TextChunk(
                    chunk_index=index,
                    text=chunk,
                    char_start=start,
                    char_end=end,
                    page_number=page_number,
                )
            )
            index += 1
        if end >= text_length:
            break
        start = end - overlap 

    return chunks