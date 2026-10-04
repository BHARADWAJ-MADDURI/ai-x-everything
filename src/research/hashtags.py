from datetime import datetime

from src.intelligence.hashtags import HashtagResearchResult
from src.intelligence.models import TargetPlatform


class CurrentEvidenceHashtagResearchProvider:
    """Relevance-only hashtag helper; it never invents reach or platform popularity."""

    def __init__(self, *, researched_at: datetime | None = None) -> None:
        self.researched_at = researched_at

    def research(self, topic_terms: list[str], platform: TargetPlatform) -> list[HashtagResearchResult]:
        results = []
        for term in dict.fromkeys(topic_terms):
            tag = "#" + "".join(ch for ch in term.title() if ch.isalnum())
            if len(tag) <= 1:
                continue
            results.append(
                HashtagResearchResult(
                    tag=tag,
                    relevance_score=0.75,
                    specificity_score=0.7,
                    estimated_reach_band=None,
                    competition_band=None,
                    researched_at=self.researched_at,
                )
            )
        return results
