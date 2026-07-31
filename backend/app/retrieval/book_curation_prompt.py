import json


def build_book_curation_prompt(
    *,
    current_year: int,
    metadata: dict,
    source_text: str,
) -> str:
    metadata_json = json.dumps(
        metadata,
        indent=2,
        ensure_ascii=False,
    )

    return f"""
You are evaluating a technical ebook for inclusion in a curated
personal engineering library.

Return only one valid JSON object matching the supplied schema.
Do not include Markdown, commentary, code fences, or text outside JSON.

The evaluation is based only on the supplied metadata and text sample.
Do not invent facts about the author, publisher, reception, or authority.

Current year:
{current_year}

Score definitions:

- technical_depth_score:
  Depth, rigor, conceptual detail, and advanced coverage.

- practicality_score:
  Hands-on usefulness, examples, implementation guidance, exercises,
  troubleshooting value, and applicability to real projects.

- freshness_score:
  How current the material appears relative to {current_year}, based on
  publication year, editions, tool versions, APIs, practices, and concepts
  visible in the supplied material.

- authority_score:
  Apparent rigor, consistency, evidence, technical correctness, and quality
  of explanation. Do not infer reputation that is not present in the source.

- clarity_score:
  Organization, readability, examples, explanations, and progression.

- outdated_risk_score:
  Risk that important guidance is obsolete or unsafe.
  0 means very low outdated risk.
  100 means extremely high outdated risk.

Allowed audience_level values:
- beginner
- intermediate
- advanced
- mixed

Allowed recommended_role values:
- foundational
- practical_guide
- reference
- advanced_specialist
- supplementary
- historical
- redundant
- avoid

Allowed library_priority values:
- essential
- high
- medium
- low
- archive

Rules:

1. Evaluate only what the supplied material supports.
2. Do not assign a high authority score merely because the book has
   a recognizable title or author.
3. Do not claim a technology is obsolete unless the text, version,
   publication year, or known version metadata supports that concern.
4. Keep curator_summary between two and five sentences.
5. Keep unique_value to one or two sentences.
6. Return at most 8 strengths.
7. Return at most 8 weaknesses.
8. Return at most 8 best_for entries.
9. Return at most 6 not_recommended_for entries.
10. Return at most 10 outdated_topics.
11. Use concise lowercase list values.
12. Use lower confidence when only a small sample is available.
13. overall_score may be zero because the application recalculates it
    deterministically from the component scores.

Trusted or available metadata:
{metadata_json}

Book content sample:
--- BEGIN BOOK SAMPLE ---
{source_text}
--- END BOOK SAMPLE ---
""".strip()