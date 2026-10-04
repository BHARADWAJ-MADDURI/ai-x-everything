from datetime import datetime, timedelta, timezone

from src.editorial.models import EditorialTiming, EditorialUrgency, ShelfLife


def assess_timing(
    *,
    published_at: datetime | None,
    now: datetime,
    evergreen: bool = False,
) -> EditorialTiming:
    """Assess timing from real timestamps only."""

    now = _aware(now)
    if evergreen:
        return EditorialTiming(
            urgency=EditorialUrgency.EVERGREEN,
            shelf_life=ShelfLife.LONG,
            publish_by=None,
            freshness_score=0.75,
            timing_rationale="Evergreen angle remains useful independent of today's news cycle.",
        )
    if published_at is None:
        return EditorialTiming(
            urgency=EditorialUrgency.CURRENT,
            shelf_life=ShelfLife.MEDIUM,
            publish_by=None,
            freshness_score=0.45,
            timing_rationale="Publication time is unknown, so no exact publish-by time was invented.",
        )
    published = _aware(published_at)
    age_hours = max(0.0, (now - published).total_seconds() / 3600)
    if age_hours <= 24:
        urgency = EditorialUrgency.BREAKING
        shelf_life = ShelfLife.SHORT
        publish_by = published + timedelta(hours=36)
    else:
        urgency = EditorialUrgency.CURRENT
        shelf_life = ShelfLife.MEDIUM
        publish_by = published + timedelta(days=7)
    freshness = max(0.0, min(1.0, 1.0 - age_hours / 240))
    return EditorialTiming(
        urgency=urgency,
        shelf_life=shelf_life,
        publish_by=publish_by,
        freshness_score=round(freshness, 3),
        timing_rationale=f"Published {age_hours:.1f} hours ago based on source timestamp.",
    )


def is_angle_expired(timing: EditorialTiming, angle_is_news: bool, now: datetime) -> bool:
    if not angle_is_news:
        return False
    if timing.urgency is EditorialUrgency.EVERGREEN:
        return False
    return timing.publish_by is not None and _aware(now) > _aware(timing.publish_by)


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value
