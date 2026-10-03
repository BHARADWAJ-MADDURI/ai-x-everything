from datetime import datetime

from src.intelligence.evidence import build_evidence_pack
from src.intelligence.models import CandidateItem, SourceType, StoryCluster


CLUSTER_A = StoryCluster(
    id="cluster_alpha",
    candidates=[
        CandidateItem(
            id="candidate_alpha",
            source_name="Company A",
            source_url="https://example.com/alpha",
            source_type=SourceType.COMPANY,
            title="Company A releases robotics model Alpha",
            summary="Company A released robotics model Alpha for visual inspection assistance.",
            published_at=datetime(2026, 10, 1, 9, 0),
            discovered_at=datetime(2026, 10, 3, 12, 0),
        )
    ],
)

CLUSTER_B = StoryCluster(
    id="cluster_beta",
    candidates=[
        CandidateItem(
            id="candidate_beta",
            source_name="Factory B",
            source_url="https://example.com/beta",
            source_type=SourceType.NEWS,
            title="Factory B reports inspection improvement with another system",
            summary="Factory B reported a 25% inspection improvement using a different inspection system.",
            published_at=datetime(2026, 10, 2, 9, 0),
            discovered_at=datetime(2026, 10, 3, 12, 0),
        )
    ],
)

PACK_A = build_evidence_pack(CLUSTER_A)
PACK_B = build_evidence_pack(CLUSTER_B)
