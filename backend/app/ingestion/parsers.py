from dataclasses import dataclass 
from pathlib import Path 

import ebooklib 
from bs4 import BeautifulSoup 
from ebooklib import epub 
from pypdf import PdfReader 

from app.ingestion.cleaner import clean_text 

@dataclass 
class ExtractedDocument:
    title: str | None 
    author: str | None 
    file_type: str 
    text: str 
    page_count: int | None = None

def extract_text_from_txt(file_path: Path) -> ExtractedDocument:
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    return ExtractedDocument(
        title=file_path.stem,
        author=None,
        file_type="txt",
        page_count=None,
    )

def extract_text_from_pdf(file_path: Path) -> ExtractedDocument:
    reader = PdfReader(str(file_path))
    parts: list[str] = []
    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        if page_text.strip():
            parts.append(f"\n\n[Page {page_number}]\n{page_text}")

    metadata = reader.metadata or {}

    title = None 
    authoer = None 

    if metadata:
        title = getattr(metadata, "title", None)
        author = getattr(metadata, "author", None)

    text = clean_text("\n".join(parts))

    return ExtractedDocument(
        title=title or file_path.stem,
        author=author,
        file_type="pdf",
        text=text,
        page_count=len(reader.pages)
    )

def _first_epub_metadata_value(book: epub.EpubBook, namespace: str, name: str) -> str | None:
    values = book.get_metadata(namespace, name)
    if not values:
        return None 
    
    first = values[0]

    if isinstance(first, tuple) and first:
        return str(first[0])
    
    return str(first)

def extract_text_from_epub(file_path: Path) -> ExtractedDocument:
    book = epub.read_epub(str(file_path))
    title = _first_epub_metadata_value(book, "DC", "title") or file_path.stem 
    author = _first_epub_metadata_value(book, "DC", "creator")

    parts: list[str] = []

    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        html_content = item.get_content()
        soup = BeautifulSoup(html_content, "html.parser")

        for tag in soup(["script", "style", "nav"]):
            tag.decompose() 

        text = soup.get_text(separator="\n")
        text = clean_text(text) 

        if text:
            parts.append(text)

    return ExtractedDocument(
        title=title,
        author=author,
        file_type="epub",
        text=clean_text("\n\n".join(parts)),
        page_count=None,
    )

def extract_document(file_path: Path) -> ExtractedDocument:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    
    if suffix == ".epub":
        return extract_text_from_epub(file_path)
    
    if suffix == ".txt":
        return extract_text_from_txt(file_path)
    
    raise ValueError(f"Unsupported file type: {suffix}")