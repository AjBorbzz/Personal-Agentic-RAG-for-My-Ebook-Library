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


def build_project_generator_prompt(
    goal: str,
    matches: list[dict[str, Any]],
    target_role: str,
    project_level: str,
    duration_weeks: int,
    detected_domains: list[str],
    search_domains: list[str],
    rewritten_query: str | None = None,
    max_context_chars: int = 18000,
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
You are a senior software architect and portfolio advisor.

Create a portfolio-grade project plan using only the user's private ebook sources.

User project goal:
{goal}

Target role:
{target_role}

Project level:
{project_level}

Expected build duration:
{duration_weeks} weeks

Detected domains:
{", ".join(detected_domains)}

Search domains:
{", ".join(search_domains) if search_domains else "all"}
{rewrite_section}

Rules:
1. Use only the provided ebook sources.
2. Do not invent book titles, authors, citations, page numbers, or unsupported claims.
3. Cite sources inline using [Source 1], [Source 2], etc.
4. The project must be buildable.
5. The output must be useful for GitHub, resume, portfolio, and interview discussion.
6. Prefer practical engineering artifacts over vague learning.
7. Include security, testing, observability, and deployment.
8. Use PDF page ranges and chunk metadata when referring to sources.
9. If sources are weak, state the weak areas clearly.

Retrieved ebook sources:
{context}

Return the project plan in this structure:

# Project Title

## 1. Executive Summary
Explain the project in one strong paragraph.

## 2. Problem Statement
Describe the real engineering problem.

## 3. Target Users
List who would use this system.

## 4. Core Use Cases
List 5 to 8 practical use cases.

## 5. Architecture Overview
Describe the major components and data flow.

## 6. Suggested Tech Stack
Group by:
- Frontend
- Backend
- Database
- Vector Store
- AI/LLM
- Queue/Workers
- Observability
- Deployment

## 7. Core Features
Separate into:
- MVP
- Intermediate
- Advanced

## 8. API Endpoints
List endpoint, method, purpose, request shape, response shape.

## 9. Database Schema
Propose tables or collections with important fields.

## 10. Security Controls
Include authentication, authorization, input validation, secrets, logging, privacy, abuse prevention.

## 11. Observability and Reliability
Include logs, metrics, tracing, retries, failure modes, backup strategy.

## 12. Implementation Plan
Break into weekly phases for {duration_weeks} weeks.

## 13. Testing Strategy
Include unit, integration, API, retrieval quality, and security tests.

## 14. GitHub README Structure
Provide a complete README outline.

## 15. Portfolio Proof
List diagrams, screenshots, demo video, sample data, documentation, and case study.

## 16. Resume Bullets
Write 5 strong resume bullets.

## 17. Interview Talking Points
List 10 points the user can explain in interviews.

## 18. Source-Backed Notes
List which sources support the project decisions.

## 19. Weak Areas / Missing Sources
State what needs more ebook coverage or external validation.
""".strip()