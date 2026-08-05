import asyncio

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.book_skill_mapping import (
    BookSkillMapping,
)
from app.models.document import Document
from app.models.skill_taxonomy import (
    Skill,
    SkillCategory,
    SkillDomain,
)
from app.schemas.book_skill_candidate import (
    BookSkillCandidateListItem,
    BookSkillCandidateListResponse,
    GenerateBookSkillCandidatesRequest,
    GenerateBookSkillCandidatesResponse,
)
from app.schemas.book_skill_mapping import (
    BookSkillMappingResponse,
)
from app.services.book_skill_candidate_generation import (
    generate_book_skill_candidates,
)


router = APIRouter(
    prefix="/book-skill-mappings",
    tags=["book-skill-mappings"],
)


@router.post(
    "/documents/{document_id}/generate-candidates",
    response_model=GenerateBookSkillCandidatesResponse,
)
async def generate_document_skill_candidates(
    document_id: str,
    request: GenerateBookSkillCandidatesRequest,
    db: Session = Depends(get_db),
):
    document = db.get(
        Document,
        document_id,
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    warnings: list[str] = []

    if not document.metadata_reviewed:
        warnings.append(
            "The document metadata has not been "
            "approved. Candidate quality may be "
            "lower."
        )

    try:
        result = (
            await generate_book_skill_candidates(
                db=db,
                document=document,
                max_source_characters=(
                    request
                    .max_source_characters
                ),
                maximum_candidate_skills=(
                    request
                    .maximum_candidate_skills
                ),
                maximum_mappings=(
                    request.maximum_mappings
                ),
                minimum_shortlist_score=(
                    request
                    .minimum_shortlist_score
                ),
                regenerate_approved=(
                    request
                    .regenerate_approved
                ),
            )
        )

        result.warnings = (
            warnings + result.warnings
        )

        return result

    except FileNotFoundError as error:
        db.rollback()

        raise HTTPException(
            status_code=422,
            detail=(
                "The parsed document text could "
                f"not be found: {error}"
            ),
        ) from error

    except asyncio.TimeoutError as error:
        db.rollback()

        raise HTTPException(
            status_code=504,
            detail=(
                "Book-to-skill generation timed "
                "out while waiting for Ollama."
            ),
        ) from error

    except ValueError as error:
        db.rollback()

        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except RuntimeError as error:
        db.rollback()

        message = str(error)

        status_code = (
            503
            if "connect" in message.lower()
            or "ollama" in message.lower()
            else 500
        )

        raise HTTPException(
            status_code=status_code,
            detail=message,
        ) from error

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Book-to-skill candidate "
                "generation failed: "
                f"{type(error).__name__}: "
                f"{error}"
            ),
        ) from error


@router.get(
    "/documents/{document_id}/candidates",
    response_model=BookSkillCandidateListResponse,
)
def list_document_skill_candidates(
    document_id: str,
    status: str | None = Query(
        default="pending"
    ),
    db: Session = Depends(get_db),
):
    document = db.get(
        Document,
        document_id,
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    statement = (
        select(
            BookSkillMapping,
            Skill,
            SkillDomain,
            SkillCategory,
        )
        .join(
            Skill,
            Skill.skill_id
            == BookSkillMapping.skill_id,
        )
        .join(
            SkillDomain,
            SkillDomain.domain_id
            == Skill.domain_id,
        )
        .outerjoin(
            SkillCategory,
            SkillCategory.category_id
            == Skill.category_id,
        )
        .where(
            BookSkillMapping.document_id
            == document_id
        )
        .order_by(
            BookSkillMapping.updated_at.desc()
        )
    )

    if status:
        statement = statement.where(
            BookSkillMapping.mapping_status
            == status
        )

    rows = db.execute(statement).all()

    candidates = [
        BookSkillCandidateListItem(
            mapping=(
                BookSkillMappingResponse
                .model_validate(mapping)
            ),
            skill_slug=skill.slug,
            skill_name=skill.name,
            domain_name=domain.name,
            category_name=(
                category.name
                if category
                else None
            ),
        )
        for (
            mapping,
            skill,
            domain,
            category,
        ) in rows
    ]

    return BookSkillCandidateListResponse(
        document_id=document_id,
        candidate_count=len(candidates),
        candidates=candidates,
    )