import json
import re
from pathlib import Path
from typing import Any

from app.models.document import Document
from app.retrieval.book_metadata_prompt import (
    build_book_metadata_prompt,
)
from app.schemas.document_enrichment import EnrichedBookMetadata
# from app.services.ollama import generate_text
from app.services.ollama import generate_structured_text
from pydantic import ValidationError
import asyncio


ENRICHABLE_FIELDS = (
    "title",
    "author",
    "subtitle",
    "publisher",
    "edition",
    "isbn_10",
    "isbn_13",
    "language",
    "publication_year",
    "description",
    "difficulty_level",
    "topics",
    "technologies",
    "tags",
    "prerequisite_skills",
)


def _clean_string(value: Any) -> str | None:
    if value is None:
        return None

    cleaned = " ".join(str(value).split()).strip()

    if not cleaned:
        return None

    return cleaned


def _clean_list(values: Any, maximum: int) -> list[str]:
    if not isinstance(values, list):
        return []

    results: list[str] = []
    seen: set[str] = set()

    for value in values:
        cleaned = _clean_string(value)

        if not cleaned:
            continue

        normalized = cleaned.lower()

        if normalized in seen:
            continue

        seen.add(normalized)
        results.append(normalized)

        if len(results) >= maximum:
            break

    return results


def _normalize_candidate(candidate: EnrichedBookMetadata,) -> EnrichedBookMetadata:
    candidate.title = _clean_string(candidate.title)
    candidate.author = _clean_string(candidate.author)
    candidate.subtitle = _clean_string(candidate.subtitle)
    candidate.publisher = _clean_string(candidate.publisher)
    candidate.edition = _clean_string(candidate.edition)
    candidate.isbn_10 = _clean_string(candidate.isbn_10)
    candidate.isbn_13 = _clean_string(candidate.isbn_13)
    candidate.language = _clean_string(candidate.language)
    candidate.description = _clean_string(candidate.description)

    allowed_difficulties = {
        "beginner",
        "intermediate",
        "advanced",
        "mixed",
        "unknown",
    }

    difficulty = (
        _clean_string(candidate.difficulty_level)
        or "unknown"
    ).lower()

    if difficulty not in allowed_difficulties:
        difficulty = "unknown"

    candidate.difficulty_level = difficulty

    candidate.topics = _clean_list(
        candidate.topics,
        maximum=15,
    )
    candidate.technologies = _clean_list(
        candidate.technologies,
        maximum=15,
    )
    candidate.tags = _clean_list(
        candidate.tags,
        maximum=20,
    )
    candidate.prerequisite_skills = _clean_list(
        candidate.prerequisite_skills,
        maximum=10,
    )

    return candidate


