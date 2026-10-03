import unittest

from src.intelligence.models import ClaimKind, VerifiedClaimCandidate
from src.intelligence.validation import validate_claims
from tests.fixtures.claim_validation_cases import PACK_A, PACK_B


class ClaimValidationTests(unittest.TestCase):
    def test_cross_cluster_evidence_is_rejected(self) -> None:
        claim = VerifiedClaimCandidate(
            claim_id="claim_001",
            text="Model Alpha improved factory inspection by 25%.",
            claim_type=ClaimKind.FACT,
            evidence_ids=[PACK_B.evidence_items[0].evidence_id],
            numeric_claim=True,
        )

        result = validate_claims([claim], PACK_A)

        self.assertEqual(len(result.valid_claims), 0)
        self.assertIn("unknown evidence_id", result.rejected_claims[0].reason)

    def test_unknown_evidence_id_rejected(self) -> None:
        claim = VerifiedClaimCandidate(
            claim_id="claim_002",
            text="Model Alpha assists visual inspection.",
            claim_type=ClaimKind.FACT,
            evidence_ids=["evidence_999"],
        )

        result = validate_claims([claim], PACK_A)

        self.assertIn("unknown evidence_id", result.rejected_claims[0].reason)

    def test_fact_without_evidence_rejected(self) -> None:
        claim = VerifiedClaimCandidate(
            claim_id="claim_003",
            text="Model Alpha assists visual inspection.",
            claim_type=ClaimKind.FACT,
            evidence_ids=[],
        )

        result = validate_claims([claim], PACK_A)

        self.assertIn("FACT requires", result.rejected_claims[0].reason)

    def test_inference_and_interpretation_keep_labels(self) -> None:
        inference = VerifiedClaimCandidate(
            claim_id="claim_004",
            text="This could affect inspection workflows.",
            claim_type=ClaimKind.INFERENCE,
            evidence_ids=[PACK_A.evidence_items[0].evidence_id],
        )
        interpretation = VerifiedClaimCandidate(
            claim_id="claim_005",
            text="This is worth explaining to professionals.",
            claim_type=ClaimKind.INTERPRETATION,
            evidence_ids=[],
        )

        result = validate_claims([inference, interpretation], PACK_A)

        self.assertEqual(result.valid_claims[0].claim_type, ClaimKind.INFERENCE)
        self.assertEqual(result.valid_claims[1].claim_type, ClaimKind.INTERPRETATION)

    def test_invented_source_url_rejected(self) -> None:
        claim = VerifiedClaimCandidate(
            claim_id="claim_006",
            text="Model Alpha assists visual inspection.",
            claim_type=ClaimKind.FACT,
            evidence_ids=[PACK_A.evidence_items[0].evidence_id],
            referenced_source_urls=["https://invented.example/source"],
        )

        result = validate_claims([claim], PACK_A)

        self.assertIn("unknown source_url", result.rejected_claims[0].reason)

    def test_invented_source_id_rejected(self) -> None:
        claim = VerifiedClaimCandidate(
            claim_id="claim_007",
            text="Model Alpha assists visual inspection.",
            claim_type=ClaimKind.FACT,
            evidence_ids=[PACK_A.evidence_items[0].evidence_id],
            referenced_source_ids=["source_999"],
        )

        result = validate_claims([claim], PACK_A)

        self.assertIn("unknown source_id", result.rejected_claims[0].reason)

    def test_unsupported_numeric_fact_rejected(self) -> None:
        claim = VerifiedClaimCandidate(
            claim_id="claim_008",
            text="Model Alpha improved inspection by 40%.",
            claim_type=ClaimKind.FACT,
            evidence_ids=[PACK_A.evidence_items[0].evidence_id],
            numeric_claim=True,
        )

        result = validate_claims([claim], PACK_A)

        self.assertIn("numeric FACT", result.rejected_claims[0].reason)

    def test_unknown_empty_fields_are_accepted(self) -> None:
        claim = VerifiedClaimCandidate(
            claim_id="claim_009",
            text="UNKNOWN",
            claim_type=ClaimKind.INTERPRETATION,
            evidence_ids=[],
        )

        result = validate_claims([claim], PACK_A)

        self.assertEqual(result.valid_claims[0].text, "UNKNOWN")
