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


def build_architecture_review_prompt(
    system_description: str,
    matches: list[dict[str, Any]],
    review_focus: list[str],
    goals: list[str],
    constraints: list[str],
    target_scale: str,
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

    goals_text = "\n".join(f"- {goal}" for goal in goals) if goals else "- Not specified"
    constraints_text = "\n".join(f"- {item}" for item in constraints) if constraints else "- Not specified"
    focus_text = "\n".join(f"- {item}" for item in review_focus) if review_focus else "- General architecture review"

    return f"""
You are a senior software architect, security engineer, and reliability reviewer.

Review the user's system architecture using only the provided ebook sources.

System description:
{system_description}

Goals:
{goals_text}

Constraints:
{constraints_text}

Target scale:
{target_scale}

Review focus:
{focus_text}

Detected domains:
{", ".join(detected_domains)}

Search domains:
{", ".join(search_domains) if search_domains else "all"}
{rewrite_section}

Rules:
1. Use only the provided ebook sources.
2. Do not invent book titles, authors, citations, page numbers, or unsupported claims.
3. Cite sources inline using [Source 1], [Source 2], etc.
4. If the retrieved sources are insufficient for a review area, say so clearly.
5. Be direct and practical.
6. Prioritize engineering risks, tradeoffs, implementation gaps, security issues, and reliability concerns.
7. Use PDF page ranges and chunk metadata when referring to sources.

Retrieved ebook sources:
{context}

Return the architecture review in this structure:

# Architecture Review

## 1. Executive Assessment
Give a direct overall judgment: strong, acceptable, risky, incomplete, or over-engineered.

## 2. Architecture Summary
Summarize the user's design in your own words.

## 3. Strengths
List what is good about the design and why.

## 4. Major Risks
List the biggest risks. Include severity: Low, Medium, High, Critical.

## 5. Missing Components
List important missing components or unclear areas.

## 6. Security Review
Review:
- authentication
- authorization
- secrets management
- input validation
- data privacy
- logging
- abuse prevention
- dependency risk

## 7. Scalability Review
Review:
- bottlenecks
- database scaling
- queue/worker design
- vector search scaling
- caching
- rate limits
- background jobs

## 8. Reliability Review
Review:
- retries
- timeouts
- failure modes
- fallback behavior
- backups
- idempotency
- monitoring

## 9. Data Model Review
Review the database/storage design and suggest improvements.

## 10. API and Service Boundary Review
Review endpoints, service responsibilities, coupling, and separation of concerns.

## 11. Observability Review
Review logs, metrics, tracing, audit trails, and operational visibility.

## 12. Deployment Review
Review local, staging, production, containerization, environment variables, and rollout strategy.

## 13. Recommended Improvements
Provide prioritized improvements:
- Must fix
- Should improve
- Nice to have

## 14. Revised Architecture Proposal
Suggest a better architecture if needed.

## 15. Implementation Checklist
Give a practical checklist the user can follow.

## 16. Source-Backed Notes
Map important recommendations to the retrieved sources.

## 17. Weak Areas / Missing Sources
State what could not be fully reviewed because the retrieved sources were weak or incomplete.
""".strip()