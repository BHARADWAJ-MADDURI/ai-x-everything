from src.content.package_models import (
    BlogPackage,
    CanonicalContentDraft,
    InstagramPackage,
    LinkedInPackage,
    ReelPackage,
    ReelScene,
    SourceReference,
    TikTokPackage,
    VisualIntent,
    XPackage,
    YouTubeShortsPackage,
)
from src.intelligence.models import HashtagCandidate


X_POST_MAX_CHARS = 280


def build_reel_package(
    draft: CanonicalContentDraft,
    *,
    source_reference_ids: list[str],
) -> ReelPackage:
    claim_ids = draft.claim_references
    scenes = [
        ReelScene(
            scene_id="scene-001",
            purpose="HOOK",
            duration_hint="5-8s",
            narration=draft.hook,
            on_screen_text=draft.hook[:80],
            visual_intent=VisualIntent.SOURCE_HEADLINE,
            supporting_claim_ids=claim_ids[:1],
            source_reference_ids=source_reference_ids[:1],
        ),
        ReelScene(
            scene_id="scene-002",
            purpose="WHAT HAPPENED",
            duration_hint="8-12s",
            narration=draft.thesis,
            on_screen_text=draft.thesis[:80],
            visual_intent=VisualIntent.EDITORIAL_TEXT,
            supporting_claim_ids=claim_ids,
            source_reference_ids=source_reference_ids[:1],
        ),
        ReelScene(
            scene_id="scene-003",
            purpose="WHY IT MATTERS",
            duration_hint="10-16s",
            narration=draft.technical_explanation,
            on_screen_text=(draft.key_points[0] if draft.key_points else draft.takeaway)[:80],
            visual_intent=VisualIntent.TECH_DIAGRAM,
            supporting_claim_ids=claim_ids,
            source_reference_ids=[],
        ),
        ReelScene(
            scene_id="scene-004",
            purpose="TAKEAWAY",
            duration_hint="6-10s",
            narration=f"{draft.takeaway} {draft.cta}",
            on_screen_text=draft.takeaway[:80],
            visual_intent=VisualIntent.OUTRO,
            supporting_claim_ids=claim_ids,
            source_reference_ids=[],
        ),
    ]
    narration = " ".join(scene.narration for scene in scenes)
    return ReelPackage(
        hook=draft.hook,
        target_duration_seconds=45,
        scenes=scenes,
        narration=narration,
        on_screen_text=[scene.on_screen_text for scene in scenes],
        cta=draft.cta,
    )


def build_instagram_package(draft: CanonicalContentDraft, hashtags: list[HashtagCandidate]) -> InstagramPackage:
    caption = f"{draft.hook}\n\n{draft.thesis}\n\nTakeaway: {draft.takeaway}\n\nSources are preserved in the package."
    return InstagramPackage(caption=caption, hashtags=hashtags)


def build_blog_package(
    draft: CanonicalContentDraft,
    *,
    title: str,
    source_references: list[SourceReference],
) -> BlogPackage:
    body = "\n\n".join(
        [
            "## What happened\n" + draft.thesis,
            "## How it works\n" + draft.technical_explanation,
            "## Why it matters\n" + (draft.human_implication or draft.takeaway),
            "## What to watch next\n" + draft.takeaway,
        ]
    )
    return BlogPackage(
        headline=title,
        dek=draft.hook,
        body=body,
        source_references=source_references,
    )


def build_linkedin_package(draft: CanonicalContentDraft) -> LinkedInPackage:
    return LinkedInPackage(
        post_copy=f"{draft.thesis}\n\n{draft.technical_explanation}\n\n{draft.takeaway}"
    )


def build_x_package(draft: CanonicalContentDraft) -> XPackage:
    single = f"{draft.hook} {draft.takeaway}"
    if len(single) <= X_POST_MAX_CHARS:
        return XPackage(posts=[single])
    return XPackage(posts=[draft.hook[:X_POST_MAX_CHARS], draft.takeaway[:X_POST_MAX_CHARS]])


def build_tiktok_package(draft: CanonicalContentDraft, hashtags: list[HashtagCandidate]) -> TikTokPackage:
    return TikTokPackage(caption=f"{draft.hook} {draft.takeaway}", hashtags=hashtags)


def build_youtube_shorts_package(draft: CanonicalContentDraft, *, title: str) -> YouTubeShortsPackage:
    return YouTubeShortsPackage(
        title=title[:100],
        description=f"{draft.thesis}\n\n{draft.takeaway}",
    )
