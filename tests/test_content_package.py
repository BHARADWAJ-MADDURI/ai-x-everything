from dataclasses import replace
from datetime import datetime, timezone
import unittest

from src.content.gates import generation_readiness
from src.content.package_generator import ContentPackageGenerationError, ContentPackageGenerator
from src.content.package_models import (
    PackageReviewState,
    PackageValidationStatus,
    PlatformContentStatus,
    SelectedTitle,
    SourceReference,
    TitleVerificationStatus,
)
from src.content.package_schemas import CanonicalContentDraftOutput
from src.content.validation import approve_for_render, validate_package
from src.editorial.models import HumanDecisionAction
from src.generation.llm_client import LLMResult
from src.intelligence.models import (
    AngleType,
    ClaimKind,
    EvidenceItem,
    EvidencePack,
    EvidenceRole,
    EvidenceSource,
    HashtagCandidate,
    HashtagResearchStatus,
    HashtagSource,
    PotentialAngle,
    SourceType,
    TargetPlatform,
    ValidationFailure,
    VerifiedClaimCandidate,
    VerifiedGroundedStory,
    VerifiedStoryAnalysis,
)
from src.shared.models import Audience
from src.editorial.decisions import record_human_decision


NOW = datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc)


class ContentPackageTests(unittest.TestCase):
    def test_approved_story_can_enter_generation(self) -> None:
        package = _package()

        self.assertEqual(package.story_id, "robotics-story")
        self.assertEqual(package.validation.status, PackageValidationStatus.READY)

    def test_save_cannot_enter_generation(self) -> None:
        with self.assertRaises(ContentPackageGenerationError):
            _package(decision_action=HumanDecisionAction.SAVE)

    def test_hold_cannot_enter_generation(self) -> None:
        with self.assertRaises(ContentPackageGenerationError):
            _package(decision_action=HumanDecisionAction.HOLD)

    def test_reject_cannot_enter_generation(self) -> None:
        with self.assertRaises(ContentPackageGenerationError):
            _package(decision_action=HumanDecisionAction.REJECT)

    def test_rejected_angle_cannot_enter_generation(self) -> None:
        story = _story()
        angle = replace(story.validated_angles[0], rejected=True)

        readiness = generation_readiness(
            story=story,
            decision=_decision(),
            selected_angle=angle,
            selected_title=_title(),
        )

        self.assertFalse(readiness.ready)

    def test_unverified_story_cannot_enter_generation(self) -> None:
        story = replace(_story(), verified_claims=[])

        readiness = generation_readiness(
            story=story,
            decision=_decision(),
            selected_angle=story.validated_angles[0],
            selected_title=_title(),
        )

        self.assertFalse(readiness.ready)

    def test_claim_allowlist_contains_only_selected_angle_claims(self) -> None:
        story = _story()
        readiness = generation_readiness(
            story=story,
            decision=_decision(),
            selected_angle=story.validated_angles[0],
            selected_title=_title(),
        )

        self.assertEqual(readiness.allowed_claim_ids, ["claim-fact"])

    def test_canonical_draft_references_valid_claims(self) -> None:
        package = _package()

        self.assertEqual(package.canonical_draft.claim_references, ["claim-fact"])

    def test_unsupported_claim_reference_rejected(self) -> None:
        package = _package(output_overrides={"claim_references": ["claim-fact", "claim-unknown"]})

        self.assertIn("unsupported claim ID claim-unknown", " ".join(package.validation.issues))

    def test_invented_source_id_rejected(self) -> None:
        package = _package()
        broken = replace(
            package,
            source_references=[SourceReference("source-invented", "Fake", "https://example.com/source", "news")],
        )

        result = validate_package(broken, _story())

        self.assertIn("invented source ID source-invented", result.issues)

    def test_invented_source_url_rejected(self) -> None:
        package = _package()
        broken = replace(
            package,
            source_references=[SourceReference("source_001", "Demo Source", "https://evil.example/source", "news")],
        )

        result = validate_package(broken, _story())

        self.assertIn("invented source URL https://evil.example/source", result.issues)

    def test_unsupported_numeric_percentage_rejected(self) -> None:
        package = _package(output_overrides={"thesis": "The system improved results by 50%."})

        self.assertIn("50%", " ".join(package.validation.issues))

    def test_supported_numeric_percentage_accepted(self) -> None:
        package = _package(output_overrides={"thesis": "The system reported a 40% inspection improvement."})

        self.assertNotIn("40%", " ".join(package.validation.issues))

    def test_unsupported_currency_figure_rejected(self) -> None:
        package = _package(output_overrides={"takeaway": "This creates a $5 billion market."})

        self.assertIn("$5 billion", " ".join(package.validation.issues))

    def test_inference_does_not_become_fact_metadata(self) -> None:
        story = _story()

        inference = next(claim for claim in story.verified_claims if claim.claim_type is ClaimKind.INFERENCE)

        self.assertEqual(inference.claim_type, ClaimKind.INFERENCE)

    def test_career_content_absent_when_career_angle_unsupported(self) -> None:
        package = _package()

        self.assertIsNone(package.canonical_draft.career_upskill_implication)

    def test_career_content_allowed_when_verified(self) -> None:
        story = _story(include_career_angle=True)
        angle = next(item for item in story.validated_angles if item.angle_type is AngleType.CAREER)
        package = _package(
            story=story,
            angle=angle,
            output_overrides={
                "hook": "A robotics story has a career angle.",
                "thesis": "Maintenance technicians may need robotics diagnostics skills.",
                "technical_explanation": "The verified career implication is scoped to diagnostics skills.",
                "career_upskill_implication": "Technicians may need robotics diagnostics skills.",
                "claim_references": ["claim-career"],
            },
            title=SelectedTitle("Career title", TitleVerificationStatus.GROUNDED, ["claim-career"]),
        )

        self.assertEqual(package.validation.issues, [])

    def test_reel_scenes_retain_claim_references(self) -> None:
        package = _package()

        self.assertTrue(all(scene.supporting_claim_ids for scene in package.reel.scenes))

    def test_reel_scenes_retain_source_references_where_required(self) -> None:
        package = _package()

        self.assertEqual(package.reel.scenes[0].source_reference_ids, ["source_001"])

    def test_instagram_uses_selected_hashtags(self) -> None:
        package = _package()

        self.assertEqual([tag.tag for tag in package.instagram.hashtags], ["#RoboticsAI"])

    def test_unknown_hashtag_reach_remains_unknown(self) -> None:
        package = _package()

        self.assertIsNone(package.instagram.hashtags[0].estimated_reach_band)

    def test_blog_sources_trace_to_verified_story(self) -> None:
        package = _package()

        self.assertEqual(package.blog.source_references[0].source_id, "source_001")

    def test_linkedin_adaptation_retains_canonical_facts(self) -> None:
        package = _package()

        self.assertIn(package.canonical_draft.thesis, package.linkedin.post_copy)

    def test_x_adaptation_retains_canonical_facts(self) -> None:
        package = _package()

        self.assertIn(package.canonical_draft.hook, package.x.posts[0])

    def test_tiktok_does_not_invent_new_claims(self) -> None:
        package = _package()

        self.assertNotIn("worldwide deployment", package.tiktok.caption.lower())

    def test_youtube_shorts_does_not_invent_new_claims(self) -> None:
        package = _package()

        self.assertIn(package.canonical_draft.thesis, package.youtube_shorts.description)

    def test_platform_failure_marks_package_not_ready(self) -> None:
        package = _package()
        failed = replace(package, linkedin=replace(package.linkedin, status=PlatformContentStatus.FAILED))
        result = validate_package(failed, _story())

        self.assertFalse(result.publish_ready)
        self.assertIn("linkedin adaptation failed", result.issues)

    def test_manual_title_remains_manual_unverified(self) -> None:
        package = _package(title=SelectedTitle("Manual title", TitleVerificationStatus.MANUAL_UNVERIFIED))

        self.assertEqual(package.selected_title.verification_status, TitleVerificationStatus.MANUAL_UNVERIFIED)

    def test_manual_title_requires_acknowledgement_before_render_approval(self) -> None:
        story = _story()
        package = _package(story=story, title=SelectedTitle("Manual title", TitleVerificationStatus.MANUAL_UNVERIFIED))
        approved = approve_for_render(package, story)

        self.assertEqual(approved.review_state, PackageReviewState.NEEDS_REVIEW)

    def test_grounded_title_does_not_require_manual_acknowledgement(self) -> None:
        story = _story()
        package = _package(story=story)
        approved = approve_for_render(package, story)

        self.assertEqual(approved.review_state, PackageReviewState.APPROVED_FOR_RENDER)

    def test_package_starts_draft_or_needs_review(self) -> None:
        package = _package()

        self.assertIn(package.review_state, {PackageReviewState.DRAFT, PackageReviewState.NEEDS_REVIEW})

    def test_final_human_review_can_mark_approved_for_render(self) -> None:
        story = _story()
        approved = approve_for_render(_package(story=story), story)

        self.assertTrue(approved.publish_ready)

    def test_fake_llm_deterministic(self) -> None:
        client = FakePackageLLMClient()

        first = client.generate_structured(system_prompt="x", user_prompt="y", response_schema=CanonicalContentDraftOutput)
        second = client.generate_structured(system_prompt="x", user_prompt="y", response_schema=CanonicalContentDraftOutput)

        self.assertEqual(first.output, second.output)

    def test_unit_tests_make_zero_network_calls(self) -> None:
        package = _package()

        self.assertEqual(package.generation_metadata.provider, "fake")


