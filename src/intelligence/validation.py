import re

from src.intelligence.models import (
    ClaimKind,
    ClaimValidationResult,
    EvidencePack,
    ValidationFailure,
    VerifiedClaimCandidate,
)


NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?%?\b")


def validate_claims(
    claims: list[VerifiedClaimCandidate],
    evidence_pack: EvidencePack,
) -> ClaimValidationResult:
    """Quarantine claims that violate provenance or closed-world rules."""

    evidence_by_id = {item.evidence_id: item for item in evidence_pack.evidence_items}
    source_ids = {source.source_id for source in evidence_pack.sources}
    source_urls = {source.source_url for source in evidence_pack.sources}
    valid = []
    rejected = []
    for claim in claims:
        reason = _claim_failure_reason(claim, evidence_by_id, source_ids, source_urls, evidence_pack.cluster_id)
        if reason:
            rejected.append(ValidationFailure(item_id=claim.claim_id, reason=reason))
        else:
            valid.append(claim)
    return ClaimValidationResult(valid_claims=valid, rejected_claims=rejected)


def _claim_failure_reason(claim, evidence_by_id, source_ids, source_urls, cluster_id) -> str | None:
    if claim.claim_type is ClaimKind.FACT and not claim.evidence_ids:
        return "FACT requires at least one evidence_id"
    for evidence_id in claim.evidence_ids:
        item = evidence_by_id.get(evidence_id)
        if item is None:
            return f"unknown evidence_id: {evidence_id}"
        if item.cluster_id != cluster_id:
            return f"evidence_id belongs to another cluster: {evidence_id}"
    for source_id in claim.referenced_source_ids:
        if source_id not in source_ids:
            return f"unknown source_id: {source_id}"
    for source_url in claim.referenced_source_urls:
        if source_url not in source_urls:
            return f"unknown source_url: {source_url}"
    if claim.numeric_claim and claim.claim_type is ClaimKind.FACT:
        claim_numbers = set(NUMBER_RE.findall(claim.text))
        if not claim_numbers:
            return "numeric_claim marked true but no number found"
        evidence_text = " ".join(evidence_by_id[evidence_id].supplied_text for evidence_id in claim.evidence_ids)
        evidence_numbers = set(NUMBER_RE.findall(evidence_text))
        if not claim_numbers <= evidence_numbers:
            return "numeric FACT lacks direct evidence for number"
    return None


def claim_ids(claims: list[VerifiedClaimCandidate]) -> set[str]:
    return {claim.claim_id for claim in claims}
