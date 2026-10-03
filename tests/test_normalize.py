import unittest

from src.intelligence.normalize import normalize_candidate, normalize_url
from tests.fixtures.intelligence_candidates import ROBOTICS_COMPANY


class NormalizeTests(unittest.TestCase):
    def test_candidate_normalization(self) -> None:
        normalized = normalize_candidate(ROBOTICS_COMPANY)

        self.assertEqual(normalized.source_url, "https://example.com/news/robotics-model")
        self.assertNotIn("  ", normalized.title)

    def test_url_tracking_parameters_are_removed(self) -> None:
        url = normalize_url("HTTPS://Example.com/path/?utm_source=x&keep=1&gclid=abc")

        self.assertEqual(url, "https://example.com/path?keep=1")
