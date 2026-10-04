from datetime import date, datetime, timedelta, timezone
import unittest

from src.editorial.decisions import record_human_decision
from src.editorial.evergreen import evergreen_from_angle
from src.editorial.history import available_angles, follow_up_potential, materially_different_angle, rejected_angles
from src.editorial.lifecycle import transition_story
from src.editorial.models import (
    AngleHistory,
    AnglePublicationRecord,
    EditorialUrgency,
    FollowUpPotential,
    HumanDecisionAction,
    ShelfLife,
    StoryLifecycleStatus,
    StoryPlanningInput,
)
from src.editorial.planner import EditorialPlanner
from src.editorial.relationships import bundle_candidates, infer_story_relationships
from src.editorial.timing import assess_timing
from src.intelligence.models import (
    AngleType,
    ClaimKind,
    EvidenceItem,
    EvidencePack,
    EvidenceRole,
    EvidenceSource,
    PotentialAngle,
    SourceType,
    TargetPlatform,
    VerifiedClaimCandidate,
    VerifiedGroundedStory,
    VerifiedStoryAnalysis,
)
from src.shared.models import Audience


NOW = datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc)


class EditorialPlannerTests(unittest.TestCase):
    def test_valid_lifecycle_transition(self) -> None:
        self.assertEqual(
            transition_story(StoryLifecycleStatus.VERIFIED, StoryLifecycleStatus.SELECTED),
            StoryLifecycleStatus.SELECTED,
        )

    def test_invalid_lifecycle_transition_rejected(self) -> None:
        with self.assertRaises(ValueError):
            transition_story(StoryLifecycleStatus.PUBLISHED, StoryLifecycleStatus.DISCOVERED)

    def test_breaking_distinct_from_importance(self) -> None:
        story = _planning_story("weak-breaking", score=0.25, published_at=NOW - timedelta(hours=2))
        plan = EditorialPlanner().plan(plan_date=date(2026, 10, 3), now=NOW, stories=[story])

        self.assertEqual(story.timing.urgency, EditorialUrgency.BREAKING)
        self.assertEqual(plan.recommended_posts, [])
        self.assertEqual(plan.held_items[0].reason, "Below editorial threshold.")

    def test_unknown_published_at_does_not_invent_publish_by(self) -> None:
        timing = assess_timing(published_at=None, now=NOW)

        self.assertIsNone(timing.publish_by)

    def test_freshness_decreases_with_age(self) -> None:
        fresh = assess_timing(published_at=NOW - timedelta(hours=2), now=NOW)
        older = assess_timing(published_at=NOW - timedelta(days=5), now=NOW)

        self.assertGreater(fresh.freshness_score, older.freshness_score)

    def test_evergreen_does_not_expire_like_breaking_news(self) -> None:
        timing = assess_timing(published_at=NOW - timedelta(days=100), now=NOW, evergreen=True)

        self.assertEqual(timing.urgency, EditorialUrgency.EVERGREEN)
        self.assertEqual(timing.shelf_life, ShelfLife.LONG)
        self.assertIsNone(timing.publish_by)

    def test_published_angle_excluded_from_identical_recommendation(self) -> None:
        story = _planning_story("robotics")
        history = _history("robotics", AngleType.NEWS)

        angles = available_angles("robotics", story.story.validated_angles, history)

        self.assertNotIn(AngleType.NEWS, {angle.angle_type for angle in angles})

    def test_unused_angle_remains_available(self) -> None:
        story = _planning_story("robotics")
        history = _history("robotics", AngleType.NEWS)

        self.assertIn(AngleType.TECHNOLOGY, {angle.angle_type for angle in available_angles("robotics", story.story.validated_angles, history)})

    def test_rejected_career_angle_not_resurfaced(self) -> None:
        story = _planning_story("career-test", include_career=True)
        history = AngleHistory(rejected_angle_types={AngleType.CAREER})

        self.assertNotIn(AngleType.CAREER, {angle.angle_type for angle in available_angles("career-test", story.story.validated_angles, history)})
        self.assertIn(AngleType.CAREER, {angle.angle_type for angle in rejected_angles(story.story.validated_angles, history)})

    def test_follow_up_requires_materially_different_angle(self) -> None:
        story = _planning_story("followup")
        history = _history("followup", AngleType.NEWS)
        news = next(angle for angle in story.story.validated_angles if angle.angle_type is AngleType.NEWS)
        explainer = next(angle for angle in story.story.validated_angles if angle.angle_type is AngleType.EXPLAINER)

        self.assertFalse(materially_different_angle("followup", news, history))
        self.assertTrue(materially_different_angle("followup", explainer, history))

    def test_follow_up_potential_uses_unused_strong_angles(self) -> None:
        story = _planning_story("followup")
        history = _history("followup", AngleType.NEWS)

        self.assertIn(follow_up_potential("followup", story.story.validated_angles, history), {FollowUpPotential.MEDIUM, FollowUpPotential.HIGH})

    def test_evergreen_item_retains_story_provenance(self) -> None:
        story = _planning_story("evergreen")
        angle = story.story.validated_angles[1]

        item = evergreen_from_angle(story.story, angle, created_at=NOW)

        self.assertEqual(item.originating_story_id, "evergreen")
        self.assertEqual(item.evidence_claim_refs, angle.supporting_fact_ids)

    def test_related_stories_remain_separate(self) -> None:
        left = _planning_story("robotics-a", domain="robotics")
        right = _planning_story("robotics-b", domain="robotics")

        relationship = infer_story_relationships([left, right])[0]

        self.assertEqual({relationship.left_story_id, relationship.right_story_id}, {"robotics-a", "robotics-b"})

    def test_bundle_references_multiple_stories_without_merging_them(self) -> None:
        bundles = bundle_candidates(
            [_planning_story("robotics-a", domain="robotics"), _planning_story("robotics-b", domain="robotics")],
            infer_story_relationships([_planning_story("robotics-a", domain="robotics"), _planning_story("robotics-b", domain="robotics")]),
        )

        self.assertEqual(len(bundles[0].story_ids), 2)

    def test_unrelated_stories_do_not_bundle(self) -> None:
        stories = [_planning_story("robotics", domain="robotics"), _planning_story("healthcare", domain="healthcare")]

        self.assertEqual(bundle_candidates(stories, infer_story_relationships(stories)), [])

    def test_same_day_occurrence_alone_does_not_cause_bundling(self) -> None:
        stories = [
            _planning_story("model", domain="models", technologies=["language model"]),
            _planning_story("healthcare", domain="healthcare", technologies=["clinical triage"]),
        ]

        self.assertEqual(infer_story_relationships(stories), [])

    def test_bundle_claims_retain_originating_story_provenance(self) -> None:
        stories = [_planning_story("robotics-a", domain="robotics"), _planning_story("robotics-b", domain="robotics")]
        bundle = bundle_candidates(stories, infer_story_relationships(stories))[0]

        self.assertEqual(set(bundle.claim_refs_by_story), {"robotics-a", "robotics-b"})
        self.assertNotEqual(bundle.claim_refs_by_story["robotics-a"], bundle.claim_refs_by_story["robotics-b"])

    def test_target_three_can_return_fewer_than_three(self) -> None:
        plan = EditorialPlanner(target_posts_per_day=3).plan(
            plan_date=date(2026, 10, 3),
            now=NOW,
            stories=[_planning_story("only", score=0.88)],
        )

        self.assertEqual(len(plan.recommended_posts), 1)

    def test_planner_can_recommend_more_than_three_when_justified(self) -> None:
        stories = [_planning_story(f"breaking-{i}", score=0.95, published_at=NOW - timedelta(hours=1)) for i in range(4)]

        plan = EditorialPlanner(target_posts_per_day=3).plan(plan_date=date(2026, 10, 3), now=NOW, stories=stories)

        self.assertEqual(len(plan.recommended_posts), 4)

    def test_weak_content_not_selected_to_fill_quota(self) -> None:
        stories = [_planning_story(f"weak-{i}", score=0.2, published_at=NOW - timedelta(hours=1)) for i in range(3)]

        plan = EditorialPlanner(target_posts_per_day=3).plan(plan_date=date(2026, 10, 3), now=NOW, stories=stories)

        self.assertEqual(plan.recommended_posts, [])

    def test_quiet_day_may_use_evergreen_content(self) -> None:
        evergreen_story = _planning_story("evergreen-source")
        evergreen = evergreen_from_angle(evergreen_story.story, evergreen_story.story.validated_angles[1], created_at=NOW)

        plan = EditorialPlanner(target_posts_per_day=3).plan(
            plan_date=date(2026, 10, 3),
            now=NOW,
            stories=[_planning_story("today", score=0.84)],
            evergreen_library=[evergreen],
        )

        self.assertEqual(len(plan.recommended_posts), 2)
        self.assertEqual(plan.recommended_posts[1].urgency, EditorialUrgency.EVERGREEN)

    def test_expired_news_angle_not_selected_as_current_news(self) -> None:
        story = _planning_story("old-news", published_at=NOW - timedelta(days=10))
        plan = EditorialPlanner().plan(plan_date=date(2026, 10, 3), now=NOW, stories=[story])

        self.assertTrue(plan.expired_items)
        self.assertNotEqual(plan.recommended_posts[0].selected_angle.angle_type, AngleType.NEWS)

    def test_expired_story_may_retain_valid_explainer_angle(self) -> None:
        story = _planning_story("old-explainer", published_at=NOW - timedelta(days=10))
        plan = EditorialPlanner().plan(plan_date=date(2026, 10, 3), now=NOW, stories=[story])

        self.assertIn(AngleType.EXPLAINER, plan.expired_items[0].still_valid_angle_types)

    def test_high_value_evergreen_can_beat_low_value_breaking_story(self) -> None:
        stories = [
            _planning_story("evergreen", score=0.92, published_at=NOW - timedelta(days=30)),
            _planning_story("weak-breaking", score=0.15, published_at=NOW - timedelta(hours=1)),
        ]

        plan = EditorialPlanner(target_posts_per_day=1).plan(plan_date=date(2026, 10, 3), now=NOW, stories=stories)

        self.assertEqual(plan.recommended_posts[0].story_id, "evergreen")

    def test_diversity_is_not_a_hard_quota(self) -> None:
        stories = [_planning_story("robotics-a", domain="robotics"), _planning_story("robotics-b", domain="robotics")]

        plan = EditorialPlanner(target_posts_per_day=2).plan(plan_date=date(2026, 10, 3), now=NOW, stories=stories)

        self.assertEqual([post.story_id for post in plan.recommended_posts], ["robotics-a", "robotics-b"])

    def test_human_decision_approve_works(self) -> None:
        decision = record_human_decision(action=HumanDecisionAction.APPROVE, target_id="post-1", decided_at=NOW)

        self.assertEqual(decision.action, HumanDecisionAction.APPROVE)

    def test_human_save_works(self) -> None:
        decision = record_human_decision(action=HumanDecisionAction.SAVE, target_id="story-1", decided_at=NOW, comment="save for quiet day")

        self.assertEqual(decision.comment, "save for quiet day")

    def test_human_keep_separate_works(self) -> None:
        decision = record_human_decision(action=HumanDecisionAction.KEEP_SEPARATE, target_id="bundle-1", decided_at=NOW)

        self.assertEqual(decision.action, HumanDecisionAction.KEEP_SEPARATE)

    def test_recommendation_contains_rationale(self) -> None:
        plan = EditorialPlanner().plan(plan_date=date(2026, 10, 3), now=NOW, stories=[_planning_story("rationale")])

        self.assertGreaterEqual(len(plan.recommended_posts[0].rationale), 3)

    def test_deterministic_planner_works_without_llm(self) -> None:
        story = _planning_story("deterministic")

        first = EditorialPlanner().plan(plan_date=date(2026, 10, 3), now=NOW, stories=[story])
        second = EditorialPlanner().plan(plan_date=date(2026, 10, 3), now=NOW, stories=[story])

        self.assertEqual(first, second)


