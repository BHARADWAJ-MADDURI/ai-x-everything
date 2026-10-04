from dataclasses import replace
from datetime import timedelta
import unittest

from src.content.package_models import PackageReviewState
from src.editorial.demo_fixture import DEMO_NOW, _planning_story, busy_news_day_fixture
from src.editorial.formats import (
    MAX_BRIEF_ITEMS,
    AIBriefItem,
    EditorialFormat,
    build_ai_brief_package,
    build_deep_dive_package,
    build_learn_package,
    recommend_formats,
    select_ai_brief_candidates,
    validate_ai_brief_package,
)
from src.intelligence.models import AngleType


class EditorialFormatTests(unittest.TestCase):
    def test_editorial_format_supports_ai_brief(self) -> None:
        self.assertEqual(EditorialFormat.AI_BRIEF.value, "ai_brief")

    def test_editorial_format_supports_deep_dive(self) -> None:
        self.assertEqual(EditorialFormat.DEEP_DIVE.value, "deep_dive")

    def test_editorial_format_supports_learn(self) -> None:
        self.assertEqual(EditorialFormat.LEARN.value, "learn")

    def test_brief_accepts_three_valid_stories(self) -> None:
        package = build_ai_brief_package(brief_id="brief-1", package_date=DEMO_NOW.date(), stories=_stories(3))

        self.assertTrue(package.validation.ready)
        self.assertEqual(package.item_count, 3)

    def test_brief_accepts_ten_valid_stories(self) -> None:
        package = build_ai_brief_package(brief_id="brief-1", package_date=DEMO_NOW.date(), stories=_stories(10))

        self.assertTrue(package.validation.ready)
        self.assertEqual(package.item_count, 10)

    def test_brief_rejects_fewer_than_three(self) -> None:
        package = build_ai_brief_package(brief_id="brief-1", package_date=DEMO_NOW.date(), stories=_stories(2))

        self.assertFalse(package.validation.ready)
        self.assertIn("3-10", package.validation.issues[0])

    def test_brief_rejects_more_than_ten(self) -> None:
        package = build_ai_brief_package(brief_id="brief-1", package_date=DEMO_NOW.date(), stories=_stories(11))

        self.assertFalse(package.validation.ready)
        self.assertIn("3-10", package.validation.issues[0])

    def test_brief_does_not_force_count_to_ten(self) -> None:
        package = build_ai_brief_package(brief_id="brief-1", package_date=DEMO_NOW.date(), stories=_stories(4))

        self.assertTrue(package.validation.ready)
        self.assertEqual(package.item_count, 4)

    def test_brief_preserves_ordering(self) -> None:
        stories = _stories(4)
        package = build_ai_brief_package(brief_id="brief-1", package_date=DEMO_NOW.date(), stories=stories)

        self.assertEqual([item.story_id for item in package.items], [story.story_id for story in stories])

    def test_brief_rejects_duplicate_story(self) -> None:
        stories = _stories(3)
        package = build_ai_brief_package(
            brief_id="brief-1",
            package_date=DEMO_NOW.date(),
            stories=[stories[0], stories[1], stories[0]],
        )

        self.assertFalse(package.validation.ready)
        self.assertTrue(any("duplicate story" in issue for issue in package.validation.issues))

    def test_brief_item_references_one_story(self) -> None:
        package = build_ai_brief_package(brief_id="brief-1", package_date=DEMO_NOW.date(), stories=_stories(3))

        self.assertEqual(package.items[0].story_id, package.items[0].cluster_id)

    def test_brief_item_claim_refs_valid(self) -> None:
        stories = _stories(3)
        package = build_ai_brief_package(brief_id="brief-1", package_date=DEMO_NOW.date(), stories=stories)

        self.assertIn(package.items[0].supporting_claim_ids[0], [claim.claim_id for claim in stories[0].story.verified_claims])

    def test_brief_item_source_refs_valid(self) -> None:
        stories = _stories(3)
        package = build_ai_brief_package(brief_id="brief-1", package_date=DEMO_NOW.date(), stories=stories)

        self.assertEqual(package.items[0].source_refs[0].source_url, stories[0].story.evidence_pack.sources[0].source_url)

    def test_cross_story_claim_leakage_rejected(self) -> None:
        stories = _stories(3)
        package = build_ai_brief_package(brief_id="brief-1", package_date=DEMO_NOW.date(), stories=stories)
        bad_item = replace(package.items[0], supporting_claim_ids=[stories[1].story.verified_claims[0].claim_id])
        bad_package = replace(package, items=[bad_item, *package.items[1:]])
        validation = validate_ai_brief_package(bad_package, stories)

        self.assertFalse(validation.ready)
        self.assertTrue(any("claim" in issue for issue in validation.issues))

    def test_cross_story_evidence_leakage_rejected(self) -> None:
        stories = _stories(3)
        package = build_ai_brief_package(brief_id="brief-1", package_date=DEMO_NOW.date(), stories=stories)
        bad_item = replace(package.items[0], evidence_reference_ids=[stories[1].story.evidence_pack.evidence_items[0].evidence_id])
        bad_package = replace(package, items=[bad_item, *package.items[1:]])
        validation = validate_ai_brief_package(bad_package, stories)

        self.assertFalse(validation.ready)
        self.assertTrue(any("evidence" in issue for issue in validation.issues))

    def test_unsupported_numeric_claim_rejected(self) -> None:
        stories = _stories(3)
        package = build_ai_brief_package(brief_id="brief-1", package_date=DEMO_NOW.date(), stories=stories)
        bad_item = replace(package.items[0], what_happened="This changed by 42%.")
        bad_package = replace(package, items=[bad_item, *package.items[1:]])
        validation = validate_ai_brief_package(bad_package, stories)

        self.assertFalse(validation.ready)
        self.assertTrue(any("unsupported numeric" in issue for issue in validation.issues))

    def test_supported_numeric_claim_accepted(self) -> None:
        stories = _stories(3)
        claim = stories[0].story.verified_claims[0]
        numeric_claim = replace(claim, text=f"{claim.text} It changed by 42%.")
        numeric_story = replace(stories[0], story=replace(stories[0].story, verified_claims=[numeric_claim]))
        package = build_ai_brief_package(brief_id="brief-1", package_date=DEMO_NOW.date(), stories=[numeric_story, *stories[1:]])
        item = replace(package.items[0], what_happened="It changed by 42%.")
        validation = validate_ai_brief_package(replace(package, items=[item, *package.items[1:]]), [numeric_story, *stories[1:]])

        self.assertTrue(validation.ready)

    def test_title_reflects_actual_item_count(self) -> None:
        package = build_ai_brief_package(brief_id="brief-1", package_date=DEMO_NOW.date(), stories=_stories(7))

        self.assertIn("7 AI developments", package.subtitle)

    def test_low_quality_story_not_added_merely_to_fill_count(self) -> None:
        good = _stories(2)
        weak = replace(_stories(1)[0], story_id="weak", editorial_score=0.1)
        selection = select_ai_brief_candidates([*good, weak])

        self.assertEqual(len(selection.selected), 2)
        self.assertIn(weak, selection.ineligible)

    def test_overflow_above_ten_remains_outside_brief(self) -> None:
        selection = select_ai_brief_candidates(_stories(12))

        self.assertEqual(len(selection.selected), MAX_BRIEF_ITEMS)
        self.assertEqual(len(selection.overflow), 2)

    def test_deep_dive_uses_one_story(self) -> None:
        story = _stories(1)[0]
        package = build_deep_dive_package(story=story, selected_angle=story.story.validated_angles[1])

        self.assertTrue(package.validation.ready)
        self.assertEqual(package.story_id, story.story_id)

    def test_deep_dive_preserves_selected_grounded_angle(self) -> None:
        story = _stories(1)[0]
        angle = story.story.validated_angles[1]
        package = build_deep_dive_package(story=story, selected_angle=angle)

        self.assertEqual(package.selected_angle, angle)

    def test_deep_dive_career_content_not_forced(self) -> None:
        story = _stories(1)[0]
        package = build_deep_dive_package(story=story, selected_angle=story.story.validated_angles[1])

        self.assertNotIn("career advice", " ".join(package.sections.values()).lower())

    def test_learn_requires_grounding(self) -> None:
        package = build_learn_package(topic="What is RAG?")

        self.assertFalse(package.validation.ready)

    def test_learn_cannot_rely_on_arbitrary_model_memory(self) -> None:
        package = build_learn_package(topic="A model-memory-only concept")

        self.assertIn("grounding", " ".join(package.validation.issues))

    def test_format_recommendation_remains_human_overridable(self) -> None:
        stories, evergreen = busy_news_day_fixture()
        recommendations = recommend_formats(stories=stories, evergreen_items=evergreen)

        self.assertTrue(recommendations)
        self.assertTrue(all(item.requires_human_approval for item in recommendations))
        self.assertTrue(all(item.override_allowed for item in recommendations))

    def test_recommendation_includes_all_three_formats_when_available(self) -> None:
        stories, evergreen = busy_news_day_fixture()
        recommendations = recommend_formats(stories=stories, evergreen_items=evergreen)
        formats = {item.editorial_format for item in recommendations}

        self.assertIn(EditorialFormat.AI_BRIEF, formats)
        self.assertIn(EditorialFormat.DEEP_DIVE, formats)
        self.assertIn(EditorialFormat.LEARN, formats)

    def test_format_tests_make_zero_network_calls(self) -> None:
        stories, evergreen = busy_news_day_fixture()

        self.assertTrue(recommend_formats(stories=stories, evergreen_items=evergreen))


def _stories(count: int):
    domains = ["models", "robotics", "healthcare", "research", "agents", "chips", "education", "science", "tools", "policy", "energy", "creative"]
    return [
        _planning_story(
            f"story-{index}",
            f"AI development {index}",
            domains[index % len(domains)],
            0.95 - (index * 0.01),
            DEMO_NOW - timedelta(hours=index + 1),
        )
        for index in range(count)
    ]


if __name__ == "__main__":
    unittest.main()
