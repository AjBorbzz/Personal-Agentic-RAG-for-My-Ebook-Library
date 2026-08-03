from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
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
    SkillTaxonomySummaryResponse,
)
from app.services.skill_taxonomy_import import (
    import_skill_taxonomy,
)


router = APIRouter(
    prefix="/skill-taxonomy",
    tags=["skill-taxonomy"],
)


STARTER_TAXONOMY_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "skill_taxonomy_starter.json"
)


@router.post(
    "/import",
    response_model=SkillTaxonomyImportResponse,
)
def import_taxonomy(
    bundle: SkillTaxonomyBundle,
    overwrite_existing: bool = Query(
        default=True
    ),
    db: Session = Depends(get_db),
):
    try:
        return import_skill_taxonomy(
            db=db,
            bundle=bundle,
            overwrite_existing=(
                overwrite_existing
            ),
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "Skill taxonomy import failed: "
                f"{type(error).__name__}: {error}"
            ),
        ) from error


@router.post(
    "/seed/starter",
    response_model=SkillTaxonomyImportResponse,
)
def seed_starter_taxonomy(
    overwrite_existing: bool = Query(
        default=True
    ),
    db: Session = Depends(get_db),
):
    if not STARTER_TAXONOMY_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail=(
                "Starter taxonomy file was not "
                f"found: {STARTER_TAXONOMY_PATH}"
            ),
        )

    try:
        bundle = SkillTaxonomyBundle.model_validate_json(
            STARTER_TAXONOMY_PATH.read_text(
                encoding="utf-8"
            )
        )

        return import_skill_taxonomy(
            db=db,
            bundle=bundle,
            overwrite_existing=(
                overwrite_existing
            ),
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "Starter taxonomy seed failed: "
                f"{type(error).__name__}: {error}"
            ),
        ) from error


@router.get(
    "/summary",
    response_model=SkillTaxonomySummaryResponse,
)
def get_taxonomy_summary(
    db: Session = Depends(get_db),
):
    def count_rows(
        model,
        *conditions,
    ) -> int:
        statement = select(
            func.count()
        ).select_from(model)

        if conditions:
            statement = statement.where(
                *conditions
            )

        return int(
            db.scalar(statement) or 0
        )

    return SkillTaxonomySummaryResponse(
        domains=count_rows(SkillDomain),
        active_domains=count_rows(
            SkillDomain,
            SkillDomain.is_active.is_(True),
        ),
        categories=count_rows(
            SkillCategory
        ),
        active_categories=count_rows(
            SkillCategory,
            SkillCategory.is_active.is_(True),
        ),
        skills=count_rows(Skill),
        active_skills=count_rows(
            Skill,
            Skill.is_active.is_(True),
        ),
        deprecated_skills=count_rows(
            Skill,
            Skill.is_deprecated.is_(True),
        ),
        aliases=count_rows(SkillAlias),
        relationships=count_rows(
            SkillRelationship,
            SkillRelationship.is_active.is_(
                True
            ),
        ),
    )