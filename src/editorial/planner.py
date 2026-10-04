from datetime import date, datetime

from src.editorial.evergreen import evergreen_from_angle
from src.editorial.history import available_angles, materially_different_angle
from src.editorial.models import (
    AngleHistory,
    DailyContentPlan,
    EditorialUrgency,
    EvergreenItem,
    EvergreenStatus,
    ExpiredItem,
    HeldItem,
    RecommendedPost,
    RecommendationStatus,
    StoryPlanningInput,
)
from src.editorial.relationships import bundle_candidates, infer_story_relationships
from src.editorial.timing import is_angle_expired
from src.intelligence.models import AngleType, PotentialAngle


MIN_RECOMMENDATION_SCORE = 0.7
STRONG_TIME_SENSITIVE_SCORE = 0.82


class EditorialPlanner:
    """Deterministic planner for today's human editorial decision."""

    def __init__(self, *, target_posts_per_day: int = 3) -> None:
        self.target_posts_per_day = target_posts_per_day

    def plan(
        self,
        *,
        plan_date: date,
        now: datetime,
        stories: list[StoryPlanningInput],
        angle_history: AngleHistory | None = None,
        evergreen_library: list[EvergreenItem] | None = None,
    ) -> DailyContentPlan:
        history = angle_history or AngleHistory()
        evergreen_items = evergreen_library or []
        relationships = infer_story_relationships(stories)
        bundles = bundle_candidates(stories, relationships)
        recommended: list[RecommendedPost] = []
        held: list[HeldItem] = []
        expired: list[ExpiredItem] = []
        saved: list[RecommendedPost] = []

        for story_input in stories:
            valid_angles = available_angles(story_input.story_id, story_input.story.validated_angles, history)
            expired_news = [
                angle.angle_type
                for angle in valid_angles
                if angle.angle_type is AngleType.NEWS and is_angle_expired(story_input.timing, True, now)
            ]
            selectable = [
                angle
                for angle in valid_angles
                if angle.angle_type is not AngleType.NEWS or angle.angle_type not in expired_news
            ]
            if expired_news:
                expired.append(
                    ExpiredItem(
                        story_id=story_input.story_id,
                        expired_angle_types=expired_news,
                        still_valid_angle_types=[angle.angle_type for angle in selectable],
                        reason="News angle is past its publish-by window; non-news angles may remain useful.",
                    )
                )
            best_angle = _best_angle(story_input.story_id, selectable, history)
            if best_angle is None:
                held.append(HeldItem(story_id=story_input.story_id, reason="No available materially different angle."))
                continue
            priority = _priority(story_input, best_angle)
            post = _recommended_post(story_input, best_angle, priority)
            if priority >= MIN_RECOMMENDATION_SCORE:
                recommended.append(post)
            else:
                held.append(HeldItem(story_id=story_input.story_id, reason="Below editorial threshold."))

        recommended.sort(key=lambda post: post.priority, reverse=True)
        publish_now = _select_publish_now(recommended, self.target_posts_per_day)
        overflow = [post for post in recommended if post not in publish_now]
        saved.extend(overflow)

        if len(publish_now) < self.target_posts_per_day:
            for evergreen in _usable_evergreen(evergreen_items, now):
                if len(publish_now) >= self.target_posts_per_day:
                    break
                publish_now.append(_evergreen_post(evergreen))

        summary = (
            f"{len(publish_now)} recommended, {len(saved)} saved, "
            f"{len(bundles)} bundle candidates, {len(expired)} expired angle records."
        )
        return DailyContentPlan(
            plan_date=plan_date,
            recommended_posts=publish_now,
            saved_for_later=saved,
            bundle_candidates=bundles,
            held_items=held,
            expired_items=expired,
            planner_summary=summary,
        )


def _select_publish_now(posts: list[RecommendedPost], target: int) -> list[RecommendedPost]:
    selected = posts[:target]
    for post in posts[target:]:
        if post.urgency is EditorialUrgency.BREAKING and post.priority >= STRONG_TIME_SENSITIVE_SCORE:
            selected.append(post)
    return selected


def _best_angle(
    story_id: str,
    angles: list[PotentialAngle],
    history: AngleHistory,
) -> PotentialAngle | None:
    candidates = [
        angle
        for angle in angles
        if materially_different_angle(story_id, angle, history)
    ]
    if not candidates:
        return None
    return max(candidates, key=_angle_score)


def _priority(story_input: StoryPlanningInput, angle: PotentialAngle) -> float:
    timing_bonus = {
        EditorialUrgency.BREAKING: 0.14,
        EditorialUrgency.CURRENT: 0.08,
        EditorialUrgency.EVERGREEN: 0.04,
    }[story_input.timing.urgency]
    score = (
        story_input.editorial_score * 0.52
        + _angle_score(angle) * 0.32
        + story_input.timing.freshness_score * 0.12
        + timing_bonus
    )
    return round(min(1.0, score), 3)


def _recommended_post(
    story_input: StoryPlanningInput,
    angle: PotentialAngle,
    priority: float,
) -> RecommendedPost:
    publish_window = story_input.timing.publish_by.isoformat() if story_input.timing.publish_by else None
    return RecommendedPost(
        story_id=story_input.story_id,
        bundle_id=None,
        selected_angle=angle,
        priority=priority,
        urgency=story_input.timing.urgency,
        recommended_publish_window=publish_window,
        rationale=[
            f"editorial score {story_input.editorial_score:.2f}",
            f"angle score {_angle_score(angle):.2f}",
            story_input.timing.timing_rationale,
            "no prior identical angle publication",
        ],
        audience=list(angle.target_audiences),
    )


def _evergreen_post(item: EvergreenItem) -> RecommendedPost:
    return RecommendedPost(
        story_id=item.originating_story_id,
        bundle_id=None,
        selected_angle=item,
        priority=0.68,
        urgency=EditorialUrgency.EVERGREEN,
        recommended_publish_window=None,
        rationale=[
            "quiet-day evergreen option",
            "retains provenance to original verified story",
        ],
        audience=list(item.audience),
        status=RecommendationStatus.RECOMMENDED,
    )


def _usable_evergreen(items: list[EvergreenItem], now: datetime) -> list[EvergreenItem]:
    usable = [
        item
        for item in items
        if item.status is EvergreenStatus.AVAILABLE and (item.expires_at is None or item.expires_at > now)
    ]
    return sorted(usable, key=lambda item: item.created_at)


def _angle_score(angle: PotentialAngle) -> float:
    if angle.score is not None:
        return angle.score
    return round(
        angle.evidence_strength * 0.35
        + angle.relevance * 0.25
        + angle.usefulness * 0.25
        + angle.novelty * 0.15
        - angle.speculation_risk * 0.2,
        3,
    )
