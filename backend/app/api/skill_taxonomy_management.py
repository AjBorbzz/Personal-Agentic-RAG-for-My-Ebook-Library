from collections import defaultdict

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.skill_taxonomy import (
    Skill,
    SkillAlias,
    SkillCategory,
    SkillDomain,
    SkillRelationship,
)
from app.schemas.skill_taxonomy_management import (
    SkillAliasCreate,
    SkillAliasResponse,
    SkillCategoryCreate,
    SkillCategoryResponse,
    SkillCategoryTree,
    SkillCategoryUpdate,
    SkillCreate,
    SkillDetailResponse,
    SkillDomainCreate,
    SkillDomainResponse,
    SkillDomainTree,
    SkillDomainUpdate,
    SkillListItem,
    SkillRelationshipCreate,
    SkillRelationshipResponse,
    SkillRelationshipUpdate,
    SkillSearchResponse,
    SkillTaxonomyTreeResponse,
    SkillUpdate,
)
from app.services.skill_taxonomy_import import (
    normalize_alias,
)


router = APIRouter(
    prefix="/skill-taxonomy",
    tags=["skill-taxonomy-management"],
)


def _get_domain(db: Session,domain_id: str) -> SkillDomain:
    domain = db.get(SkillDomain, domain_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Skill domain not found.")
    return domain

def _get_category(db: Session, category_id: str) -> SkillCategory:
    category = db.get(SkillCategory, category_id)

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Skill category not found.",
        )

    return category


def _get_skill(
    db: Session,
    skill_id: str,
) -> Skill:
    skill = db.get(
        Skill,
        skill_id,
    )

    if not skill:
        raise HTTPException(
            status_code=404,
            detail="Skill not found.",
        )

    return skill


def _validate_category_domain(
    *,
    category: SkillCategory | None,
    domain_id: str,
) -> None:
    if (
        category is not None
        and category.domain_id != domain_id
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "The selected category does not "
                "belong to the selected domain."
            ),
        )


def _skill_list_item(
    *,
    skill: Skill,
    domain: SkillDomain,
    category: SkillCategory | None,
) -> SkillListItem:
    return SkillListItem(
        skill_id=skill.skill_id,
        domain_id=domain.domain_id,
        domain_slug=domain.slug,
        domain_name=domain.name,
        category_id=(
            category.category_id
            if category
            else None
        ),
        category_slug=(
            category.slug
            if category
            else None
        ),
        category_name=(
            category.name
            if category
            else None
        ),
        slug=skill.slug,
        name=skill.name,
        description=skill.description,
        skill_type=skill.skill_type,
        difficulty_level=(
            skill.difficulty_level
        ),
        tags=skill.tags or [],
        is_active=skill.is_active,
        is_deprecated=(
            skill.is_deprecated
        ),
        source=skill.source,
    )


def _load_skill_items(
    db: Session,
    skills: list[Skill],
) -> list[SkillListItem]:
    if not skills:
        return []

    domain_ids = {
        skill.domain_id
        for skill in skills
    }

    category_ids = {
        skill.category_id
        for skill in skills
        if skill.category_id
    }

    domains = list(
        db.scalars(
            select(SkillDomain).where(
                SkillDomain.domain_id.in_(
                    domain_ids
                )
            )
        ).all()
    )

    categories = []

    if category_ids:
        categories = list(
            db.scalars(
                select(SkillCategory).where(
                    SkillCategory.category_id.in_(
                        category_ids
                    )
                )
            ).all()
        )

    domain_by_id = {
        domain.domain_id: domain
        for domain in domains
    }

    category_by_id = {
        category.category_id: category
        for category in categories
    }

    result = []

    for skill in skills:
        domain = domain_by_id.get(
            skill.domain_id
        )

        if not domain:
            continue

        category = (
            category_by_id.get(
                skill.category_id
            )
            if skill.category_id
            else None
        )

        result.append(
            _skill_list_item(
                skill=skill,
                domain=domain,
                category=category,
            )
        )

    return result


def _relationship_response(
    *,
    relationship: SkillRelationship,
    skill_by_id: dict[str, Skill],
) -> SkillRelationshipResponse:
    source_skill = skill_by_id[
        relationship.source_skill_id
    ]
    target_skill = skill_by_id[
        relationship.target_skill_id
    ]

    return SkillRelationshipResponse(
        relationship_id=(
            relationship.relationship_id
        ),
        source_skill_id=(
            source_skill.skill_id
        ),
        source_skill_slug=(
            source_skill.slug
        ),
        source_skill_name=(
            source_skill.name
        ),
        target_skill_id=(
            target_skill.skill_id
        ),
        target_skill_slug=(
            target_skill.slug
        ),
        target_skill_name=(
            target_skill.name
        ),
        relationship_type=(
            relationship.relationship_type
        ),
        strength=relationship.strength,
        notes=relationship.notes,
        source=relationship.source,
        is_active=relationship.is_active,
        created_at=relationship.created_at,
        updated_at=relationship.updated_at,
    )