def _history(story_id: str, angle_type: AngleType) -> AngleHistory:
    return AngleHistory(
        publication_records=[
            AnglePublicationRecord(
                story_id=story_id,
                angle_type=angle_type,
                title_used="Published title",
                published_at=NOW,
                platform=TargetPlatform.INSTAGRAM,
                content_id="content-1",
            )
        ]
    )


def _planning_story(
    story_id: str,
    *,
    score: float = 0.88,
    published_at: datetime = NOW - timedelta(hours=4),
    domain: str = "robotics",
    technologies: list[str] | None = None,
    include_career: bool = False,
) -> StoryPlanningInput:
    technologies = technologies or ([domain, "vision language action"] if domain == "robotics" else [f"{domain} AI"])
    story = _verified_story(story_id, technologies=technologies, include_career=include_career, domain=domain)
    return StoryPlanningInput(
        story_id=story_id,
        story=story,
        timing=assess_timing(published_at=published_at, now=NOW),
        editorial_score=score,
        domain=domain,
    )


def _verified_story(story_id: str, *, technologies: list[str], include_career: bool, domain: str) -> VerifiedGroundedStory:
    claim = VerifiedClaimCandidate(
        f"{story_id}-claim",
        f"{story_id} uses {technologies[0]} for factory diagnostic workflows.",
        ClaimKind.FACT,
        [f"{story_id}-evidence"],
    )
    evidence_pack = EvidencePack(
        cluster_id=story_id,
        canonical_title=f"{story_id} canonical title",
        sources=[
            EvidenceSource(
                candidate_id=f"{story_id}-candidate",
                source_name="Example Source",
                source_url=f"https://example.com/{story_id}",
                source_type=SourceType.NEWS,
                evidence_role=EvidenceRole.SECONDARY,
                is_independent=True,
                source_id="source_001",
            )
        ],
        evidence_items=[
            EvidenceItem(
                evidence_id=f"{story_id}-evidence",
                cluster_id=story_id,
                source_id="source_001",
                source_url=f"https://example.com/{story_id}",
                source_type=SourceType.NEWS,
                supplied_text="Evidence text.",
                published_at=NOW,
            )
        ],
    )
    angles = [
        _angle("news", AngleType.NEWS, "What changed today", 0.83),
        _angle("technology", AngleType.TECHNOLOGY, "How the technology works", 0.82),
        _angle("explainer", AngleType.EXPLAINER, "Why this matters beyond the news", 0.80),
        _angle("workflow", AngleType.WORKFLOW_IMPACT, "How workflows may change", 0.78),
    ]
    if include_career:
        angles.append(_angle("career", AngleType.CAREER, "What professionals should learn", 0.7))
    return VerifiedGroundedStory(
        cluster_id=story_id,
        canonical_title=f"{story_id} canonical title",
        evidence_pack=evidence_pack,
        verified_claims=[claim],
        rejected_claims=[],
        analysis=VerifiedStoryAnalysis(
            development_summary="A verified AI development.",
            technologies=technologies,
            applications=[f"{domain} diagnostics"],
            industries=[domain],
            workflows=[f"{domain} workflow"],
            verified_claim_ids=[claim.claim_id],
        ),
        validated_angles=angles,
    )


def _angle(angle_id: str, angle_type: AngleType, thesis: str, score: float) -> PotentialAngle:
    return PotentialAngle(
        id=angle_id,
        angle_type=angle_type,
        thesis=thesis,
        target_audiences=[Audience.PROFESSIONAL, Audience.ENTHUSIAST],
        evidence_strength=0.85,
        relevance=0.85,
        novelty=0.7,
        usefulness=0.82,
        speculation_risk=0.15,
        supporting_fact_ids=["placeholder"],
        score=score,
    )


if __name__ == "__main__":
    unittest.main()
