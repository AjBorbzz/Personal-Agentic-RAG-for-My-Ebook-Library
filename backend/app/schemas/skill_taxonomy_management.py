from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


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


class SkillDomainCreate(BaseModel):
    slug: str = Field(
        min_length=1,
        max_length=120,
    )
    name: str = Field(
        min_length=1,
        max_length=200,
    )
    description: str | None = None
    display_order: int = 0
    is_active: bool = True


class SkillDomainUpdate(BaseModel):
    slug: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
    )
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    description: str | None = None
    display_order: int | None = None
    is_active: bool | None = None


class SkillDomainResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    domain_id: str
    slug: str
    name: str
    description: str | None
    display_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SkillCategoryCreate(BaseModel):
    domain_id: str
    parent_category_id: str | None = None

    slug: str = Field(
        min_length=1,
        max_length=120,
    )
    name: str = Field(
        min_length=1,
        max_length=200,
    )

    description: str | None = None
    display_order: int = 0
    is_active: bool = True


class SkillCategoryUpdate(BaseModel):
    domain_id: str | None = None
    parent_category_id: str | None = None

    slug: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
    )
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    description: str | None = None
    display_order: int | None = None
    is_active: bool | None = None


class SkillCategoryResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    category_id: str
    domain_id: str
    parent_category_id: str | None

    slug: str
    name: str
    description: str | None

    display_order: int
    is_active: bool

    created_at: datetime
    updated_at: datetime


class SkillCreate(BaseModel):
    domain_id: str
    category_id: str | None = None

    slug: str = Field(
        min_length=1,
        max_length=160,
    )
    name: str = Field(
        min_length=1,
        max_length=240,
    )

    description: str | None = None

    skill_type: SkillType = "concept"
    difficulty_level: DifficultyLevel = (
        "foundational"
    )

    tags: list[str] = Field(
        default_factory=list
    )

    is_active: bool = True
    is_deprecated: bool = False

    superseded_by_skill_id: str | None = None

    source: str = "manual"


class SkillUpdate(BaseModel):
    domain_id: str | None = None
    category_id: str | None = None

    slug: str | None = Field(
        default=None,
        min_length=1,
        max_length=160,
    )
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=240,
    )

    description: str | None = None

    skill_type: SkillType | None = None
    difficulty_level: DifficultyLevel | None = (
        None
    )

    tags: list[str] | None = None

    is_active: bool | None = None
    is_deprecated: bool | None = None

    superseded_by_skill_id: str | None = None

    source: str | None = None


class SkillListItem(BaseModel):
    skill_id: str
    domain_id: str
    domain_slug: str
    domain_name: str

    category_id: str | None
    category_slug: str | None
    category_name: str | None

    slug: str
    name: str
    description: str | None

    skill_type: str
    difficulty_level: str

    tags: list[str]

    is_active: bool
    is_deprecated: bool

    source: str


class SkillAliasCreate(BaseModel):
    alias: str = Field(
        min_length=1,
        max_length=240,
    )
    alias_type: AliasType = "synonym"


class SkillAliasResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    alias_id: str
    skill_id: str
    alias: str
    normalized_alias: str
    alias_type: str
    created_at: datetime


class SkillRelationshipCreate(BaseModel):
    source_skill_id: str
    target_skill_id: str

    relationship_type: RelationshipType

    strength: float = Field(
        default=1.0,
        ge=0,
        le=1,
    )

    notes: str | None = None
    source: str = "manual"
    is_active: bool = True


class SkillRelationshipUpdate(BaseModel):
    relationship_type: (
        RelationshipType | None
    ) = None

    strength: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    notes: str | None = None
    source: str | None = None
    is_active: bool | None = None


class SkillRelationshipResponse(BaseModel):
    relationship_id: str

    source_skill_id: str
    source_skill_slug: str
    source_skill_name: str

    target_skill_id: str
    target_skill_slug: str
    target_skill_name: str

    relationship_type: str
    strength: float

    notes: str | None
    source: str
    is_active: bool

    created_at: datetime
    updated_at: datetime


class SkillDetailResponse(BaseModel):
    skill: SkillListItem

    aliases: list[SkillAliasResponse]

    outgoing_relationships: list[
        SkillRelationshipResponse
    ]

    incoming_relationships: list[
        SkillRelationshipResponse
    ]

    superseded_by: SkillListItem | None = None


class SkillSearchResponse(BaseModel):
    total: int
    result_count: int
    results: list[SkillListItem]


class SkillCategoryTree(BaseModel):
    category_id: str
    domain_id: str
    parent_category_id: str | None

    slug: str
    name: str
    description: str | None
    display_order: int

    skills: list[SkillListItem] = Field(
        default_factory=list
    )

    children: list[
        SkillCategoryTree
    ] = Field(default_factory=list)


class SkillDomainTree(BaseModel):
    domain_id: str
    slug: str
    name: str
    description: str | None
    display_order: int

    uncategorized_skills: list[
        SkillListItem
    ] = Field(default_factory=list)

    categories: list[
        SkillCategoryTree
    ] = Field(default_factory=list)


class SkillTaxonomyTreeResponse(BaseModel):
    domain_count: int
    category_count: int
    skill_count: int

    domains: list[SkillDomainTree]