#!/usr/bin/env python3

import argparse
from pathlib import Path

import httpx


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a portfolio project plan and save it as Markdown."
    )

    parser.add_argument("--goal", required=True)
    parser.add_argument("--target-role", default="AI Security Engineer")
    parser.add_argument("--project-level", default="intermediate")
    parser.add_argument("--duration-weeks", type=int, default=6)
    parser.add_argument("--domains", nargs="*", default=None)
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--output", type=Path, default=Path("data/exports/project_plan.md"))

    args = parser.parse_args()

    payload = {
        "goal": args.goal,
        "target_role": args.target_role,
        "project_level": args.project_level,
        "duration_weeks": args.duration_weeks,
        "domains": args.domains,
        "limit": args.limit,
    }

    timeout = httpx.Timeout(connect=10.0, read=1800.0, write=60.0, pool=10.0)

    with httpx.Client(timeout=timeout) as client:
        response = client.post(
            f"{args.base_url.rstrip('/')}/project-generator",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    args.output.parent.mkdir(parents=True, exist_ok=True)

    markdown = data["project_plan"]

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

    print(f"Saved project plan to: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())