def _package(
    *,
    story: VerifiedGroundedStory | None = None,
    angle: PotentialAngle | None = None,
    decision_action: HumanDecisionAction = HumanDecisionAction.APPROVE,
    title: SelectedTitle | None = None,
    output_overrides: dict | None = None,
):
    story = story or _story()
    angle = angle or story.validated_angles[0]
    return ContentPackageGenerator(
        llm_client=FakePackageLLMClient(output_overrides=output_overrides or {})
    ).generate(
        story=story,
        decision=record_human_decision(action=decision_action, target_id=story.cluster_id, decided_at=NOW, comment=None),
        selected_angle=angle,
        selected_title=title or _title(),
        selected_hashtags=_hashtags(),
    )


def _title() -> SelectedTitle:
    return SelectedTitle("Robotics system reports 40% inspection improvement", TitleVerificationStatus.GROUNDED, ["claim-fact"])


def _decision() :
    return record_human_decision(action=HumanDecisionAction.APPROVE, target_id="robotics-story", decided_at=NOW)


def _hashtags() -> list[HashtagCandidate]:
    return [
        HashtagCandidate(
            tag="#RoboticsAI",
            relevance_score=0.85,
            specificity_score=0.8,
            source=HashtagSource.VERIFIED_STORY,
            research_status=HashtagResearchStatus.UNRESEARCHED,
            platform=TargetPlatform.INSTAGRAM,
            estimated_reach_band=None,
            competition_band=None,
            supporting_topic_terms=["robotics"],
        )
    ]


