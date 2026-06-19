#!/usr/bin/env python3

import argparse
from pathlib import Path

import httpx


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate an architecture review and save it as Markdown."
    )

    parser.add_argument("--system-description", required=True)
    parser.add_argument("--goal", action="append", default=[])
    parser.add_argument("--constraint", action="append", default=[])
    parser.add_argument("--review-focus", nargs="*", default=None)
    parser.add_argument("--target-scale", default="small to medium production workload")
    parser.add_argument("--domains", nargs="*", default=None)
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--output", type=Path, default=Path("data/exports/architecture_review.md"))

    args = parser.parse_args()

    payload = {
        "system_description": args.system_description,
        "goals": args.goal,
        "constraints": args.constraint,
        "target_scale": args.target_scale,
        "domains": args.domains,
        "limit": args.limit,
    }

    if args.review_focus:
        payload["review_focus"] = args.review_focus

    timeout = httpx.Timeout(connect=10.0, read=1800.0, write=60.0, pool=10.0)

    with httpx.Client(timeout=timeout) as client:
        response = client.post(
            f"{args.base_url.rstrip('/')}/architecture-review",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    args.output.parent.mkdir(parents=True, exist_ok=True)

    markdown = data["architecture_review"]

    markdown += "\n\n---\n\n# Retrieved Sources\n\n"

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

    print(f"Saved architecture review to: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())