from dataclasses import dataclass
from datetime import datetime

from src.editorial.demo_fixture import DEMO_NOW, busy_news_day_fixture
from src.editorial.models import AngleHistory, DailyContentPlan, EvergreenItem, StoryPlanningInput
from src.editorial.planner import EditorialPlanner
from src.intelligence.models import (
    HashtagCandidate,
    HashtagResearchStatus,
    HashtagSource,
    TargetPlatform,
    TitleCandidate,
    TitleType,
)


@dataclass(frozen=True)
class DashboardData:
    mode_label: str
    plan: DailyContentPlan
    stories: list[StoryPlanningInput]
    evergreen_items: list[EvergreenItem]
    angle_history: AngleHistory
    title_candidates_by_story: dict[str, list[TitleCandidate]]
    hashtag_candidates_by_story: dict[str, list[HashtagCandidate]]
    loaded_at: datetime


def load_demo_dashboard_data() -> DashboardData:
    stories, evergreen_items = busy_news_day_fixture()
    plan = EditorialPlanner(target_posts_per_day=3).plan(
        plan_date=DEMO_NOW.date(),
        now=DEMO_NOW,
        stories=stories,
        evergreen_library=evergreen_items,
    )
    return DashboardData(
        mode_label="DEMO DATA",
        plan=plan,
        stories=stories,
        evergreen_items=evergreen_items,
        angle_history=AngleHistory(),
        title_candidates_by_story={
            story.story_id: _titles_for_story(story)
            for story in stories
        },
        hashtag_candidates_by_story={
            story.story_id: _hashtags_for_story(story)
            for story in stories
        },
        loaded_at=DEMO_NOW,
    )


def load_live_boundary_data() -> DashboardData:
    """Expose the honest Step 7B live boundary without making network calls."""

    demo = load_demo_dashboard_data()
    return DashboardData(
        mode_label="LIVE MODE NOT WIRED",
        plan=demo.plan,
        stories=demo.stories,
        evergreen_items=demo.evergreen_items,
        angle_history=demo.angle_history,
        title_candidates_by_story=demo.title_candidates_by_story,
        hashtag_candidates_by_story=demo.hashtag_candidates_by_story,
        loaded_at=demo.loaded_at,
    )


def _titles_for_story(story: StoryPlanningInput) -> list[TitleCandidate]:
    claim_ids = [claim.claim_id for claim in story.story.verified_claims]
    return [
        TitleCandidate(
            text=story.story.canonical_title,
            title_type=TitleType.NEWS,
            supported_claim_ids=claim_ids,
            target_platform=TargetPlatform.INSTAGRAM,
            hook_strength=0.78,
            clarity=0.9,
            hype_risk=0.12,
        ),
        TitleCandidate(
            text=f"What {story.story.canonical_title} actually changes",
            title_type=TitleType.EXPLAINER,
            supported_claim_ids=claim_ids,
            target_platform=TargetPlatform.INSTAGRAM,
            hook_strength=0.72,
            clarity=0.86,
            hype_risk=0.1,
        ),
    ]


def _hashtags_for_story(story: StoryPlanningInput) -> list[HashtagCandidate]:
    terms = [*story.story.analysis.technologies[:2], *story.story.analysis.industries[:1]]
    tags = []
    for term in dict.fromkeys(terms):
        tag = "#" + "".join(ch for ch in term.title() if ch.isalnum())
        tags.append(
            HashtagCandidate(
                tag=tag,
                relevance_score=0.78,
                specificity_score=0.7,
                source=HashtagSource.VERIFIED_STORY,
                research_status=HashtagResearchStatus.UNRESEARCHED,
                platform=TargetPlatform.INSTAGRAM,
                estimated_reach_band=None,
                competition_band=None,
                supporting_topic_terms=[term],
            )
        )
    return tags