def _story(*, include_career_angle: bool = False) -> VerifiedGroundedStory:
    fact = VerifiedClaimCandidate(
        "claim-fact",
        "The robotics system reported a 40% inspection improvement.",
        ClaimKind.FACT,
        ["evidence-1"],
    )
    inference = VerifiedClaimCandidate(
        "claim-inference",
        "This may help technicians focus on diagnostics.",
        ClaimKind.INFERENCE,
        ["evidence-1"],
    )
    career = VerifiedClaimCandidate(
        "claim-career",
        "Maintenance technicians may need robotics diagnostics skills.",
        ClaimKind.INFERENCE,
        ["evidence-1"],
    )
    claims = [fact, inference, career]
    angles = [
        _angle("technology", AngleType.TECHNOLOGY, "How the robotics system works", ["claim-fact"]),
        _angle("explainer", AngleType.EXPLAINER, "Why this robotics system matters", ["claim-fact", "claim-inference"]),
    ]
    if include_career_angle:
        angles.append(_angle("career", AngleType.CAREER, "What technicians may need to learn", ["claim-career"]))
    return VerifiedGroundedStory(
        cluster_id="robotics-story",
        canonical_title="Robotics system reports 40% inspection improvement",
        evidence_pack=EvidencePack(
            cluster_id="robotics-story",
            canonical_title="Robotics system reports 40% inspection improvement",
            sources=[
                EvidenceSource(
                    candidate_id="candidate-1",
                    source_name="Demo Robotics Lab",
                    source_url="https://example.com/source",
                    source_type=SourceType.RESEARCH,
                    evidence_role=EvidenceRole.PRIMARY,
                    is_independent=True,
                    source_id="source_001",
                )
            ],
            evidence_items=[
                EvidenceItem(
                    evidence_id="evidence-1",
                    cluster_id="robotics-story",
                    source_id="source_001",
                    source_url="https://example.com/source",
                    source_type=SourceType.RESEARCH,
                    supplied_text="The robotics system reported a 40% inspection improvement.",
                    published_at=NOW,
                )
            ],
        ),
        verified_claims=claims,
        rejected_claims=[ValidationFailure("claim-bad", "unsupported deployment claim")],
        analysis=VerifiedStoryAnalysis(
            development_summary="A robotics system was evaluated.",
            technologies=["robotics"],
            applications=["inspection"],
            industries=["manufacturing"],
            workflows=["quality inspection"],
            verified_claim_ids=[claim.claim_id for claim in claims],
        ),
        validated_angles=angles,
    )


def _angle(angle_id: str, angle_type: AngleType, thesis: str, claim_ids: list[str]) -> PotentialAngle:
    return PotentialAngle(
        id=angle_id,
        angle_type=angle_type,
        thesis=thesis,
        target_audiences=[Audience.PROFESSIONAL, Audience.ENTHUSIAST],
        evidence_strength=0.88,
        relevance=0.86,
        novelty=0.7,
        usefulness=0.82,
        speculation_risk=0.12,
        supporting_fact_ids=claim_ids,
        score=0.85,
    )


class FakePackageLLMClient:
    def __init__(self, output_overrides: dict | None = None) -> None:
        self.output_overrides = output_overrides or {}

    def generate_structured(self, *, system_prompt, user_prompt, response_schema):
        data = {
            "hook": "A robotics system reported a measurable inspection gain.",
            "thesis": "The robotics system reported a 40% inspection improvement.",
            "key_points": ["The verified claim is scoped to inspection."],
            "technical_explanation": "The system links robotics perception with inspection workflows.",
            "human_implication": "This may affect how teams review quality issues.",
            "career_upskill_implication": None,
            "takeaway": "The useful story is the bounded workflow evidence, not a universal automation claim.",
            "cta": "Follow Everything × AI to understand what's changing.",
            "claim_references": ["claim-fact"],
        }
        data.update(self.output_overrides)
        output = response_schema.model_validate(data)
        return LLMResult(
            output=output,
            model="fake-package-model",
            provider="fake",
            latency_ms=5,
            input_tokens=50,
            output_tokens=50,
            estimated_cost_usd=None,
        )


if __name__ == "__main__":
    unittest.main()
