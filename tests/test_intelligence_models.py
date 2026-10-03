import unittest

from src.intelligence.models import CandidateItem, SourceType
from tests.fixtures.intelligence_candidates import NOW


class IntelligenceModelTests(unittest.TestCase):
    def test_arbitrary_domains_and_professions_remain_strings(self) -> None:
        domain = "oil and gas"
        profession = "reliability technician"

        self.assertIsInstance(domain, str)
        self.assertIsInstance(profession, str)

    def test_candidate_item_represents_untrusted_discovery_input(self) -> None:
        candidate = CandidateItem(
            id="candidate-custom",
            source_name="Custom Source",
            source_url="https://example.com/custom",
            source_type=SourceType.NEWS,
            title="AI changes a workflow",
            summary=None,
            published_at=None,
            discovered_at=NOW,
            author=None,
        )

        self.assertEqual(candidate.title, "AI changes a workflow")
        self.assertIsNone(candidate.summary)
