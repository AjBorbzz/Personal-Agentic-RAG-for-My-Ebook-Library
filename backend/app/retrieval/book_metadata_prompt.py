import json


def build_book_metadata_prompt(
    *,
    filename: str | None,
    existing_metadata: dict,
    source_text: str,
) -> str:
    existing_json = json.dumps(
        existing_metadata,
        indent=2,
        ensure_ascii=False,
    )

    return f"""
You are extracting structured metadata from a technical ebook.

Return only one valid JSON object. Do not include Markdown, commentary,
code fences, or text outside the JSON object.

Required JSON structure:

{{
  "title": string or null,
  "author": string or null,
  "subtitle": string or null,
  "publisher": string or null,
  "edition": string or null,
  "isbn_10": string or null,
  "isbn_13": string or null,
  "language": string or null,
  "publication_year": integer or null,
  "description": string or null,
  "difficulty_level": "beginner", "intermediate", "advanced", "mixed", or "unknown",
  "topics": [string],
  "technologies": [string],
  "tags": [string],
  "prerequisite_skills": [string],
  "metadata_confidence": number between 0 and 1
}}

Rules:

1. Use only information supported by the filename, existing metadata,
   or supplied book text.
2. Do not invent an ISBN, publisher, edition, author, or publication year.
3. Return null for unsupported bibliographic fields.
4. Keep description between one and three sentences.
5. Return at most 15 topics.
6. Return at most 15 technologies.
7. Return at most 20 tags.
8. Return at most 10 prerequisite skills.
9. Use concise lowercase values for topics, technologies, tags, and prerequisites.
10. Difficulty should describe the overall expected reader level.
11. Set metadata_confidence lower when bibliographic information is uncertain.
12. Existing metadata may help, but verify it against the supplied text.

Filename:
{filename or "Unknown"}

Existing metadata:
{existing_json}

Book text sample:
--- BEGIN BOOK TEXT ---
{source_text}
--- END BOOK TEXT ---
""".strip()