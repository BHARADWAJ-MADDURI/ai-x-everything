from src.editorial.models import StoryLifecycleStatus


VALID_TRANSITIONS = {
    StoryLifecycleStatus.DISCOVERED: {
        StoryLifecycleStatus.VERIFIED,
        StoryLifecycleStatus.REJECTED,
    },
    StoryLifecycleStatus.VERIFIED: {
        StoryLifecycleStatus.SELECTED,
        StoryLifecycleStatus.HOLD,
        StoryLifecycleStatus.EVERGREEN_LIBRARY,
        StoryLifecycleStatus.REJECTED,
        StoryLifecycleStatus.EXPIRED,
    },
    StoryLifecycleStatus.SELECTED: {
        StoryLifecycleStatus.PUBLISHED,
        StoryLifecycleStatus.HOLD,
        StoryLifecycleStatus.REJECTED,
    },
    StoryLifecycleStatus.PUBLISHED: {
        StoryLifecycleStatus.FOLLOW_UP_ELIGIBLE,
        StoryLifecycleStatus.EVERGREEN_LIBRARY,
    },
    StoryLifecycleStatus.HOLD: {
        StoryLifecycleStatus.SELECTED,
        StoryLifecycleStatus.EXPIRED,
        StoryLifecycleStatus.REJECTED,
    },
    StoryLifecycleStatus.FOLLOW_UP_ELIGIBLE: {
        StoryLifecycleStatus.SELECTED,
        StoryLifecycleStatus.EVERGREEN_LIBRARY,
        StoryLifecycleStatus.EXPIRED,
    },
    StoryLifecycleStatus.EVERGREEN_LIBRARY: {
        StoryLifecycleStatus.SELECTED,
        StoryLifecycleStatus.EXPIRED,
    },
    StoryLifecycleStatus.REJECTED: set(),
    StoryLifecycleStatus.EXPIRED: set(),
}


def transition_story(
    current: StoryLifecycleStatus,
    target: StoryLifecycleStatus,
) -> StoryLifecycleStatus:
    """Move a story lifecycle state or fail with a clear error."""

    if target not in VALID_TRANSITIONS[current]:
        raise ValueError(f"Invalid story lifecycle transition: {current.value} -> {target.value}")
    return target
