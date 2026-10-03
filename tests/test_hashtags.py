from datetime import datetime
import unittest

from src.intelligence.hashtags import (
    FakeHashtagResearchProvider,
    HashtagResearchResult,
    select_hashtags,
    unresearched_hashtag_candidates,
)
from src.intelligence.models import (
    HashtagCandidate,
    HashtagResearchStatus,
    HashtagSource,
    TargetPlatform,
)
from tests.test_titles import _verified_story


class HashtagTests(unittest.TestCase):
    def test_hashtag_relevance_affects_ranking(self) -> None:
        relevant = _tag("#industrialrobotics", 0.95, "LOW")
        generic = _tag("#motivation", 0.05, "HIGH")

        selected = select_hashtags([generic, relevant], limit=1)

        self.assertEqual(selected[0].tag, "#industrialrobotics")

    def test_popularity_cannot_override_near_zero_relevance(self) -> None:
        generic = _tag("#motivation", 0.01, "HIGH")

        selected = select_hashtags([generic], limit=1)

        self.assertEqual(selected, [])
        self.assertEqual(generic.rejection_reason, "generic filler hashtag")

    def test_unresearched_hashtag_has_no_fake_reach(self) -> None:
        candidates = unresearched_hashtag_candidates(_verified_story(), TargetPlatform.INSTAGRAM)

        self.assertTrue(candidates)
        self.assertEqual(candidates[0].research_status, HashtagResearchStatus.UNRESEARCHED)
        self.assertIsNone(candidates[0].estimated_reach_band)

    def test_fake_research_provider_works_deterministically(self) -> None:
        provider = FakeHashtagResearchProvider([
            HashtagResearchResult("#robotics", 0.9, 0.7, "MEDIUM", "MEDIUM", datetime(2026, 10, 3))
        ])

        results = provider.research(["robotics"], TargetPlatform.INSTAGRAM)

        self.assertEqual(results[0].tag, "#robotics")

    def test_hashtag_limits_are_configurable(self) -> None:
        tags = [_tag(f"#tag{i}", 0.8, "LOW") for i in range(5)]

        selected = select_hashtags(tags, limit=2)

        self.assertEqual(len(selected), 2)


def _tag(tag: str, relevance: float, reach: str | None) -> HashtagCandidate:
    return HashtagCandidate(
        tag=tag,
        relevance_score=relevance,
        specificity_score=0.7,
        source=HashtagSource.LIVE_RESEARCH,
        research_status=HashtagResearchStatus.RESEARCHED if reach else HashtagResearchStatus.UNRESEARCHED,
        platform=TargetPlatform.INSTAGRAM,
        estimated_reach_band=reach,
        competition_band=None,
        researched_at=datetime(2026, 10, 3) if reach else None,
        supporting_topic_terms=["industrial robotics"],
    )
