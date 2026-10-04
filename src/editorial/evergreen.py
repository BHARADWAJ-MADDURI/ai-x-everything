from datetime import datetime

from src.editorial.models import EvergreenItem
from src.intelligence.models import PotentialAngle, VerifiedGroundedStory


def evergreen_from_angle(
    story: VerifiedGroundedStory,
    angle: PotentialAngle,
    *,
    created_at: datetime,
    review_at: datetime | None = None,
    expires_at: datetime | None = None,
) -> EvergreenItem:
    return EvergreenItem(
        item_id=f"evergreen-{story.cluster_id}-{angle.id}",
        originating_story_id=story.cluster_id,
        angle_id=angle.id,
        angle_type=angle.angle_type,
        proposed_thesis=angle.thesis,
        evidence_claim_refs=list(angle.supporting_fact_ids),
        created_at=created_at,
        review_at=review_at,
        expires_at=expires_at,
        audience=list(angle.target_audiences),
    )
