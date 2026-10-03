from dataclasses import replace

from src.intelligence.models import EvidenceItem, EvidencePack, StoryCluster
from src.intelligence.sources import evidence_from_candidate


def build_evidence_pack(cluster: StoryCluster) -> EvidencePack:
    """Build a closed-world evidence pack for exactly one story cluster."""

    sources = []
    items = []
    for index, candidate in enumerate(cluster.candidates, start=1):
        source_id = f"source_{index:03d}"
        evidence_id = f"{cluster.id}_evidence_{index:03d}"
        source = replace(evidence_from_candidate(candidate), source_id=source_id)
        sources.append(source)
        items.append(
            EvidenceItem(
                evidence_id=evidence_id,
                cluster_id=cluster.id,
                source_id=source_id,
                source_url=candidate.source_url,
                source_type=candidate.source_type,
                supplied_text=candidate.summary or candidate.title,
                published_at=candidate.published_at,
            )
        )
    return EvidencePack(
        cluster_id=cluster.id,
        canonical_title=cluster.title,
        sources=sources,
        evidence_items=items,
    )
