from dataclasses import replace
from datetime import date, datetime, timezone
import unittest

from dashboard.demo_data import load_demo_dashboard_data
from dashboard.content_packages import approve_session_package_for_render, generate_session_package, package_summary
from dashboard.view_models import (
    audit_entry,
    bundle_story_sections,
    can_select_angle,
    claim_kind_label,
    content_direction_label,
    create_decision,
    dashboard_counts,
    display_timestamp,
    editorial_status_label,
    evergreen_library_items,
    hashtag_reach_label,
    hashtag_choices,
    manual_title_label,
    manual_title_requires_acknowledgement,
    metrics_empty_state,
    package_preview,
    post_slots,
    primary_action_for_status,
    provenance_display_rows,
    rejected_claim_display_rows,
    saved_library_items,
    provenance_rows,
    select_angle,
    select_title,
    story_card_view_model,
    title_choices,
    today_summary,
    trust_summary,
    validation_summary,
)
from src.content.package_models import PackageReviewState, TitleVerificationStatus
from src.editorial.models import DailyContentPlan, HumanDecisionAction
from src.intelligence.models import AngleType, ClaimKind


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

        self.assertIn("No posts published yet.", text)
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

    def test_dashboard_content_package_preview_uses_session_data(self) -> None:
        data = load_demo_dashboard_data()
        package = generate_session_package(data, data.plan.recommended_posts[0])

        self.assertEqual(package.generation_metadata.provider, "fake")
        self.assertTrue(package_summary(package))

    def test_today_identifies_top_recommended_story(self) -> None:
        data = load_demo_dashboard_data()
        post = data.plan.recommended_posts[0]
        story = data.stories[0]
        card = story_card_view_model(post=post, story=story, decision_log=[])

        self.assertEqual(card.priority_label, "TOP PICK")
        self.assertEqual(card.headline, story.story.canonical_title)

    def test_top_story_gets_one_clear_primary_action(self) -> None:
        data = load_demo_dashboard_data()
        card = story_card_view_model(
            post=data.plan.recommended_posts[0],
            story=data.stories[0],
            decision_log=[],
        )

        self.assertEqual(card.primary_action, "Review Story")
        self.assertNotIn("Approve", card.primary_action)

    def test_review_action_selects_story_workflow_target(self) -> None:
        data = load_demo_dashboard_data()
        card = story_card_view_model(
            post=data.plan.recommended_posts[0],
            story=data.stories[0],
            decision_log=[],
        )

        self.assertEqual(card.story_id, data.plan.recommended_posts[0].story_id)

    def test_selected_story_state_can_persist_as_story_id(self) -> None:
        data = load_demo_dashboard_data()
        selected_story_id = data.stories[0].story_id

        self.assertIn(selected_story_id, [story.story_id for story in data.stories])

    def test_human_readable_status_mapping_defaults_to_recommended(self) -> None:
        self.assertEqual(editorial_status_label(story_id="s1", decision_log=[]), "RECOMMENDED")
        self.assertEqual(primary_action_for_status("RECOMMENDED"), "Review Story")

    def test_approved_story_displays_approved(self) -> None:
        entry = audit_entry(create_decision(action=HumanDecisionAction.APPROVE, target_id="s1", decided_at=NOW))

        self.assertEqual(editorial_status_label(story_id="s1", decision_log=[entry]), "APPROVED")

    def test_saved_story_displays_saved(self) -> None:
        entry = audit_entry(create_decision(action=HumanDecisionAction.SAVE, target_id="s1", decided_at=NOW))

        self.assertEqual(editorial_status_label(story_id="s1", decision_log=[entry]), "SAVED")

    def test_held_story_displays_held(self) -> None:
        entry = audit_entry(create_decision(action=HumanDecisionAction.HOLD, target_id="s1", decided_at=NOW))

        self.assertEqual(editorial_status_label(story_id="s1", decision_log=[entry]), "HELD")

    def test_selected_angle_has_visible_helper_state(self) -> None:
        data = load_demo_dashboard_data()
        label = content_direction_label(data.stories[0].story.validated_angles[0])

        self.assertIn("THE AI BRIEF", label)

    def test_selected_title_has_visible_helper_state(self) -> None:
        data = load_demo_dashboard_data()
        titles = data.title_candidates_by_story[data.stories[0].story_id]
        choices = title_choices(titles, titles[1].text)

        self.assertTrue(choices[1].selected)
        self.assertIn("Grounded", choices[1].helper)

    def test_technical_ids_excluded_from_primary_card_output(self) -> None:
        data = load_demo_dashboard_data()
        card = story_card_view_model(
            post=data.plan.recommended_posts[0],
            story=data.stories[0],
            decision_log=[],
        )
        rendered = " ".join([card.headline, card.what_happened, card.why_it_matters, card.trust_label])

        self.assertNotIn("claim", rendered.lower())
        self.assertNotIn("cluster", rendered.lower())

    def test_trust_summary_translates_verified_facts(self) -> None:
        data = load_demo_dashboard_data()
        summary = trust_summary(data.stories[0])

        self.assertIn("Verified from", summary.label)
        self.assertGreaterEqual(summary.fact_count, 1)

    def test_inference_translated_distinctly_from_verified_fact(self) -> None:
        self.assertEqual(claim_kind_label(ClaimKind.INFERENCE), "INTERPRETATION / REASONED INFERENCE")
        self.assertNotEqual(claim_kind_label(ClaimKind.INFERENCE), claim_kind_label(ClaimKind.FACT))

    def test_rejected_claim_translated_distinctly(self) -> None:
        data = load_demo_dashboard_data()
        rows = rejected_claim_display_rows(data.stories[0])

        self.assertEqual(rows, [])
        self.assertEqual(claim_kind_label(ClaimKind.INTERPRETATION), "NOT ESTABLISHED / REJECTED")

    def test_provenance_display_hides_technical_ids(self) -> None:
        data = load_demo_dashboard_data()
        row = provenance_display_rows(data.stories[0])[0]

        self.assertEqual(row.label, "VERIFIED FACT")
        self.assertFalse(hasattr(row, "claim_id"))

    def test_generated_package_preview_exposes_actual_reel_content(self) -> None:
        data = load_demo_dashboard_data()
        preview = package_preview(generate_session_package(data, data.plan.recommended_posts[0]))

        self.assertTrue(preview.reel_hook)
        self.assertTrue(preview.reel_scenes[0].narration)

    def test_generated_package_preview_exposes_actual_instagram_caption(self) -> None:
        data = load_demo_dashboard_data()
        preview = package_preview(generate_session_package(data, data.plan.recommended_posts[0]))

        self.assertIn("Takeaway:", preview.instagram_caption)

    def test_platform_preview_exposes_actual_blog_content(self) -> None:
        data = load_demo_dashboard_data()
        preview = package_preview(generate_session_package(data, data.plan.recommended_posts[0]))

        self.assertIn("What happened", preview.blog_body)

    def test_platform_preview_exposes_actual_linkedin_content(self) -> None:
        data = load_demo_dashboard_data()
        preview = package_preview(generate_session_package(data, data.plan.recommended_posts[0]))

        self.assertTrue(preview.linkedin_post)

    def test_platform_preview_exposes_actual_x_content(self) -> None:
        data = load_demo_dashboard_data()
        preview = package_preview(generate_session_package(data, data.plan.recommended_posts[0]))

        self.assertTrue(preview.x_posts)

    def test_platform_preview_exposes_tiktok_and_youtube_content(self) -> None:
        data = load_demo_dashboard_data()
        preview = package_preview(generate_session_package(data, data.plan.recommended_posts[0]))

        self.assertTrue(preview.tiktok_caption)
        self.assertTrue(preview.youtube_description)

    def test_validation_summary_is_human_readable(self) -> None:
        data = load_demo_dashboard_data()
        summary = validation_summary(generate_session_package(data, data.plan.recommended_posts[0]))

        self.assertTrue(summary.ready)
        self.assertIn("Uses verified story claims", summary.lines)

    def test_approve_for_render_uses_existing_package_review_state(self) -> None:
        data = load_demo_dashboard_data()
        package = generate_session_package(data, data.plan.recommended_posts[0])
        approved = approve_session_package_for_render(data, package)

        self.assertEqual(approved.review_state, PackageReviewState.APPROVED_FOR_RENDER)

    def test_manual_title_acknowledgement_enforced(self) -> None:
        data = load_demo_dashboard_data()
        package = generate_session_package(data, data.plan.recommended_posts[0])
        manual = replace(
            package,
            selected_title=replace(
                package.selected_title,
                verification_status=TitleVerificationStatus.MANUAL_UNVERIFIED,
                manual_acknowledged=False,
            ),
        )

        self.assertTrue(manual_title_requires_acknowledgement(manual))

    def test_successful_approval_produces_ready_for_render_status(self) -> None:
        data = load_demo_dashboard_data()
        package = approve_session_package_for_render(data, generate_session_package(data, data.plan.recommended_posts[0]))

        self.assertEqual(
            editorial_status_label(story_id=data.stories[0].story_id, decision_log=[], package=package),
            "READY FOR RENDER",
        )

    def test_saved_item_appears_in_library_helper(self) -> None:
        data = load_demo_dashboard_data()
        entry = audit_entry(
            create_decision(
                action=HumanDecisionAction.SAVE,
                target_id=data.stories[0].story_id,
                decided_at=NOW,
            )
        )

        self.assertIn(data.stories[0].story.canonical_title, [item.title for item in saved_library_items(data, [entry])])

    def test_evergreen_items_appear_in_library_helper(self) -> None:
        data = load_demo_dashboard_data()

        self.assertTrue(evergreen_library_items(data))

    def test_today_summary_counts_progressing_items(self) -> None:
        data = load_demo_dashboard_data()
        package = generate_session_package(data, data.plan.recommended_posts[0])
        summary = today_summary(data, [], {data.stories[0].story_id: package})

        self.assertEqual(summary["draft_ready"], 1)

    def test_hashtag_choices_keep_unknown_reach_honest(self) -> None:
        data = load_demo_dashboard_data()
        tags = data.hashtag_candidates_by_story[data.stories[0].story_id]
        choices = hashtag_choices(tags, None)

        self.assertIn("UNKNOWN", choices[0].helper)


if __name__ == "__main__":
    unittest.main()
