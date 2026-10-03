from src.intelligence.models import ClaimKind, FactType, GroundedFact, StoryCluster


def extract_grounded_facts(cluster: StoryCluster) -> list[GroundedFact]:
    """Extract minimal grounded facts from normalized candidate coverage."""

    facts: list[GroundedFact] = []
    for index, candidate in enumerate(cluster.candidates, start=1):
        claim = candidate.summary or candidate.title
        facts.append(
            GroundedFact(
                id=f"{cluster.id}-fact-{index}",
                claim=claim,
                supporting_source_urls=[candidate.source_url],
                confidence=0.75,
                fact_type=_guess_fact_type(claim),
                claim_kind=ClaimKind.FACT,
            )
        )
    if len(cluster.candidates) > 1:
        facts.append(
            GroundedFact(
                id=f"{cluster.id}-inference-1",
                claim="Multiple sources appear to cover the same underlying development.",
                supporting_source_urls=[candidate.source_url for candidate in cluster.candidates],
                confidence=0.65,
                fact_type=FactType.OTHER,
                claim_kind=ClaimKind.INFERENCE,
            )
        )
    return facts


def _guess_fact_type(text: str) -> FactType:
    lowered = text.lower()
    if "research" in lowered or "study" in lowered:
        return FactType.RESEARCH_RESULT
    if "limitation" in lowered or "risk" in lowered or "not yet" in lowered:
        return FactType.LIMITATION
    if "workflow" in lowered or "maintenance" in lowered or "diagnostic" in lowered:
        return FactType.WORKFLOW_IMPACT
    if "launch" in lowered or "announce" in lowered or "introduce" in lowered:
        return FactType.ANNOUNCEMENT
    if "can" in lowered or "capability" in lowered:
        return FactType.CAPABILITY
    return FactType.OTHER
