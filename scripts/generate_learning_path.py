#!/usr/bin/env python3

import argparse
from pathlib import Path

import httpx


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a learning path and save it as Markdown."
    )

    parser.add_argument("--goal", required=True)
    parser.add_argument("--duration-weeks", type=int, default=8)
    parser.add_argument("--hours-per-week", type=int, default=5)
    parser.add_argument("--current-level", default="intermediate")
    parser.add_argument("--target-level", default="advanced")
    parser.add_argument("--domains", nargs="*", default=None)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--output", type=Path, default=Path("data/exports/learning_path.md"))

    args = parser.parse_args()

    payload = {
        "goal": args.goal,
        "duration_weeks": args.duration_weeks,
        "hours_per_week": args.hours_per_week,
        "current_level": args.current_level,
        "target_level": args.target_level,
        "domains": args.domains,
        "limit": args.limit,
    }

    timeout = httpx.Timeout(connect=10.0, read=1800.0, write=60.0, pool=10.0)

    with httpx.Client(timeout=timeout) as client:
        response = client.post(
            f"{args.base_url.rstrip('/')}/learning-path",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    args.output.parent.mkdir(parents=True, exist_ok=True)

    markdown = data["learning_path"]

    sources = data.get("sources", [])

    markdown += "\n\n---\n\n# Retrieved Sources\n\n"

    for source in sources:
        markdown += (
            f"- Source {source.get('source_number')}: "
            f"{source.get('title')} | "
            f"File: {source.get('filename')} | "
            f"Pages: {source.get('page_start')}-{source.get('page_end')} | "
            f"Chunk: {source.get('chunk_index')} | "
            f"Domains: {', '.join(source.get('domains') or [])}\n"
        )

    args.output.write_text(markdown, encoding="utf-8")

    print(f"Saved learning path to: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())