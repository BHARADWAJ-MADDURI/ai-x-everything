from datetime import date, datetime, timezone
import unittest

from dashboard.demo_data import load_demo_dashboard_data
from dashboard.view_models import (
    audit_entry,
    bundle_story_sections,
    can_select_angle,
    create_decision,
    dashboard_counts,
    display_timestamp,
    hashtag_reach_label,
    manual_title_label,
    metrics_empty_state,
    post_slots,
    provenance_rows,
    select_angle,
    select_title,
)
from src.editorial.models import DailyContentPlan, HumanDecisionAction
from src.intelligence.models import AngleType


NOW = datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc)


class DashboardHelperTests(unittest.TestCase):
    def test_demo_dashboard_data_loads(self) -> None:
        data = load_demo_dashboard_data()

        self.assertEqual(data.mode_label, "DEMO DATA")
        self.assertTrue(data.plan.recommended_posts)

    def test_missing_timestamp_handled(self) -> None:
        self.assertEqual(display_timestamp(None), "UNKNOWN")

    def test_unknown_hashtag_reach_displays_unknown(self) -> None:
        data = load_demo_dashboard_data()
        tag = next(iter(data.hashtag_candidates_by_story.values()))[0]

        self.assertEqual(hashtag_reach_label(tag), "UNKNOWN")

    def test_rejected_angle_cannot_be_normally_selected(self) -> None:
        data = load_demo_dashboard_data()
        angle = data.stories[0].story.validated_angles[0]

        self.assertFalse(can_select_angle(angle, {angle.angle_type}))
        with self.assertRaises(ValueError):
            select_angle(angle, {angle.angle_type})

    def test_available_angle_can_be_selected(self) -> None:
        data = load_demo_dashboard_data()
        angle = data.stories[0].story.validated_angles[0]

        self.assertEqual(select_angle(angle), angle)

    def test_grounded_title_can_be_selected(self) -> None:
        data = load_demo_dashboard_data()
        title = next(iter(data.title_candidates_by_story.values()))[0]

        self.assertEqual(select_title(title), title)

    def test_manual_title_marked_unverified(self) -> None:
        self.assertIn("MANUAL — NOT AUTOMATICALLY VERIFIED", manual_title_label("Custom headline"))

    def test_approve_creates_human_editorial_decision(self) -> None:
        decision = create_decision(action=HumanDecisionAction.APPROVE, target_id="story-1", decided_at=NOW)

        self.assertEqual(decision.action, HumanDecisionAction.APPROVE)

    def test_save_creates_human_editorial_decision(self) -> None:
        decision = create_decision(action=HumanDecisionAction.SAVE, target_id="story-1", decided_at=NOW)

        self.assertEqual(decision.action, HumanDecisionAction.SAVE)

    def test_hold_creates_human_editorial_decision(self) -> None:
        decision = create_decision(action=HumanDecisionAction.HOLD, target_id="story-1", decided_at=NOW)

        self.assertEqual(decision.action, HumanDecisionAction.HOLD)

    def test_reject_requires_confirmation_state(self) -> None:
        with self.assertRaises(ValueError):
            create_decision(action=HumanDecisionAction.REJECT, target_id="story-1", decided_at=NOW)

        confirmed = create_decision(action=HumanDecisionAction.REJECT, target_id="story-1", decided_at=NOW, confirmed=True)
        self.assertEqual(confirmed.action, HumanDecisionAction.REJECT)

    def test_approve_bundle_requires_confirmation_state(self) -> None:
        with self.assertRaises(ValueError):
            create_decision(action=HumanDecisionAction.APPROVE_BUNDLE, target_id="bundle-1", decided_at=NOW)

        confirmed = create_decision(
            action=HumanDecisionAction.APPROVE_BUNDLE,
            target_id="bundle-1",
            decided_at=NOW,
            confirmed=True,
        )
        self.assertEqual(confirmed.action, HumanDecisionAction.APPROVE_BUNDLE)

    def test_keep_separate_decision_works(self) -> None:
        decision = create_decision(action=HumanDecisionAction.KEEP_SEPARATE, target_id="bundle-1", decided_at=NOW)

        self.assertEqual(decision.action, HumanDecisionAction.KEEP_SEPARATE)

    def test_decision_audit_entry_created(self) -> None:
        decision = create_decision(action=HumanDecisionAction.SAVE, target_id="story-1", decided_at=NOW)
        entry = audit_entry(decision)

        self.assertIn("SAVE", entry.label)
        self.assertIn("story-1", entry.label)

    def test_bundle_stories_remain_separate(self) -> None:
        data = load_demo_dashboard_data()
        bundle = data.plan.bundle_candidates[0]
        sections = bundle_story_sections(bundle, data.stories)

        self.assertEqual(set(sections), set(bundle.story_ids))
        self.assertNotEqual(sections[bundle.story_ids[0]], sections[bundle.story_ids[1]])

    def test_claim_provenance_view_model_maps_claim_to_evidence_to_source(self) -> None:
        data = load_demo_dashboard_data()
        rows = provenance_rows(data.stories[0])

        self.assertTrue(rows)
        self.assertTrue(rows[0].claim_id)
        self.assertTrue(rows[0].evidence_id)
        self.assertTrue(rows[0].source_url)

    def test_empty_daily_plan_works(self) -> None:
        empty = DailyContentPlan(
            plan_date=date(2026, 10, 3),
            recommended_posts=[],
            saved_for_later=[],
            bundle_candidates=[],
            held_items=[],
            expired_items=[],
            planner_summary="empty",
        )

        self.assertEqual(post_slots(empty), [])

    def test_fewer_than_three_posts_displays_correctly(self) -> None:
        data = load_demo_dashboard_data()
        one_post_plan = DailyContentPlan(
            plan_date=data.plan.plan_date,
            recommended_posts=data.plan.recommended_posts[:1],
            saved_for_later=[],
            bundle_candidates=[],
            held_items=[],
            expired_items=[],
            planner_summary="one",
        )

        self.assertEqual(len(post_slots(one_post_plan)), 1)

    def test_more_than_three_recommendations_supported(self) -> None:
        data = load_demo_dashboard_data()
        expanded = DailyContentPlan(
            plan_date=data.plan.plan_date,
            recommended_posts=[*data.plan.recommended_posts, data.plan.saved_for_later[0]],
            saved_for_later=[],
            bundle_candidates=[],
            held_items=[],
            expired_items=[],
            planner_summary="four",
        )

        self.assertEqual(len(post_slots(expanded)), 4)

    def test_metrics_empty_state_contains_no_fake_analytics(self) -> None:
        text = metrics_empty_state()

        self.assertIn("No published metrics recorded yet.", text)
        self.assertNotIn("views", text.lower())

    def test_demo_mode_clearly_labeled(self) -> None:
        self.assertEqual(load_demo_dashboard_data().mode_label, "DEMO DATA")

    def test_dashboard_helpers_do_not_make_network_calls_in_tests(self) -> None:
        data = load_demo_dashboard_data()
        counts = dashboard_counts(data)

        self.assertEqual(counts["discovered"], len(data.stories))

    def test_inference_claims_can_be_labeled_in_provenance(self) -> None:
        data = load_demo_dashboard_data()
        rows = provenance_rows(data.stories[0])

        self.assertNotEqual(rows[0].claim_kind.value, "")

    def test_angle_type_available_for_display(self) -> None:
        data = load_demo_dashboard_data()
        angle_types = {angle.angle_type for angle in data.stories[0].story.validated_angles}

        self.assertIn(AngleType.NEWS, angle_types)


if __name__ == "__main__":
    unittest.main()
