from typing import Literal

from pydantic import BaseModel, Field


SkillType = Literal[
    "concept",
    "practice",
    "language",
    "framework",
    "platform",
    "tool",
    "architecture",
    "methodology",
]

DifficultyLevel = Literal[
    "foundational",
    "intermediate",
    "advanced",
    "expert",
]

AliasType = Literal[
    "synonym",
    "abbreviation",
    "product_name",
    "former_name",
    "alternate_spelling",
]

RelationshipType = Literal[
    "prerequisite",
    "related",
    "complements",
    "supersedes",
]


class SkillDomainSeed(BaseModel):
    slug: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=200)

    description: str | None = None
    display_order: int = 0
    is_active: bool = True


class SkillCategorySeed(BaseModel):
    domain_slug: str
    slug: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=200)

    parent_category_slug: str | None = None

    description: str | None = None
    display_order: int = 0
    is_active: bool = True


class SkillAliasSeed(BaseModel):
    alias: str = Field(min_length=1, max_length=240)

    alias_type: AliasType = "synonym"


class SkillSeed(BaseModel):
    domain_slug: str
    category_slug: str | None = None

    slug: str = Field(min_length=1, max_length=160)
    name: str = Field(min_length=1, max_length=240)

    description: str | None = None

    skill_type: SkillType = "concept"
    difficulty_level: DifficultyLevel = "foundational"

    tags: list[str] = Field(default_factory=list)
    aliases: list[SkillAliasSeed] = Field(
        default_factory=list
    )

    is_active: bool = True
    is_deprecated: bool = False

    source: Literal[
        "manual",
        "imported",
        "llm_candidate",
        "reviewed_llm",
    ] = "imported"


class SkillRelationshipSeed(BaseModel):
    source_skill_slug: str
    target_skill_slug: str

    relationship_type: RelationshipType

    strength: float = Field(
        default=1.0,
        ge=0,
        le=1,
    )

    notes: str | None = None

    source: Literal[
        "manual",
        "imported",
        "llm_candidate",
        "reviewed_llm",
    ] = "imported"


class SkillTaxonomyBundle(BaseModel):
    version: str = "1.0"

    domains: list[SkillDomainSeed] = Field(
        default_factory=list
    )

    categories: list[SkillCategorySeed] = Field(
        default_factory=list
    )

    skills: list[SkillSeed] = Field(
        default_factory=list
    )

    relationships: list[
        SkillRelationshipSeed
    ] = Field(default_factory=list)


class SkillTaxonomyImportResponse(BaseModel):
    version: str
    overwrite_existing: bool

    domains_created: int
    domains_updated: int

    categories_created: int
    categories_updated: int

    skills_created: int
    skills_updated: int

    aliases_created: int
    aliases_updated: int

    relationships_created: int
    relationships_updated: int

    warnings: list[str] = Field(
        default_factory=list
    )


class SkillTaxonomySummaryResponse(BaseModel):
    domains: int
    active_domains: int

    categories: int
    active_categories: int

    skills: int
    active_skills: int
    deprecated_skills: int

    aliases: int
    relationships: int