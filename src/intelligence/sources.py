from src.intelligence.models import CandidateItem, EvidenceRole, EvidenceSource, SourceType


def evidence_from_candidate(candidate: CandidateItem) -> EvidenceSource:
    """Convert a candidate into explicit evidence context."""

    if candidate.source_type in {SourceType.PRIMARY, SourceType.RESEARCH, SourceType.GOVERNMENT}:
        role = EvidenceRole.PRIMARY
    else:
        role = EvidenceRole.SECONDARY

    is_independent = candidate.source_type not in {SourceType.COMPANY}
    authoritative_for = []
    if candidate.source_type == SourceType.COMPANY:
        authoritative_for = ["company_announcement"]
    elif candidate.source_type == SourceType.RESEARCH:
        authoritative_for = ["research_result"]
    elif candidate.source_type == SourceType.GOVERNMENT:
        authoritative_for = ["regulatory_publication"]
    elif candidate.source_type == SourceType.PRIMARY:
        authoritative_for = ["primary_claim"]

    evidence_score = {
        SourceType.RESEARCH: 0.9,
        SourceType.GOVERNMENT: 0.9,
        SourceType.PRIMARY: 0.8,
        SourceType.NEWS: 0.7,
        SourceType.COMPANY: 0.6,
        SourceType.OTHER: 0.35,
    }[candidate.source_type]

    return EvidenceSource(
        candidate_id=candidate.id,
        source_name=candidate.source_name,
        source_url=candidate.source_url,
        source_type=candidate.source_type,
        evidence_role=role,
        is_independent=is_independent,
        authoritative_for=authoritative_for,
        evidence_score=evidence_score,
        source_id="",
    )


def evidence_quality(sources: list[EvidenceSource]) -> float:
    if not sources:
        return 0.0
    base = sum(source.evidence_score for source in sources) / len(sources)
    has_independent = any(source.is_independent for source in sources)
    has_primary = any(source.evidence_role is EvidenceRole.PRIMARY for source in sources)
    bonus = (0.08 if has_independent else 0.0) + (0.06 if has_primary else 0.0)
    return min(1.0, base + bonus)
