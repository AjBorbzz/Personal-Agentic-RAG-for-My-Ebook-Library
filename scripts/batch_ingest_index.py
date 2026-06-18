#!/usr/bin/env python3

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

import httpx


SUPPORTED_EXTENSIONS = {".pdf", ".epub", ".txt"}


def sha256_file(file_path: Path) -> str:
    hasher = hashlib.sha256()

    with file_path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(block)

    return hasher.hexdigest()


def load_manifest(manifest_path: Path) -> dict[str, Any]:
    if not manifest_path.exists():
        return {
            "files": {},
            "created_at": time.time(),
            "updated_at": time.time(),
        }

    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return {
            "files": {},
            "created_at": time.time(),
            "updated_at": time.time(),
        }


def save_manifest(manifest_path: Path, manifest: dict[str, Any]) -> None:
    manifest["updated_at"] = time.time()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def discover_files(input_dir: Path, recursive: bool) -> list[Path]:
    pattern = "**/*" if recursive else "*"

    files = [
        path
        for path in input_dir.glob(pattern)
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    return sorted(files)


def health_check(client: httpx.Client, base_url: str) -> None:
    response = client.get(f"{base_url}/health")
    response.raise_for_status()


def ingest_file(client: httpx.Client, base_url: str, file_path: Path) -> dict[str, Any]:
    with file_path.open("rb") as file:
        files = {
            "file": (
                file_path.name,
                file,
                "application/octet-stream",
            )
        }

        response = client.post(
            f"{base_url}/ingest",
            files=files,
        )

    response.raise_for_status()
    return response.json()


def index_document(
    client: httpx.Client,
    base_url: str,
    document_id: str,
) -> dict[str, Any]:
    response = client.post(f"{base_url}/index/{document_id}")
    response.raise_for_status()
    return response.json()


def process_file(
    client: httpx.Client,
    base_url: str,
    file_path: Path,
    manifest: dict[str, Any],
    manifest_path: Path,
    should_index: bool,
    force: bool,
) -> None:
    file_hash = sha256_file(file_path)
    file_key = str(file_path.resolve())

    previous = manifest["files"].get(file_key)

    if (
        previous
        and previous.get("file_hash") == file_hash
        and previous.get("status") == "indexed"
        and not force
    ):
        print(f"[SKIP] Already indexed: {file_path}")
        return

    if (
        previous
        and previous.get("file_hash") == file_hash
        and previous.get("status") == "ingested"
        and not should_index
        and not force
    ):
        print(f"[SKIP] Already ingested: {file_path}")
        return

    record = {
        "file_path": file_key,
        "filename": file_path.name,
        "file_hash": file_hash,
        "extension": file_path.suffix.lower(),
        "status": "started",
        "document_id": None,
        "ingest_response": None,
        "index_response": None,
        "error": None,
        "started_at": time.time(),
        "finished_at": None,
    }

    manifest["files"][file_key] = record
    save_manifest(manifest_path, manifest)

    try:
        print(f"[INGEST] {file_path}")
        ingest_response = ingest_file(client, base_url, file_path)

        document_id = ingest_response["document_id"]

        record["status"] = "ingested"
        record["document_id"] = document_id
        record["ingest_response"] = {
            "document_id": ingest_response.get("document_id"),
            "filename": ingest_response.get("filename"),
            "file_type": ingest_response.get("file_type"),
            "title": ingest_response.get("title"),
            "author": ingest_response.get("author"),
            "page_count": ingest_response.get("page_count"),
            "primary_domain": ingest_response.get("primary_domain"),
            "domains": ingest_response.get("domains"),
            "text_characters": ingest_response.get("text_characters"),
            "chunk_count": ingest_response.get("chunk_count"),
            "elapsed_seconds": ingest_response.get("elapsed_seconds"),
        }

        save_manifest(manifest_path, manifest)

        if should_index:
            print(f"[INDEX] {file_path.name} -> {document_id}")
            index_response = index_document(client, base_url, document_id)

            record["status"] = "indexed"
            record["index_response"] = {
                "document_id": index_response.get("document_id"),
                "collection_name": index_response.get("collection_name"),
                "primary_domain": index_response.get("primary_domain"),
                "domains": index_response.get("domains"),
                "chunk_count": index_response.get("chunk_count"),
                "indexed_count": index_response.get("indexed_count"),
                "embedding_dimension": index_response.get("embedding_dimension"),
                "elapsed_seconds": index_response.get("elapsed_seconds"),
            }

        record["finished_at"] = time.time()
        save_manifest(manifest_path, manifest)

        print(f"[OK] {file_path.name}")

    except Exception as error:
        record["status"] = "failed"
        record["error"] = str(error)
        record["finished_at"] = time.time()
        save_manifest(manifest_path, manifest)

        print(f"[FAILED] {file_path}")
        print(f"         {error}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Batch ingest and optionally index ebooks into the local RAG system."
    )

    parser.add_argument(
        "input_dir",
        type=Path,
        help="Directory containing PDFs, EPUBs, or TXT files.",
    )

    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="FastAPI base URL. Default: http://localhost:8000",
    )

    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/batch_ingest_manifest.json"),
        help="Manifest file used to skip already processed files.",
    )

    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Search files recursively.",
    )

    parser.add_argument(
        "--no-index",
        action="store_true",
        help="Only ingest files. Do not index them.",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Reprocess files even if already indexed.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process only the first N discovered files.",
    )

    args = parser.parse_args()

    input_dir = args.input_dir

    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Input directory does not exist or is not a directory: {input_dir}")
        return 1

    files = discover_files(input_dir, recursive=args.recursive)

    if args.limit is not None:
        files = files[: args.limit]

    if not files:
        print("No supported files found.")
        return 0

    print(f"Discovered {len(files)} file(s).")

    manifest = load_manifest(args.manifest)

    timeout = httpx.Timeout(
        connect=10.0,
        read=1800.0,
        write=1800.0,
        pool=10.0,
    )

    with httpx.Client(timeout=timeout) as client:
        try:
            health_check(client, args.base_url)
        except Exception as error:
            print(f"Backend health check failed: {error}")
            print("Start FastAPI first:")
            print("  cd backend")
            print("  source .venv/bin/activate")
            print("  uvicorn app.main:app --reload --port 8000")
            return 1

        for file_path in files:
            process_file(
                client=client,
                base_url=args.base_url.rstrip("/"),
                file_path=file_path,
                manifest=manifest,
                manifest_path=args.manifest,
                should_index=not args.no_index,
                force=args.force,
            )

    total = len(manifest.get("files", {}))
    indexed = sum(
        1
        for item in manifest["files"].values()
        if item.get("status") == "indexed"
    )
    ingested = sum(
        1
        for item in manifest["files"].values()
        if item.get("status") == "ingested"
    )
    failed = sum(
        1
        for item in manifest["files"].values()
        if item.get("status") == "failed"
    )

    print("")
    print("Batch summary")
    print(f"Total tracked: {total}")
    print(f"Indexed:       {indexed}")
    print(f"Ingested only: {ingested}")
    print(f"Failed:        {failed}")
    print(f"Manifest:      {args.manifest}")

    return 0


if __name__ == "__main__":
    sys.exit(main())