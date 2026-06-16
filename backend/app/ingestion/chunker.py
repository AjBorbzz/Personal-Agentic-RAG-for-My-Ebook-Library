import re
from dataclasses import dataclass

from app.ingestion.page_spans import PageSpan


@dataclass
class TextChunk:
    chunk_index: int
    text: str
    char_start: int
    char_end: int
    page_number: int | None = None
    page_start: int | None = None
    page_end: int | None = None
    page_numbers: list[int] | None = None


def infer_page_range_from_spans(page_spans, char_start: int, char_end: int) -> tuple[int | None, int | None, list[int]]:
    if not page_spans:
        return None, None, []

    pages: list[int] = []

    for span in page_spans:
        overlaps = span.start < char_end and span.end > char_start

        if overlaps:
            pages.append(span.page_number)

    if not pages:
        previous_spans = [
            span for span in page_spans
            if span.start <= char_start
        ]

        if previous_spans:
            page = previous_spans[-1].page_number
            return page, page, [page]

        return None, None, []

    unique_pages = list(dict.fromkeys(pages))

    return unique_pages[0], unique_pages[-1], unique_pages

def infer_page_number_from_spans(
    page_spans: list[PageSpan] | None,
    char_position: int,
) -> int | None:
    if not page_spans:
        return None

    for span in page_spans:
        if span.start <= char_position < span.end:
            return span.page_number

    previous_spans = [
        span for span in page_spans
        if span.start <= char_position
    ]

    if previous_spans:
        return previous_spans[-1].page_number

    return page_spans[0].page_number


def infer_page_number_from_markers(text: str, char_position: int) -> int | None:
    """
    Fallback page inference from [Page X] markers.

    Handles first chunk too, where char_position = 0.
    """
    lookback_start = max(0, char_position - 1000)
    lookahead_end = min(len(text), char_position + 1000)

    nearby_text = text[lookback_start:lookahead_end]

    matches = list(re.finditer(r"\[Page\s+(\d+)\]", nearby_text))

    if not matches:
        return None

    valid_matches = []

    for match in matches:
        absolute_match_start = lookback_start + match.start()

        if absolute_match_start <= char_position + 100:
            valid_matches.append(match)

    if valid_matches:
        return int(valid_matches[-1].group(1))

    return int(matches[0].group(1))


def chunk_text(
                text: str,
                chunk_size: int = 2500,
                overlap: int = 300,
                page_spans: list[PageSpan] | None = None,
                infer_pages: bool = True,
            ) -> list[TextChunk]:
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
            page_start = None
            page_end = None
            page_numbers: list[int] = []

            if infer_pages:
                page_start, page_end, page_numbers = infer_page_range_from_spans(
                    page_spans=page_spans,
                    char_start=start,
                    char_end=end,
                )

            page_number = page_start

            chunks.append(
                TextChunk(
                    chunk_index=index,
                    text=chunk,
                    char_start=start,
                    char_end=end,
                    page_number=page_number,
                    page_start=page_start,
                    page_end=page_end,
                    page_numbers=page_numbers,
                )
            )

            index += 1

        if end >= text_length:
            break

        start = end - overlap

    return chunks