@router.get(
    "/tree",
    response_model=SkillTaxonomyTreeResponse,
)
def get_skill_taxonomy_tree(
    include_inactive: bool = Query(
        default=False
    ),
    include_deprecated: bool = Query(
        default=False
    ),
    db: Session = Depends(get_db),
):
    domain_statement = (
        select(SkillDomain)
        .order_by(
            SkillDomain.display_order,
            SkillDomain.name,
        )
    )

    category_statement = (
        select(SkillCategory)
        .order_by(
            SkillCategory.display_order,
            SkillCategory.name,
        )
    )

    skill_statement = (
        select(Skill)
        .order_by(Skill.name)
    )

    if not include_inactive:
        domain_statement = (
            domain_statement.where(
                SkillDomain.is_active.is_(True)
            )
        )

        category_statement = (
            category_statement.where(
                SkillCategory.is_active.is_(
                    True
                )
            )
        )

        skill_statement = (
            skill_statement.where(
                Skill.is_active.is_(True)
            )
        )

    if not include_deprecated:
        skill_statement = (
            skill_statement.where(
                Skill.is_deprecated.is_(False)
            )
        )

    domains = list(
        db.scalars(
            domain_statement
        ).all()
    )

    domain_ids = {
        domain.domain_id
        for domain in domains
    }

    categories = list(
        db.scalars(
            category_statement.where(
                SkillCategory.domain_id.in_(
                    domain_ids
                )
            )
        ).all()
    ) if domain_ids else []

    skills = list(
        db.scalars(
            skill_statement.where(
                Skill.domain_id.in_(
                    domain_ids
                )
            )
        ).all()
    ) if domain_ids else []

    skill_items = _load_skill_items(
        db,
        skills,
    )

    skills_by_category: dict[
        str,
        list[SkillListItem],
    ] = defaultdict(list)

    uncategorized_by_domain: dict[
        str,
        list[SkillListItem],
    ] = defaultdict(list)

    for item in skill_items:
        if item.category_id:
            skills_by_category[
                item.category_id
            ].append(item)
        else:
            uncategorized_by_domain[
                item.domain_id
            ].append(item)

    category_nodes: dict[
        str,
        SkillCategoryTree,
    ] = {}

    for category in categories:
        category_nodes[
            category.category_id
        ] = SkillCategoryTree(
            category_id=(
                category.category_id
            ),
            domain_id=category.domain_id,
            parent_category_id=(
                category.parent_category_id
            ),
            slug=category.slug,
            name=category.name,
            description=(
                category.description
            ),
            display_order=(
                category.display_order
            ),
            skills=skills_by_category.get(
                category.category_id,
                [],
            ),
            children=[],
        )

    root_categories: dict[
        str,
        list[SkillCategoryTree],
    ] = defaultdict(list)

    for category in categories:
        node = category_nodes[
            category.category_id
        ]

        if (
            category.parent_category_id
            and category.parent_category_id
            in category_nodes
        ):
            category_nodes[
                category.parent_category_id
            ].children.append(node)
        else:
            root_categories[
                category.domain_id
            ].append(node)

    domain_nodes = []

    for domain in domains:
        domain_nodes.append(
            SkillDomainTree(
                domain_id=domain.domain_id,
                slug=domain.slug,
                name=domain.name,
                description=domain.description,
                display_order=(
                    domain.display_order
                ),
                uncategorized_skills=(
                    uncategorized_by_domain.get(
                        domain.domain_id,
                        [],
                    )
                ),
                categories=(
                    root_categories.get(
                        domain.domain_id,
                        [],
                    )
                ),
            )
        )

    return SkillTaxonomyTreeResponse(
        domain_count=len(domains),
        category_count=len(categories),
        skill_count=len(skills),
        domains=domain_nodes,
    )


