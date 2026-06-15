from pydantic import BaseModel
from fastapi import APIRouter

from app.core.domains import DOMAIN_LABELS
from app.services.domain_classifier import classify_domains

router = APIRouter()


class ClassifyDomainRequest(BaseModel):
    text: str


class ClassifyDomainResponse(BaseModel):
    primary_domain: str
    domains: list[str]
    labels: dict[str, str]
    scores: dict[str, int]


@router.get("/domains")
def list_domains():
    return {
        "domains": DOMAIN_LABELS,
    }


@router.post("/classify-domain", response_model=ClassifyDomainResponse)
def classify_domain(request: ClassifyDomainRequest):
    classification = classify_domains(request.text)

    return ClassifyDomainResponse(
        primary_domain=classification.primary_domain,
        domains=classification.domains,
        labels={
            domain: DOMAIN_LABELS.get(domain, domain)
            for domain in classification.domains
        },
        scores=classification.scores,
    )