import re
from dataclasses import dataclass


@dataclass
class PageSpan:
    page_number: int
    start: int
    end: int
    physical_page_number: int
    printed_page_number: int | None = None


def infer_page_number_from_markers(text: str, char_position: int) -> int | None:
    """
    Infer page number from injected [Page X] markers.
    """
    text_before_chunk = text[:char_position]
    matches = list(re.finditer(r"\[Page\s+(\d+)\]", text_before_chunk))

    if not matches:
        return None

    return int(matches[-1].group(1))


def infer_page_range_from_spans(
    page_spans: list[PageSpan] | None,
    char_start: int,
    char_end: int,
) -> tuple[int | None, int | None, list[int]]:
    if not page_spans:
        return None, None, []

    pages: list[int] = []

    for span in page_spans:
        overlaps = span.start < char_end and span.end > char_start

        if overlaps:
            pages.append(span.physical_page_number)

    if not pages:
        previous_spans = [
            span for span in page_spans
            if span.start <= char_start
        ]

        if previous_spans:
            page = previous_spans[-1].physical_page_number
            return page, page, [page]

        return None, None, []

    unique_pages = sorted(set(pages))

    return unique_pages[0], unique_pages[-1], unique_pages