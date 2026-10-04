import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.editorial.demo_fixture import DEMO_NOW, busy_news_day_fixture
from src.editorial.planner import EditorialPlanner


def main() -> None:
    stories, evergreen_library = busy_news_day_fixture()
    plan = EditorialPlanner(target_posts_per_day=3).plan(
        plan_date=DEMO_NOW.date(),
        now=DEMO_NOW,
        stories=stories,
        evergreen_library=evergreen_library,
    )

    print("EVERYTHING × AI")
    print("DAILY EDITORIAL PLAN")
    print("Understand what's changing.")
    print()
    print("SUMMARY")
    print("-------")
    print(f"Candidates: {len(stories)}")
    print(f"Recommended: {len(plan.recommended_posts)}")
    print(f"Saved: {len(plan.saved_for_later)}")
    print(f"Bundles: {len(plan.bundle_candidates)}")
    print(f"Expired: {len(plan.expired_items)}")
    print(plan.planner_summary)
    print()

    for index, post in enumerate(plan.recommended_posts, start=1):
        angle = post.selected_angle
        print(f"POST {index} — PUBLISH NOW")
        print(f"Story: {post.story_id}")
        print(f"Angle: {angle.angle_type.value}")
        print(f"Urgency: {post.urgency.value}")
        print(f"Score: {post.priority:.3f}")
        print(f"Publish by: {post.recommended_publish_window or 'not time-bound'}")
        print(f"Audience: {', '.join(audience.value for audience in post.audience)}")
        print("Why:")
        for reason in post.rationale:
            print(f"- {reason}")
        print()

    for bundle in plan.bundle_candidates:
        print("BUNDLE OPPORTUNITY")
        print("------------------")
        print(f"Stories: {', '.join(bundle.story_ids)}")
        print(f"Thesis: {bundle.proposed_thesis}")
        print(f"Coherence: {bundle.coherence_score:.3f}")
        print(f"Recommendation: {bundle.rationale}")
        print()

    for post in plan.saved_for_later:
        angle = post.selected_angle
        print("SAVE FOR LATER")
        print("--------------")
        print(f"Story: {post.story_id}")
        print(f"Angle: {angle.angle_type.value}")
        print(f"Shelf life: {post.urgency.value}")
        print(f"Reason: priority {post.priority:.3f} after stronger publish-now items")
        print()

    print("EVERGREEN LIBRARY")
    print("-----------------")
    for item in evergreen_library:
        print(f"Story: {item.originating_story_id}")
        print(f"Angle: {item.angle_type.value}")
        print(f"Thesis: {item.proposed_thesis}")
        print()

    for expired in plan.expired_items:
        print("EXPIRED")
        print("-------")
        print(f"Story: {expired.story_id}")
        print(f"Expired angle: {', '.join(angle.value for angle in expired.expired_angle_types)}")
        print(f"Still-valid angles: {', '.join(angle.value for angle in expired.still_valid_angle_types)}")
        print()


if __name__ == "__main__":
    main()
