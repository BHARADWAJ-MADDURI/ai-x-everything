import unittest

from src.intelligence.dedup import cluster_candidates
from src.intelligence.grounding import extract_grounded_facts
from src.intelligence.models import ClaimKind, EvidenceRole
from src.intelligence.normalize import normalize_candidate
from src.intelligence.sources import evidence_from_candidate
from tests.fixtures.intelligence_candidates import ROBOTICS_COMPANY, ROBOTICS_NEWS_DUPLICATE


class GroundingTests(unittest.TestCase):
    def test_primary_source_distinguishable_from_independent_evidence(self) -> None:
        company = evidence_from_candidate(normalize_candidate(ROBOTICS_COMPANY))
        news = evidence_from_candidate(normalize_candidate(ROBOTICS_NEWS_DUPLICATE))

        self.assertEqual(company.evidence_role, EvidenceRole.SECONDARY)
        self.assertFalse(company.is_independent)
        self.assertTrue(news.is_independent)

    def test_company_claim_is_not_automatically_independent_proof(self) -> None:
        company = evidence_from_candidate(normalize_candidate(ROBOTICS_COMPANY))

        self.assertIn("company_announcement", company.authoritative_for)
        self.assertFalse(company.is_independent)

    def test_facts_preserve_provenance(self) -> None:
        cluster = cluster_candidates([normalize_candidate(ROBOTICS_COMPANY)])[0]
        facts = extract_grounded_facts(cluster)

        self.assertEqual(facts[0].supporting_source_urls, [cluster.candidates[0].source_url])

    def test_fact_vs_inference_distinction_survives_grounding(self) -> None:
        cluster = cluster_candidates(
            [normalize_candidate(ROBOTICS_COMPANY), normalize_candidate(ROBOTICS_NEWS_DUPLICATE)]
        )[0]
        facts = extract_grounded_facts(cluster)

        self.assertIn(ClaimKind.FACT, {fact.claim_kind for fact in facts})
        self.assertIn(ClaimKind.INFERENCE, {fact.claim_kind for fact in facts})
