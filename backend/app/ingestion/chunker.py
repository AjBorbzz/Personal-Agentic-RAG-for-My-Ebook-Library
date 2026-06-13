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
    if not text:
        return []