from app.schemas.book_skill_candidate import (
    ShortlistedSkillResponse,
)


def build_book_skill_mapping_prompt(
    *,
    document_metadata: dict,
    source_sample: str,
    shortlisted_skills: list[
        ShortlistedSkillResponse
    ],
    maximum_mappings: int,
) -> str:
    skill_lines = []

    for skill in shortlisted_skills:
        matched_terms = ", ".join(
            skill.matched_terms
        ) or "none"

        skill_lines.append(
            "\n".join(
                [
                    f"- slug: {skill.slug}",
                    f"  name: {skill.name}",
                    (
                        "  domain: "
                        f"{skill.domain_name}"
                    ),
                    (
                        "  category: "
                        f"{skill.category_name or 'none'}"
                    ),
                    (
                        "  skill_type: "
                        f"{skill.skill_type}"
                    ),
                    (
                        "  difficulty: "
                        f"{skill.difficulty_level}"
                    ),
                    (
                        "  deterministic_matches: "
                        f"{matched_terms}"
                    ),
                ]
            )
        )

    candidate_skill_text = "\n".join(
        skill_lines
    )

    return f"""
You are evaluating a technical ebook against a
controlled skill taxonomy.

Your task is to identify only the skills that the
book meaningfully teaches.

STRICT RULES:

1. Choose skills only from the supplied candidate
   skill list.
2. Return at most {maximum_mappings} mappings.
3. Omit a skill when there is insufficient evidence.
4. Do not infer coverage merely because a technology
   is mentioned once.
5. A primary skill must be a major subject of the
   book. Mark no more than three skills as primary.
6. Evidence excerpts must be copied from the supplied
   source text. Do not invent quotations.
7. Do not invent chapter names, section names, page
   numbers, or technical topics.
8. Use null for location fields that are not clearly
   present in the source.
9. The output must conform exactly to the supplied
   JSON schema.

COVERAGE LEVELS:

- mention:
  Named briefly, with little teaching value.

- introductory:
  Explains terminology and basic concepts.

- working:
  Provides enough guidance for routine practical use.

- advanced:
  Covers difficult implementation, design, or
  troubleshooting concerns.

- comprehensive:
  Treats the skill as a central subject with broad
  and deep coverage.

SCORING:

- relevance_score:
  How directly the book relates to the skill.

- coverage_score:
  How much of the skill's scope is covered.

- depth_score:
  How deeply the book explains the skill.

- practicality_score:
  How much implementation, exercises, examples,
  procedures, or applied guidance is provided.

- confidence:
  Confidence in this mapping based only on the
  supplied evidence.

PROFICIENCY LEVELS:

- awareness
- foundational
- working
- advanced
- expert

The entry level is the recommended proficiency before
reading the material.

The exit level is the likely proficiency after
successfully studying and applying the material.

BOOK METADATA:

{document_metadata}

CANDIDATE SKILLS:

{candidate_skill_text}

BOOK CONTENT SAMPLE:

--- BEGIN SOURCE SAMPLE ---

{source_sample}

--- END SOURCE SAMPLE ---
""".strip()