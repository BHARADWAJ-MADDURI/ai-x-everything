from src.intelligence.hashtags import select_hashtags
from src.intelligence.models import (
    HashtagCandidate,
    HashtagResearchStatus,
    PotentialAngle,
    PublishingMetadata,
    TargetPlatform,
    TitleCandidate,
)
from src.intelligence.titles import validate_title
from src.intelligence.models import VerifiedGroundedStory


def create_publishing_metadata(
    story: VerifiedGroundedStory,
    titles: list[TitleCandidate],
    hashtags: list[HashtagCandidate],
    selected_angle: PotentialAngle,
    target_platform: TargetPlatform,
    hashtag_limit: int = 5,
) -> PublishingMetadata:
    """Create publishing metadata without scheduling or platform APIs."""

    valid_titles = []
    for title in titles:
        validated, failure = validate_title(title, story)
        if failure is None:
            valid_titles.append(validated)
    if not valid_titles:
        raise ValueError("At least one valid title is required.")
    selected_hashtags = select_hashtags(hashtags, limit=hashtag_limit)
    statuses = {tag.research_status for tag in selected_hashtags}
    hashtag_status = (
        HashtagResearchStatus.RESEARCHED
        if statuses and statuses == {HashtagResearchStatus.RESEARCHED}
        else HashtagResearchStatus.UNRESEARCHED
    )
    return PublishingMetadata(
        selected_title=valid_titles[0],
        alternate_titles=valid_titles[1:],
        selected_hashtags=selected_hashtags,
        hashtag_research_status=hashtag_status,
        selected_angle=selected_angle,
        target_platform=target_platform,
    )