@router.get(
    "/skills",
    response_model=SkillSearchResponse,
)
def search_skills(
    query: str | None = Query(
        default=None
    ),
    domain_slug: str | None = Query(
        default=None
    ),
    category_slug: str | None = Query(
        default=None
    ),
    skill_type: str | None = Query(
        default=None
    ),
    difficulty_level: str | None = Query(
        default=None
    ),
    include_inactive: bool = Query(
        default=False
    ),
    include_deprecated: bool = Query(
        default=False
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    db: Session = Depends(get_db),
):
    # statement = (
    #     select(Skill)
    #     .outerjoin(
    #         SkillAlias,
    #         SkillAlias.skill_id
    #         == Skill.skill_id,
    #     )
    #     .distinct()
    #     .order_by(Skill.name)
    # )

    

    # if query and query.strip():
    #     pattern = f"%{query.strip()}%"

    #     statement = statement.where(
    #         or_(
    #             Skill.name.ilike(pattern),
    #             Skill.slug.ilike(pattern),
    #             Skill.description.ilike(
    #                 pattern
    #             ),
    #             SkillAlias.alias.ilike(
    #                 pattern
    #             ),
    #         )
    #     )

    statement = (
        select(Skill)
        .order_by(Skill.name)
    )

    if query and query.strip():
        pattern = f"%{query.strip()}%"

        alias_skill_ids = (
            select(SkillAlias.skill_id)
            .where(
                SkillAlias.alias.ilike(pattern)
            )
        )

        statement = statement.where(
            or_(
                Skill.name.ilike(pattern),
                Skill.slug.ilike(pattern),
                Skill.description.ilike(pattern),
                Skill.skill_id.in_(
                    alias_skill_ids
                ),
            )
        )

    if domain_slug:
        domain = db.scalar(
            select(SkillDomain).where(
                SkillDomain.slug
                == domain_slug
            )
        )

        if not domain:
            raise HTTPException(
                status_code=404,
                detail="Skill domain not found.",
            )

        statement = statement.where(
            Skill.domain_id
            == domain.domain_id
        )

    if category_slug:
        category_ids = list(
            db.scalars(
                select(
                    SkillCategory.category_id
                ).where(
                    SkillCategory.slug
                    == category_slug
                )
            ).all()
        )

        if not category_ids:
            return SkillSearchResponse(
                total=0,
                result_count=0,
                results=[],
            )

        statement = statement.where(
            Skill.category_id.in_(
                category_ids
            )
        )

    if skill_type:
        statement = statement.where(
            Skill.skill_type == skill_type
        )

    if difficulty_level:
        statement = statement.where(
            Skill.difficulty_level
            == difficulty_level
        )

    if not include_inactive:
        statement = statement.where(
            Skill.is_active.is_(True)
        )

    if not include_deprecated:
        statement = statement.where(
            Skill.is_deprecated.is_(False)
        )

    all_skills = list(
        db.scalars(statement).all()
    )

    visible_skills = all_skills[:limit]

    return SkillSearchResponse(
        total=len(all_skills),
        result_count=len(visible_skills),
        results=_load_skill_items(
            db,
            visible_skills,
        ),
    )


@router.get("/skills/{skill_id}", response_model=SkillDetailResponse)
def get_skill_detail(skill_id: str, db: Session = Depends(get_db)):
    skill = _get_skill(db, skill_id)

    domain = _get_domain(
        db,
        skill.domain_id,
    )

    category = (
        _get_category(
            db,
            skill.category_id,
        )
        if skill.category_id
        else None
    )

    aliases = list(
        db.scalars(
            select(SkillAlias)
            .where(
                SkillAlias.skill_id
                == skill_id
            )
            .order_by(SkillAlias.alias)
        ).all()
    )

    relationships = list(
        db.scalars(
            select(SkillRelationship).where(
                or_(
                    SkillRelationship
                    .source_skill_id
                    == skill_id,

                    SkillRelationship
                    .target_skill_id
                    == skill_id,
                )
            )
        ).all()
    )

    related_skill_ids = {
        relationship.source_skill_id
        for relationship in relationships
    } | {
        relationship.target_skill_id
        for relationship in relationships
    }

    related_skills = list(
        db.scalars(
            select(Skill).where(
                Skill.skill_id.in_(
                    related_skill_ids
                )
            )
        ).all()
    ) if related_skill_ids else []

    skill_by_id = {
        item.skill_id: item
        for item in related_skills
    }

    outgoing = []
    incoming = []

    for relationship in relationships:
        response = _relationship_response(
            relationship=relationship,
            skill_by_id=skill_by_id,
        )

        if (
            relationship.source_skill_id
            == skill_id
        ):
            outgoing.append(response)
        else:
            incoming.append(response)

    superseded_by = None

    if skill.superseded_by_skill_id:
        replacement = db.get(
            Skill,
            skill.superseded_by_skill_id,
        )

        if replacement:
            replacement_items = (
                _load_skill_items(
                    db,
                    [replacement],
                )
            )

            if replacement_items:
                superseded_by = (
                    replacement_items[0]
                )

    return SkillDetailResponse(
        skill=_skill_list_item(
            skill=skill,
            domain=domain,
            category=category,
        ),
        aliases=aliases,
        outgoing_relationships=outgoing,
        incoming_relationships=incoming,
        superseded_by=superseded_by,
    )


@router.post(
    "/domains",
    response_model=SkillDomainResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_skill_domain(
    request: SkillDomainCreate,
    db: Session = Depends(get_db),
):
    existing = db.scalar(
        select(SkillDomain).where(
            or_(
                SkillDomain.slug
                == request.slug,
                SkillDomain.name
                == request.name,
            )
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                "A domain with this slug or "
                "name already exists."
            ),
        )

    domain = SkillDomain(
        **request.model_dump()
    )

    db.add(domain)
    db.commit()
    db.refresh(domain)

    return domain


@router.patch(
    "/domains/{domain_id}",
    response_model=SkillDomainResponse,
)
def update_skill_domain(
    domain_id: str,
    request: SkillDomainUpdate,
    db: Session = Depends(get_db),
):
    domain = _get_domain(
        db,
        domain_id,
    )

    for field_name, value in (
        request.model_dump(
            exclude_unset=True
        ).items()
    ):
        setattr(
            domain,
            field_name,
            value,
        )

    db.commit()
    db.refresh(domain)

    return domain


@router.post(
    "/categories",
    response_model=SkillCategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_skill_category(
    request: SkillCategoryCreate,
    db: Session = Depends(get_db),
):
    _get_domain(
        db,
        request.domain_id,
    )

    parent = None

    if request.parent_category_id:
        parent = _get_category(
            db,
            request.parent_category_id,
        )

        if parent.domain_id != request.domain_id:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Parent category must belong "
                    "to the same domain."
                ),
            )

    existing = db.scalar(
        select(SkillCategory).where(
            SkillCategory.domain_id
            == request.domain_id,
            SkillCategory.slug
            == request.slug,
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                "This category slug already "
                "exists in the selected domain."
            ),
        )

    category = SkillCategory(
        **request.model_dump()
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return category


@router.patch(
    "/categories/{category_id}",
    response_model=SkillCategoryResponse,
)
def update_skill_category(
    category_id: str,
    request: SkillCategoryUpdate,
    db: Session = Depends(get_db),
):
    category = _get_category(
        db,
        category_id,
    )

    update_data = request.model_dump(
        exclude_unset=True
    )

    final_domain_id = update_data.get(
        "domain_id",
        category.domain_id,
    )

    _get_domain(
        db,
        final_domain_id,
    )

    if "parent_category_id" in update_data:
        parent_id = update_data[
            "parent_category_id"
        ]

        if parent_id is not None:
            if parent_id == category_id:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "A category cannot be "
                        "its own parent."
                    ),
                )

            parent = _get_category(
                db,
                parent_id,
            )

            if (
                parent.domain_id
                != final_domain_id
            ):
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "Parent category must "
                        "belong to the same domain."
                    ),
                )

    for field_name, value in (
        update_data.items()
    ):
        setattr(
            category,
            field_name,
            value,
        )

    db.commit()
    db.refresh(category)

    return category


