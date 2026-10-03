import unittest

from src.intelligence.models import ClaimKind, TargetPlatform, TitleCandidate, TitleType, VerifiedClaimCandidate
from src.intelligence.titles import generate_title_candidates, validate_title
from src.intelligence.validation import validate_claims
from src.intelligence.verified import build_verified_grounded_story
from src.intelligence.models import StoryAnalysis
from tests.fixtures.claim_validation_cases import PACK_A


class TitleTests(unittest.TestCase):
    def test_grounded_title_succeeds_and_retains_claim_ids(self) -> None:
        story = _verified_story()
        candidate = TitleCandidate(
            text="How AI is changing visual inspection",
            title_type=TitleType.EXPLAINER,
            supported_claim_ids=["claim_001"],
            target_platform=TargetPlatform.WEBSITE,
            hook_strength=0.7,
            clarity=0.8,
            hype_risk=0.2,
        )

        validated, failure = validate_title(candidate, story)

        self.assertIsNone(failure)
        self.assertEqual(validated.supported_claim_ids, ["claim_001"])

    def test_hallucinated_title_fails(self) -> None:
        story = _verified_story()
        candidate = TitleCandidate(
            text="AI eliminates 50% of factory inspection jobs",
            title_type=TitleType.IMPACT,
            supported_claim_ids=[],
            target_platform=TargetPlatform.INSTAGRAM,
            hook_strength=0.9,
            clarity=0.6,
            hype_risk=0.95,
        )

        validated, failure = validate_title(candidate, story)

        self.assertTrue(validated.rejected)
        self.assertIsNotNone(failure)

    def test_arbitrary_platform_title_metadata_works(self) -> None:
        story = _verified_story()
        titles = generate_title_candidates(story, target_platform=TargetPlatform.LINKEDIN)

        self.assertEqual(titles[0].target_platform, TargetPlatform.LINKEDIN)


def _verified_story():
    claim = VerifiedClaimCandidate(
        "claim_001",
        "Model Alpha assists visual inspection.",
        ClaimKind.FACT,
        [PACK_A.evidence_items[0].evidence_id],
    )
    result = validate_claims([claim], PACK_A)
    return build_verified_grounded_story(
        evidence_pack=PACK_A,
        raw_analysis=StoryAnalysis(
            development_summary="AI system assists visual inspection",
            technologies=["robotics"],
            applications=["visual inspection"],
        ),
        valid_claims=result.valid_claims,
        rejected_claims=result.rejected_claims,
        angles=[],
    )
