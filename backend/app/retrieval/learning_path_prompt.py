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


def build_learning_path_prompt(
    goal: str,
    matches: list[dict[str, Any]],
    duration_weeks: int,
    hours_per_week: int,
    current_level: str,
    target_level: str,
    detected_domains: list[str],
    search_domains: list[str],
    rewritten_query: str | None = None,
    max_context_chars: int = 16000,
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

    context = "\n\n---\n\n".join(context_blocks)

    rewrite_section = ""
    if rewritten_query:
        rewrite_section = f"\nRewritten retrieval query:\n{rewritten_query}\n"

    return f"""
You are a senior technical mentor creating a source-backed learning path from the user's private ebook library.

User goal:
{goal}

Planning constraints:
- Duration: {duration_weeks} weeks
- Available study/build time: {hours_per_week} hours per week
- Current level: {current_level}
- Target level: {target_level}
- Detected domains: {", ".join(detected_domains)}
- Search domains: {", ".join(search_domains) if search_domains else "all"}
{rewrite_section}

Rules:
1. Use only the provided ebook sources.
2. Do not invent book titles, authors, citations, page numbers, or chapters.
3. Cite sources inline using [Source 1], [Source 2], etc.
4. If the sources are insufficient, say which parts are not well supported.
5. Make the plan practical and implementation-driven.
6. Every week must produce a visible artifact.
7. Favor projects, code, architecture diagrams, documentation, and tests over passive reading.
8. Use PDF page ranges and chunk metadata when referring to sources.

Retrieved ebook sources:
{context}

Return the learning path in this structure:

# Learning Path Title

## 1. Goal Interpretation
Explain what the user is trying to become or build.

## 2. Detected Domains
List the technical domains involved.

## 3. Skill Roadmap
Group the skills into:
- Foundation
- Intermediate
- Advanced
- Portfolio Proof

## 4. Weekly Plan
For each week, include:
- Theme
- Concepts
- Ebook-backed sources
- Hands-on task
- Output artifact
- Success criteria

## 5. Mini-Projects
List 3 to 5 mini-projects that reinforce the path.

## 6. Portfolio Artifact Plan
List what should be published or documented.

## 7. Quiz and Review Questions
Create scenario-based questions.

## 8. Gaps and Missing Sources
State what is weakly covered by the retrieved sources.
""".strip()