@router.post(
    "/skills",
    response_model=SkillListItem,
    status_code=status.HTTP_201_CREATED,
)
def create_skill(
    request: SkillCreate,
    db: Session = Depends(get_db),
):
    domain = _get_domain(
        db,
        request.domain_id,
    )

    category = None

    if request.category_id:
        category = _get_category(
            db,
            request.category_id,
        )

    _validate_category_domain(
        category=category,
        domain_id=request.domain_id,
    )

    existing = db.scalar(
        select(Skill).where(
            Skill.slug == request.slug
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                "A skill with this slug "
                "already exists."
            ),
        )

    if request.superseded_by_skill_id:
        _get_skill(
            db,
            request.superseded_by_skill_id,
        )

    skill = Skill(
        **request.model_dump()
    )

    db.add(skill)
    db.commit()
    db.refresh(skill)

    return _skill_list_item(
        skill=skill,
        domain=domain,
        category=category,
    )


@router.patch(
    "/skills/{skill_id}",
    response_model=SkillListItem,
)
def update_skill(
    skill_id: str,
    request: SkillUpdate,
    db: Session = Depends(get_db),
):
    skill = _get_skill(
        db,
        skill_id,
    )

    update_data = request.model_dump(
        exclude_unset=True
    )

    final_domain_id = update_data.get(
        "domain_id",
        skill.domain_id,
    )

    final_category_id = update_data.get(
        "category_id",
        skill.category_id,
    )

    domain = _get_domain(
        db,
        final_domain_id,
    )

    category = (
        _get_category(
            db,
            final_category_id,
        )
        if final_category_id
        else None
    )

    _validate_category_domain(
        category=category,
        domain_id=final_domain_id,
    )

    if (
        "superseded_by_skill_id"
        in update_data
    ):
        replacement_id = update_data[
            "superseded_by_skill_id"
        ]

        if replacement_id == skill_id:
            raise HTTPException(
                status_code=422,
                detail=(
                    "A skill cannot supersede "
                    "itself."
                ),
            )

        if replacement_id:
            _get_skill(
                db,
                replacement_id,
            )

    for field_name, value in (
        update_data.items()
    ):
        setattr(
            skill,
            field_name,
            value,
        )

    db.commit()
    db.refresh(skill)

    return _skill_list_item(
        skill=skill,
        domain=domain,
        category=category,
    )


