#!/usr/bin/env python3

import argparse
from pathlib import Path

import httpx


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Review a local code file using the Code Review Agent."
    )

    parser.add_argument("--file", required=True, type=Path)
    parser.add_argument("--language", default="python")
    parser.add_argument("--code-context", default="No additional context provided.")
    parser.add_argument("--review-focus", nargs="*", default=None)
    parser.add_argument("--domains", nargs="*", default=None)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--max-code-chars", type=int, default=12000)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--output", type=Path, default=Path("data/exports/code_review.md"))

    args = parser.parse_args()

    if not args.file.exists() or not args.file.is_file():
        raise FileNotFoundError(f"Code file not found: {args.file}")

    code = args.file.read_text(encoding="utf-8", errors="ignore")

    payload = {
        "code": code,
        "language": args.language,
        "code_context": args.code_context,
        "domains": args.domains,
        "limit": args.limit,
        "max_code_chars": args.max_code_chars,
    }

    if args.review_focus:
        payload["review_focus"] = args.review_focus

    timeout = httpx.Timeout(connect=10.0, read=1800.0, write=60.0, pool=10.0)

    with httpx.Client(timeout=timeout) as client:
        response = client.post(
            f"{args.base_url.rstrip('/')}/code-review",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    args.output.parent.mkdir(parents=True, exist_ok=True)

    markdown = data["code_review"]

    markdown += "\n\n---\n\n# Reviewed File\n\n"
    markdown += f"- File: `{args.file}`\n"
    markdown += f"- Language: `{args.language}`\n"
    markdown += f"- Context: {args.code_context}\n"

    markdown += "\n\n# Retrieved Sources\n\n"

    for source in data.get("sources", []):
        page_start = source.get("page_start")
        page_end = source.get("page_end")

        if page_start is not None and page_end is not None:
            pages = f"{page_start}-{page_end}" if page_start != page_end else str(page_start)
        else:
            pages = str(source.get("page_number") or "N/A")

        markdown += (
            f"- Source {source.get('source_number')}: "
            f"{source.get('title')} | "
            f"File: {source.get('filename')} | "
            f"Pages: {pages} | "
            f"Chunk: {source.get('chunk_index')} | "
            f"Domains: {', '.join(source.get('domains') or [])}\n"
        )

    args.output.write_text(markdown, encoding="utf-8")

    print(f"Saved code review to: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())