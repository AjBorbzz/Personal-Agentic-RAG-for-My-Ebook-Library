import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.skill_taxonomy import (
    Skill,
    SkillAlias,
    SkillCategory,
    SkillDomain,
    SkillRelationship,
)
from app.schemas.skill_taxonomy_import import (
    SkillTaxonomyBundle,
    SkillTaxonomyImportResponse,
)


def normalize_alias(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"\s+", " ", normalized)

    return normalized


def import_skill_taxonomy(
    *,
    db: Session,
    bundle: SkillTaxonomyBundle,
    overwrite_existing: bool = True,
) -> SkillTaxonomyImportResponse:
    counters = {
        "domains_created": 0,
        "domains_updated": 0,
        "categories_created": 0,
        "categories_updated": 0,
        "skills_created": 0,
        "skills_updated": 0,
        "aliases_created": 0,
        "aliases_updated": 0,
        "relationships_created": 0,
        "relationships_updated": 0,
    }

    warnings: list[str] = []

    try:
        domain_by_slug: dict[
            str,
            SkillDomain,
        ] = {}

        # -----------------------------------------
        # Domains
        # -----------------------------------------

        for item in bundle.domains:
            domain = db.scalar(
                select(SkillDomain).where(
                    SkillDomain.slug == item.slug
                )
            )

            if domain is None:
                domain = SkillDomain(
                    slug=item.slug,
                    name=item.name,
                    description=item.description,
                    display_order=item.display_order,
                    is_active=item.is_active,
                )

                db.add(domain)
                db.flush()

                counters["domains_created"] += 1

            elif overwrite_existing:
                domain.name = item.name
                domain.description = item.description
                domain.display_order = (
                    item.display_order
                )
                domain.is_active = item.is_active

                counters["domains_updated"] += 1

            domain_by_slug[item.slug] = domain

        db.flush()

        # -----------------------------------------
        # Categories: first pass
        # -----------------------------------------

        category_by_key: dict[
            tuple[str, str],
            SkillCategory,
        ] = {}

        for item in bundle.categories:
            domain = domain_by_slug.get(
                item.domain_slug
            )

            if domain is None:
                domain = db.scalar(
                    select(SkillDomain).where(
                        SkillDomain.slug
                        == item.domain_slug
                    )
                )

            if domain is None:
                raise ValueError(
                    "Unknown domain slug for category "
                    f"'{item.slug}': "
                    f"'{item.domain_slug}'."
                )

            category = db.scalar(
                select(SkillCategory).where(
                    SkillCategory.domain_id
                    == domain.domain_id,
                    SkillCategory.slug
                    == item.slug,
                )
            )

            if category is None:
                category = SkillCategory(
                    domain_id=domain.domain_id,
                    parent_category_id=None,
                    slug=item.slug,
                    name=item.name,
                    description=item.description,
                    display_order=item.display_order,
                    is_active=item.is_active,
                )

                db.add(category)
                db.flush()

                counters[
                    "categories_created"
                ] += 1

            elif overwrite_existing:
                category.name = item.name
                category.description = (
                    item.description
                )
                category.display_order = (
                    item.display_order
                )
                category.is_active = item.is_active

                counters[
                    "categories_updated"
                ] += 1

            category_by_key[
                (
                    item.domain_slug,
                    item.slug,
                )
            ] = category

        db.flush()

        # -----------------------------------------
        # Categories: parent assignments
        # -----------------------------------------

        for item in bundle.categories:
            if not item.parent_category_slug:
                continue

            category = category_by_key[
                (
                    item.domain_slug,
                    item.slug,
                )
            ]

            parent = category_by_key.get(
                (
                    item.domain_slug,
                    item.parent_category_slug,
                )
            )

            if parent is None:
                raise ValueError(
                    "Unknown parent category "
                    f"'{item.parent_category_slug}' "
                    f"for category '{item.slug}'."
                )

            if category.category_id == parent.category_id:
                raise ValueError(
                    f"Category '{item.slug}' cannot "
                    "be its own parent."
                )

            category.parent_category_id = (
                parent.category_id
            )

        db.flush()

        # -----------------------------------------
        # Skills
        # -----------------------------------------

        skill_by_slug: dict[str, Skill] = {}

        for item in bundle.skills:
            domain = domain_by_slug.get(
                item.domain_slug
            )

            if domain is None:
                domain = db.scalar(
                    select(SkillDomain).where(
                        SkillDomain.slug
                        == item.domain_slug
                    )
                )

            if domain is None:
                raise ValueError(
                    "Unknown domain slug for skill "
                    f"'{item.slug}': "
                    f"'{item.domain_slug}'."
                )

            category: SkillCategory | None = None

            if item.category_slug:
                category = category_by_key.get(
                    (
                        item.domain_slug,
                        item.category_slug,
                    )
                )

                if category is None:
                    raise ValueError(
                        "Unknown category slug for "
                        f"skill '{item.slug}': "
                        f"'{item.category_slug}'."
                    )

            skill = db.scalar(
                select(Skill).where(
                    Skill.slug == item.slug
                )
            )

            if skill is None:
                skill = Skill(
                    domain_id=domain.domain_id,
                    category_id=(
                        category.category_id
                        if category
                        else None
                    ),
                    slug=item.slug,
                    name=item.name,
                    description=item.description,
                    skill_type=item.skill_type,
                    difficulty_level=(
                        item.difficulty_level
                    ),
                    tags=item.tags,
                    is_active=item.is_active,
                    is_deprecated=(
                        item.is_deprecated
                    ),
                    source=item.source,
                )

                db.add(skill)
                db.flush()

                counters["skills_created"] += 1

            elif overwrite_existing:
                skill.domain_id = domain.domain_id
                skill.category_id = (
                    category.category_id
                    if category
                    else None
                )
                skill.name = item.name
                skill.description = (
                    item.description
                )
                skill.skill_type = item.skill_type
                skill.difficulty_level = (
                    item.difficulty_level
                )
                skill.tags = item.tags
                skill.is_active = item.is_active
                skill.is_deprecated = (
                    item.is_deprecated
                )
                skill.source = item.source

                counters["skills_updated"] += 1

            skill_by_slug[item.slug] = skill

            # -------------------------------------
            # Skill aliases
            # -------------------------------------

            for alias_item in item.aliases:
                normalized_alias = normalize_alias(
                    alias_item.alias
                )

                existing_alias = db.scalar(
                    select(SkillAlias).where(
                        SkillAlias.skill_id
                        == skill.skill_id,
                        SkillAlias.normalized_alias
                        == normalized_alias,
                    )
                )

                if existing_alias is None:
                    db.add(
                        SkillAlias(
                            skill_id=skill.skill_id,
                            alias=alias_item.alias,
                            normalized_alias=(
                                normalized_alias
                            ),
                            alias_type=(
                                alias_item.alias_type
                            ),
                        )
                    )

                    counters[
                        "aliases_created"
                    ] += 1

                elif overwrite_existing:
                    existing_alias.alias = (
                        alias_item.alias
                    )
                    existing_alias.alias_type = (
                        alias_item.alias_type
                    )

                    counters[
                        "aliases_updated"
                    ] += 1

        db.flush()

        # Include skills already present in the DB
        # when relationships reference them.

        referenced_slugs = {
            item.source_skill_slug
            for item in bundle.relationships
        } | {
            item.target_skill_slug
            for item in bundle.relationships
        }

        missing_slugs = (
            referenced_slugs
            - set(skill_by_slug)
        )

        if missing_slugs:
            existing_skills = list(
                db.scalars(
                    select(Skill).where(
                        Skill.slug.in_(
                            missing_slugs
                        )
                    )
                ).all()
            )

            for skill in existing_skills:
                skill_by_slug[skill.slug] = skill

        # -----------------------------------------
        # Skill relationships
        # -----------------------------------------

        for item in bundle.relationships:
            source_skill = skill_by_slug.get(
                item.source_skill_slug
            )
            target_skill = skill_by_slug.get(
                item.target_skill_slug
            )

            if source_skill is None:
                raise ValueError(
                    "Unknown relationship source "
                    f"skill: "
                    f"'{item.source_skill_slug}'."
                )

            if target_skill is None:
                raise ValueError(
                    "Unknown relationship target "
                    f"skill: "
                    f"'{item.target_skill_slug}'."
                )

            if (
                source_skill.skill_id
                == target_skill.skill_id
            ):
                raise ValueError(
                    "A skill cannot have a "
                    "relationship with itself: "
                    f"'{item.source_skill_slug}'."
                )

            relationship = db.scalar(
                select(SkillRelationship).where(
                    SkillRelationship.source_skill_id
                    == source_skill.skill_id,
                    SkillRelationship.target_skill_id
                    == target_skill.skill_id,
                    SkillRelationship.relationship_type
                    == item.relationship_type,
                )
            )

            if relationship is None:
                relationship = SkillRelationship(
                    source_skill_id=(
                        source_skill.skill_id
                    ),
                    target_skill_id=(
                        target_skill.skill_id
                    ),
                    relationship_type=(
                        item.relationship_type
                    ),
                    strength=item.strength,
                    notes=item.notes,
                    source=item.source,
                    is_active=True,
                )

                db.add(relationship)

                counters[
                    "relationships_created"
                ] += 1

            elif overwrite_existing:
                relationship.strength = (
                    item.strength
                )
                relationship.notes = item.notes
                relationship.source = item.source
                relationship.is_active = True

                counters[
                    "relationships_updated"
                ] += 1

        db.commit()

        return SkillTaxonomyImportResponse(
            version=bundle.version,
            overwrite_existing=overwrite_existing,
            warnings=warnings,
            **counters,
        )

    except Exception:
        db.rollback()
        raise