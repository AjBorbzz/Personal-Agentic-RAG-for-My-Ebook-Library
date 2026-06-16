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


def infer_page_number_from_spans(
    page_spans: list[PageSpan] | None,
    char_position: int,
) -> int | None:
    """
    Infer page number using exact page span boundaries.

    This is safer than relying only on regex markers.
    """
    if not page_spans:
        return None

    for span in page_spans:
        if span.start <= char_position < span.end:
            return span.page_number

    # If chunk starts after the last page span, return the last known page.
    if page_spans and char_position >= page_spans[-1].end:
        return page_spans[-1].page_number

    return None