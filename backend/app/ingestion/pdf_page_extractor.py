"""
!!!Important change: this version cleans each page before creating PageSpan. 
Do not clean the full PDF text afterward, or the span positions may become inaccurate.
"""

import re
from pathlib import Path

from app.ingestion.cleaner import clean_text
from app.ingestion.page_spans import PageSpan


def detect_visible_page_number_pymupdf(page) -> int | None:
    """
    Detect printed page numbers from the top-right header area.

    Example:
    A PDF physical page may be page 107,
    but the printed ebook page number may show 105.
    """
    try:
        page_dict = page.get_text("dict")
        width = page.rect.width
        height = page.rect.height

        candidates: list[int] = []

        for block in page_dict.get("blocks", []):
            if block.get("type") != 0:
                continue

            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    bbox = span.get("bbox", [])

                    if not text or len(bbox) != 4:
                        continue

                    x0, y0, x1, y1 = bbox

                    is_top_area = y1 <= height * 0.18
                    is_right_area = x0 >= width * 0.65

                    if is_top_area and is_right_area:
                        numbers = re.findall(r"\b\d{1,5}\b", text)
                        for number in numbers:
                            candidates.append(int(number))

        if candidates:
            return candidates[-1]

    except Exception:
        return None

    return None


def detect_visible_page_number_pdfplumber(pdfplumber_page) -> int | None:
    """
    Fallback detector using pdfplumber by cropping the top-right area.
    """
    try:
        width = pdfplumber_page.width
        height = pdfplumber_page.height

        top_right = pdfplumber_page.crop(
            (
                width * 0.60,
                0,
                width,
                height * 0.18,
            )
        )

        text = top_right.extract_text() or ""
        numbers = re.findall(r"\b\d{1,5}\b", text)

        if numbers:
            return int(numbers[-1])

    except Exception:
        return None

    return None


def extract_text_pymupdf(page) -> str:
    try:
        return page.get_text("text", sort=True).strip()
    except Exception:
        return ""


def extract_text_pdfplumber(pdfplumber_page) -> str:
    try:
        return (pdfplumber_page.extract_text() or "").strip()
    except Exception:
        return ""


def extract_text_pypdf(reader, page_index: int) -> str:
    try:
        return (reader.pages[page_index].extract_text() or "").strip()
    except Exception:
        return ""


def extract_pdf_with_page_markers(pdf_path: str | Path) -> tuple[str, list[PageSpan]]:
    """
    Extract PDF text page by page.

    Priority:
    1. Use visible printed page number from top-right header if available.
    2. Fall back to physical PDF page index.
    3. Inject [Page X] marker manually.
    4. Return full text plus page spans for safer chunk metadata mapping.
    """
    pdf_path = Path(pdf_path)

    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise ImportError("Install PyMuPDF: pip install pymupdf") from exc

    try:
        import pdfplumber
    except ImportError:
        pdfplumber = None

    try:
        from pypdf import PdfReader
    except ImportError:
        PdfReader = None

    doc = fitz.open(str(pdf_path))

    plumber_pdf = None
    if pdfplumber:
        try:
            plumber_pdf = pdfplumber.open(str(pdf_path))
        except Exception:
            plumber_pdf = None

    reader = None
    if PdfReader:
        try:
            reader = PdfReader(str(pdf_path))
        except Exception:
            reader = None

    full_text_parts: list[str] = []
    page_spans: list[PageSpan] = []
    current_position = 0

    try:
        for page_index in range(len(doc)):
            pymupdf_page = doc.load_page(page_index)

            physical_page_number = page_index + 1
            printed_page_number = detect_visible_page_number_pymupdf(pymupdf_page)

            if printed_page_number is None and plumber_pdf is not None:
                printed_page_number = detect_visible_page_number_pdfplumber(
                    plumber_pdf.pages[page_index]
                )

            page_number = physical_page_number
            page_block = f"\n\n[PDF Page {physical_page_number}]"

            if printed_page_number is not None:
                page_block += f" [Printed Page {printed_page_number}]"


            page_text = extract_text_pymupdf(pymupdf_page)
            
            if not page_text and plumber_pdf is not None:
                page_text = extract_text_pdfplumber(plumber_pdf.pages[page_index])

            if not page_text and reader is not None:
                page_text = extract_text_pypdf(reader, page_index)

            page_text = clean_text(page_text)

            page_block += f"\n{page_text}\n"

            start = current_position
            end = current_position + len(page_block)

            full_text_parts.append(page_block)
            page_spans.append(
                PageSpan(
                    page_number=physical_page_number,
                    physical_page_number=physical_page_number,
                    printed_page_number=printed_page_number,
                    start=start,
                    end=end,
                )
            )

            current_position = end

    finally:
        doc.close()

        if plumber_pdf is not None:
            plumber_pdf.close()

    return "".join(full_text_parts), page_spans