def _extract_json_object(raw_response: str) -> dict[str, Any]:
    cleaned = raw_response.strip()

    cleaned = re.sub(
        r"^```(?:json)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"\s*```$",
        "",
        cleaned,
    )

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError(
            "The language model did not return a JSON object."
        )

    json_text = cleaned[start : end + 1]

    parsed = json.loads(json_text)

    if not isinstance(parsed, dict):
        raise ValueError(
            "The metadata response must be a JSON object."
        )

    return parsed


def _read_json_text(path: Path) -> str | None:
    try:
        data = json.loads(
            path.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        )
    except (OSError, json.JSONDecodeError):
        return None

    if isinstance(data, dict):
        for key in (
            "text",
            "full_text",
            "content",
            "extracted_text",
        ):
            value = data.get(key)

            if isinstance(value, str) and value.strip():
                return value

        chunks = data.get("chunks")

        if isinstance(chunks, list):
            texts: list[str] = []

            for chunk in chunks:
                if not isinstance(chunk, dict):
                    continue

                chunk_text = (
                    chunk.get("chunk_text")
                    or chunk.get("text")
                    or chunk.get("content")
                )

                if isinstance(chunk_text, str):
                    texts.append(chunk_text)

            if texts:
                return "\n\n".join(texts)

    if isinstance(data, list):
        texts = []

        for item in data:
            if not isinstance(item, dict):
                continue

            item_text = (
                item.get("chunk_text")
                or item.get("text")
                or item.get("content")
            )

            if isinstance(item_text, str):
                texts.append(item_text)

        if texts:
            return "\n\n".join(texts)

    return None


def load_document_text(document: Document) -> str:
    candidate_paths = [
        document.parsed_output_path,
        document.chunks_output_path,
    ]

    for path_value in candidate_paths:
        if not path_value:
            continue

        path = Path(path_value)

        if not path.exists():
            continue

        if path.suffix.lower() == ".json":
            extracted = _read_json_text(path)

            if extracted:
                return extracted
        else:
            text = path.read_text(
                encoding="utf-8",
                errors="ignore",
            )

            if text.strip():
                return text

    if document.saved_path:
        saved_path = Path(document.saved_path)

        if (
            saved_path.exists()
            and saved_path.suffix.lower() == ".txt"
        ):
            text = saved_path.read_text(
                encoding="utf-8",
                errors="ignore",
            )

            if text.strip():
                return text

    raise FileNotFoundError(
        "No readable parsed text or chunk output was found "
        f"for document {document.document_id}."
    )


def sample_document_text(
    text: str,
    maximum_characters: int,
) -> tuple[str, bool]:
    cleaned = text.strip()

    if len(cleaned) <= maximum_characters:
        return cleaned, False

    section_size = maximum_characters // 3
    middle_start = max(
        0,
        (len(cleaned) // 2) - (section_size // 2),
    )
    middle_end = middle_start + section_size

    sample = "\n\n".join(
        [
            "### BEGINNING OF BOOK",
            cleaned[:section_size],
            "### MIDDLE OF BOOK",
            cleaned[middle_start:middle_end],
            "### END OF BOOK",
            cleaned[-section_size:],
        ]
    )

    return sample, True


def _existing_metadata(document: Document) -> dict[str, Any]:
    return {
        "title": document.title,
        "author": document.author,
        "subtitle": document.subtitle,
        "publisher": document.publisher,
        "edition": document.edition,
        "isbn_10": document.isbn_10,
        "isbn_13": document.isbn_13,
        "language": document.language,
        "publication_year": document.publication_year,
        "primary_domain": document.primary_domain,
        "domains": document.domains,
        "difficulty_level": document.difficulty_level,
        "topics": document.topics,
        "technologies": document.technologies,
        "tags": document.tags,
        "prerequisite_skills": document.prerequisite_skills,
    }


async def generate_metadata_candidate(
            document: Document,
            maximum_source_characters: int,
        ) -> tuple[EnrichedBookMetadata, int, bool]:
    full_text = load_document_text(document)

    source_sample, was_truncated = sample_document_text(
        full_text,
        maximum_source_characters,
    )

    prompt = build_book_metadata_prompt(
        filename=document.filename,
        existing_metadata=_existing_metadata(document),
        source_text=source_sample,
    )

    try:
        raw_response = await asyncio.wait_for(generate_structured_text(
            prompt=prompt,
            json_schema=EnrichedBookMetadata.model_json_schema(),
        ), timeout=180)

        candidate = EnrichedBookMetadata.model_validate_json(
            raw_response
        )

    except ValidationError as error:
        raise ValueError(
            "Ollama returned JSON, but it did not match the "
            f"metadata schema: {error}"
        ) from error

    candidate = _normalize_candidate(candidate)

    return candidate, len(source_sample), was_truncated


def _has_value(value: Any) -> bool:
    if value is None:
        return False

    if isinstance(value, str):
        return bool(value.strip())

    if isinstance(value, (list, dict, tuple, set)):
        return bool(value)

    return True

def build_metadata_updates(
    document: Document,
    candidate: EnrichedBookMetadata,
    overwrite_existing: bool,
) -> dict[str, Any]:
    updates: dict[str, Any] = {}

    candidate_data = candidate.model_dump()

    for field_name in ENRICHABLE_FIELDS:
        proposed_value = candidate_data.get(field_name)

        if not _has_value(proposed_value):
            continue

        current_value = getattr(
            document,
            field_name,
            None,
        )

        if overwrite_existing or not _has_value(current_value):
            updates[field_name] = proposed_value

    return updates