import unittest

from src.intelligence.evidence import build_evidence_pack
from tests.fixtures.claim_validation_cases import CLUSTER_A, CLUSTER_B


class EvidencePackTests(unittest.TestCase):
    def test_analysis_receives_exactly_one_cluster(self) -> None:
        pack = build_evidence_pack(CLUSTER_A)

        self.assertEqual(pack.cluster_id, CLUSTER_A.id)
        self.assertTrue(all(item.cluster_id == CLUSTER_A.id for item in pack.evidence_items))
        self.assertNotEqual(pack.cluster_id, CLUSTER_B.id)

    def test_stable_source_and_evidence_ids_are_assigned_by_code(self) -> None:
        pack = build_evidence_pack(CLUSTER_A)

        self.assertEqual(pack.sources[0].source_id, "source_001")
        self.assertEqual(pack.evidence_items[0].evidence_id, "cluster_alpha_evidence_001")