@router.post(
    "/skills/{skill_id}/aliases",
    response_model=SkillAliasResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_skill_alias(
    skill_id: str,
    request: SkillAliasCreate,
    db: Session = Depends(get_db),
):
    _get_skill(
        db,
        skill_id,
    )

    normalized = normalize_alias(
        request.alias
    )

    existing = db.scalar(
        select(SkillAlias).where(
            SkillAlias.skill_id == skill_id,
            SkillAlias.normalized_alias
            == normalized,
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                "This alias already exists "
                "for the selected skill."
            ),
        )

    alias = SkillAlias(
        skill_id=skill_id,
        alias=request.alias,
        normalized_alias=normalized,
        alias_type=request.alias_type,
    )

    db.add(alias)
    db.commit()
    db.refresh(alias)

    return alias


@router.delete(
    "/aliases/{alias_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_skill_alias(
    alias_id: str,
    db: Session = Depends(get_db),
):
    alias = db.get(
        SkillAlias,
        alias_id,
    )

    if not alias:
        raise HTTPException(
            status_code=404,
            detail="Skill alias not found.",
        )

    db.delete(alias)
    db.commit()

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


@router.post(
    "/relationships",
    response_model=SkillRelationshipResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_skill_relationship(
    request: SkillRelationshipCreate,
    db: Session = Depends(get_db),
):
    source_skill = _get_skill(
        db,
        request.source_skill_id,
    )

    target_skill = _get_skill(
        db,
        request.target_skill_id,
    )

    if (
        source_skill.skill_id
        == target_skill.skill_id
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "A skill cannot have a "
                "relationship with itself."
            ),
        )

    existing = db.scalar(
        select(SkillRelationship).where(
            SkillRelationship.source_skill_id
            == source_skill.skill_id,
            SkillRelationship.target_skill_id
            == target_skill.skill_id,
            SkillRelationship.relationship_type
            == request.relationship_type,
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                "This skill relationship "
                "already exists."
            ),
        )

    relationship = SkillRelationship(
        **request.model_dump()
    )

    db.add(relationship)
    db.commit()
    db.refresh(relationship)

    return _relationship_response(
        relationship=relationship,
        skill_by_id={
            source_skill.skill_id: (
                source_skill
            ),
            target_skill.skill_id: (
                target_skill
            ),
        },
    )


@router.patch(
    "/relationships/{relationship_id}",
    response_model=SkillRelationshipResponse,
)
def update_skill_relationship(
    relationship_id: str,
    request: SkillRelationshipUpdate,
    db: Session = Depends(get_db),
):
    relationship = db.get(
        SkillRelationship,
        relationship_id,
    )

    if not relationship:
        raise HTTPException(
            status_code=404,
            detail=(
                "Skill relationship not found."
            ),
        )

    for field_name, value in (
        request.model_dump(
            exclude_unset=True
        ).items()
    ):
        setattr(
            relationship,
            field_name,
            value,
        )

    source_skill = _get_skill(
        db,
        relationship.source_skill_id,
    )

    target_skill = _get_skill(
        db,
        relationship.target_skill_id,
    )

    db.commit()
    db.refresh(relationship)

    return _relationship_response(
        relationship=relationship,
        skill_by_id={
            source_skill.skill_id: (
                source_skill
            ),
            target_skill.skill_id: (
                target_skill
            ),
        },
    )