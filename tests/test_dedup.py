import unittest

from src.intelligence.dedup import cluster_candidates
from src.intelligence.normalize import normalize_candidate
from tests.fixtures.intelligence_candidates import (
    FOUNDATION_MODEL,
    ROBOTICS_COMPANY,
    ROBOTICS_NEWS_DUPLICATE,
)


class DedupTests(unittest.TestCase):
    def test_duplicate_urls_cluster(self) -> None:
        first = normalize_candidate(ROBOTICS_COMPANY)
        second = normalize_candidate(
            ROBOTICS_COMPANY.__class__(
                **{**ROBOTICS_COMPANY.__dict__, "id": "candidate-robotics-copy"}
            )
        )

        clusters = cluster_candidates([first, second])

        self.assertEqual(len(clusters), 1)
        self.assertEqual(len(clusters[0].candidates), 2)

    def test_similar_duplicate_story_coverage_can_cluster_conservatively(self) -> None:
        clusters = cluster_candidates(
            [normalize_candidate(ROBOTICS_COMPANY), normalize_candidate(ROBOTICS_NEWS_DUPLICATE)]
        )

        self.assertEqual(len(clusters), 1)

    def test_unrelated_stories_do_not_cluster(self) -> None:
        clusters = cluster_candidates(
            [normalize_candidate(ROBOTICS_COMPANY), normalize_candidate(FOUNDATION_MODEL)]
        )

        self.assertEqual(len(clusters), 2)
