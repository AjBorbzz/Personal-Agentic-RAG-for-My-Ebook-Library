from typing import Any


def _format_pages(payload: dict[str, Any]) -> str:
    page_start = payload.get("page_start")
    page_end = payload.get("page_end")
    page_number = payload.get("page_number")

    if page_start is not None and page_end is not None:
        if page_start == page_end:
            return str(page_start)

        return f"{page_start}-{page_end}"

    if page_number is not None:
        return str(page_number)

    return "N/A"


def _trim_code(code: str, max_code_chars: int) -> str:
    if len(code) <= max_code_chars:
        return code

    return (
        code[:max_code_chars]
        + "\n\n# --- Code truncated because it exceeded max_code_chars ---"
    )


def build_code_review_prompt(
    code: str,
    language: str,
    code_context: str,
    review_focus: list[str],
    matches: list[dict[str, Any]],
    detected_domains: list[str],
    search_domains: list[str],
    rewritten_query: str | None = None,
    max_context_chars: int = 16000,
    max_code_chars: int = 12000,
) -> str:
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

    source_context = "\n\n---\n\n".join(context_blocks)

    rewrite_section = ""
    if rewritten_query:
        rewrite_section = f"\nRewritten retrieval query:\n{rewritten_query}\n"

    focus_text = (
        "\n".join(f"- {item}" for item in review_focus)
        if review_focus
        else "- correctness\n- security\n- maintainability\n- testing"
    )

    trimmed_code = _trim_code(code, max_code_chars=max_code_chars)

    return f"""
You are a senior code reviewer, backend engineer, security engineer, and reliability engineer.

Review the user's code using only the provided ebook sources and the code shown below.

Language:
{language}

Code context:
{code_context}

Review focus:
{focus_text}

Detected domains:
{", ".join(detected_domains)}

Search domains:
{", ".join(search_domains) if search_domains else "all"}
{rewrite_section}

Rules:
1. Use the provided code as the review target.
2. Use the ebook sources to support engineering recommendations.
3. Do not invent book titles, authors, citations, page numbers, or unsupported claims.
4. Cite ebook sources inline using [Source 1], [Source 2], etc.
5. Be direct and practical.
6. Separate confirmed issues from optional improvements.
7. If the sources are insufficient for a specific review area, say so clearly.
8. Do not rewrite the entire code unless necessary.
9. Prefer small, safe patches and explain why.
10. Use PDF page ranges and chunk metadata when referring to sources.

Retrieved ebook sources:
{source_context}

Code to review:
```{language}
{trimmed_code}

Return the code review in this structure:

Code Review
1. Executive Summary

Give a direct summary of the code quality.

2. What the Code Appears to Do

Explain the purpose of the code in plain terms.

3. Critical Issues

List bugs, broken logic, unsafe assumptions, or likely runtime failures.

4. Security Issues

Review:

input validation
secrets
unsafe file handling
injection risk
authentication/authorization assumptions
logging sensitive data
dependency risk
5. Reliability Issues

Review:

error handling
retries
timeouts
idempotency
failure modes
resource usage
6. Performance Issues

Review:

inefficient loops
unnecessary network calls
memory usage
blocking operations
scalability bottlenecks
7. Maintainability Issues

Review:

naming
structure
separation of concerns
duplication
typing
comments
testability
8. Recommended Fixes

Group fixes as:

Must fix
Should improve
Nice to have
9. Suggested Patch

Provide focused code snippets only for the most important fixes.

10. Testing Recommendations

List unit, integration, edge-case, and regression tests.

11. Source-Backed Notes

Map important recommendations to the retrieved sources.

12. Weak Areas / Missing Sources

State what could not be strongly supported by the retrieved ebook sources.
""".strip()