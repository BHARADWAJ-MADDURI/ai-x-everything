import unittest

from src.intelligence.models import AngleType, ClaimKind, PotentialAngle, StoryAnalysis, VerifiedClaimCandidate
from src.intelligence.validation import validate_claims
from src.intelligence.verified import build_verified_grounded_story
from src.shared.models import Audience
from tests.fixtures.claim_validation_cases import PACK_A


class VerifiedStoryTests(unittest.TestCase):
    def test_invalid_claims_cannot_enter_verified_grounded_story(self) -> None:
        valid = VerifiedClaimCandidate(
            "claim_001",
            "Model Alpha assists visual inspection.",
            ClaimKind.FACT,
            [PACK_A.evidence_items[0].evidence_id],
        )
        invalid = VerifiedClaimCandidate("claim_002", "Invented fact.", ClaimKind.FACT, [])
        result = validate_claims([valid, invalid], PACK_A)
        story = build_verified_grounded_story(
            evidence_pack=PACK_A,
            raw_analysis=StoryAnalysis(
                development_summary="Model Alpha assists visual inspection.",
                technologies=["robotics"],
                applications=["visual inspection"],
            ),
            valid_claims=result.valid_claims,
            rejected_claims=result.rejected_claims,
            angles=[],
        )

        self.assertEqual([claim.claim_id for claim in story.verified_claims], ["claim_001"])
        self.assertEqual(len(story.rejected_claims), 1)

    def test_generation_boundary_uses_verified_data(self) -> None:
        valid = VerifiedClaimCandidate(
            "claim_001",
            "Model Alpha assists visual inspection.",
            ClaimKind.FACT,
            [PACK_A.evidence_items[0].evidence_id],
        )
        result = validate_claims([valid], PACK_A)
        story = build_verified_grounded_story(
            evidence_pack=PACK_A,
            raw_analysis=StoryAnalysis(development_summary="Model Alpha assists visual inspection."),
            valid_claims=result.valid_claims,
            rejected_claims=result.rejected_claims,
            angles=[],
        )

        self.assertEqual(story.analysis.verified_claim_ids, ["claim_001"])

    def test_career_and_upskill_cannot_use_another_cluster(self) -> None:
        valid = VerifiedClaimCandidate(
            "claim_001",
            "Model Alpha assists visual inspection.",
            ClaimKind.FACT,
            [PACK_A.evidence_items[0].evidence_id],
        )
        result = validate_claims([valid], PACK_A)
        angle = PotentialAngle(
            id="career",
            angle_type=AngleType.CAREER,
            thesis="Inspectors should learn robotics diagnostics.",
            target_audiences=[Audience.PROFESSIONAL],
            evidence_strength=0.8,
            relevance=0.8,
            novelty=0.5,
            usefulness=0.7,
            speculation_risk=0.3,
            supporting_fact_ids=["claim_other_cluster"],
        )
        story = build_verified_grounded_story(
            evidence_pack=PACK_A,
            raw_analysis=StoryAnalysis(
                development_summary="Model Alpha assists visual inspection.",
                workflows=["visual inspection"],
                professions=["factory inspector"],
            ),
            valid_claims=result.valid_claims,
            rejected_claims=result.rejected_claims,
            angles=[angle],
        )

        self.assertEqual(story.validated_angles, [])
