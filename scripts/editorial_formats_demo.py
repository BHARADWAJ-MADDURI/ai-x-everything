from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.editorial.demo_fixture import DEMO_NOW, busy_news_day_fixture
from src.editorial.formats import (
    EditorialFormat,
    build_ai_brief_package,
    build_deep_dive_package,
    build_learn_package,
    recommend_formats,
    select_ai_brief_candidates,
)


def main() -> None:
    stories, evergreen_items = busy_news_day_fixture()
    recommendations = recommend_formats(stories=stories, evergreen_items=evergreen_items)
    brief_selection = select_ai_brief_candidates(stories)
    brief = build_ai_brief_package(
        brief_id="demo-brief",
        package_date=DEMO_NOW.date(),
        stories=brief_selection.selected,
    )
    deep_story = brief_selection.selected[0]
    deep_dive = build_deep_dive_package(
        story=deep_story,
        selected_angle=deep_story.story.validated_angles[1],
    )
    learn = build_learn_package(
        topic=evergreen_items[0].proposed_thesis,
        evergreen_item=evergreen_items[0],
    )

    print("EVERYTHING × AI")
    print("EDITORIAL FORMATS")
    print()
    print("TODAY")
    print("-----")
    print()
    print(f"Verified stories: {len(stories)}")
    print()
    print("RECOMMENDED:")
    print()
    for recommendation in recommendations:
        print(_format_name(recommendation.editorial_format))
        print(recommendation.reason)
        print()
    print(brief.title.upper())
    print(brief.subtitle)
    print()
    for item in brief.items:
        print(f"{item.position}. {item.headline}")
        print(f"   {item.category} | {item.what_happened}")
    print()
    print("DEEP DIVE")
    print(f"Story: {deep_dive.headline}")
    print(f"Why: {deep_dive.selected_angle.thesis}")
    print()
    print("LEARN")
    print(f"Topic: {learn.topic}")
    print("Why: Grounded evergreen material is available.")
    print()
    print("AI BRIEF VALIDATION")
    print("-------------------")
    print(f"Stories isolated: {'YES' if brief.validation.ready else 'NO'}")
    print(f"Claims valid: {'YES' if brief.validation.ready else 'NO'}")
    print(f"Sources valid: {'YES' if brief.validation.ready else 'NO'}")
    print(f"Ready for editor review: {'YES' if brief.validation.ready else 'NO'}")


def _format_name(editorial_format: EditorialFormat) -> str:
    return {
        EditorialFormat.AI_BRIEF: "AI Brief",
        EditorialFormat.DEEP_DIVE: "Deep Dive",
        EditorialFormat.LEARN: "Learn",
    }[editorial_format]


if __name__ == "__main__":
    main()
