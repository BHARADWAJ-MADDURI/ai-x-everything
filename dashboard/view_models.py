from dataclasses import dataclass
from datetime import datetime

from dashboard.demo_data import DashboardData
from src.content.package_models import PackageReviewState, PublishableContentPackage, TitleVerificationStatus
from src.editorial.decisions import record_human_decision
from src.editorial.models import (
    BundleCandidate,
    DailyContentPlan,
    EditorialUrgency,
    EvergreenItem,
    HumanDecisionAction,
    HumanEditorialDecision,
    RecommendedPost,
    StoryPlanningInput,
)
from src.intelligence.models import (
    AngleType,
    ClaimKind,
    HashtagCandidate,
    PotentialAngle,
    TitleCandidate,
    VerifiedClaimCandidate,
)


@dataclass(frozen=True)
class AuditEntry:
    timestamp: datetime
    decision: HumanEditorialDecision
    label: str


@dataclass(frozen=True)
class ProvenanceRow:
    claim_id: str
    claim_text: str
    claim_kind: ClaimKind
    evidence_id: str
    evidence_text: str
    source_id: str
    source_name: str
    source_url: str
    source_type: str


@dataclass(frozen=True)
class TrustSummary:
    label: str
    source_count: int
    has_primary_source: bool
    fact_count: int
    inference_count: int
    rejected_count: int


@dataclass(frozen=True)
class ClaimDisplay:
    label: str
    text: str
    evidence: str | None = None
    source_name: str | None = None
    source_url: str | None = None


@dataclass(frozen=True)
class StoryCardViewModel:
    story_id: str
    headline: str
    what_happened: str
    why_it_matters: str
    urgency_label: str
    timing_label: str
    trust_label: str
    content_direction: str
    priority_label: str
    status_label: str
    primary_action: str
    secondary_actions: list[str]


@dataclass(frozen=True)
class TitleChoice:
    text: str
    label: str
    helper: str
    selected: bool


@dataclass(frozen=True)
class HashtagChoice:
    tag: str
    helper: str
    selected: bool


@dataclass(frozen=True)
class ReelScenePreview:
    purpose: str
    narration: str
    on_screen_text: str
    visual_direction: str
    duration_hint: str


@dataclass(frozen=True)
class PackagePreview:
    reel_hook: str
    reel_narration: str
    reel_cta: str
    reel_target_duration: int
    reel_scenes: list[ReelScenePreview]
    instagram_caption: str
    instagram_hashtags: list[str]
    blog_headline: str
    blog_dek: str
    blog_body: str
    linkedin_post: str
    x_posts: list[str]
    tiktok_caption: str
    tiktok_hashtags: list[str]
    youtube_title: str
    youtube_description: str


@dataclass(frozen=True)
class ValidationSummary:
    lines: list[str]
    ready: bool


@dataclass(frozen=True)
class LibraryItem:
    title: str
    helper: str
    status: str


def dashboard_counts(data: DashboardData) -> dict[str, int]:
    return {
        "discovered": len(data.stories),
        "verified": len(data.stories),
        "recommended": len(data.plan.recommended_posts),
        "requiring_review": (
            len(data.plan.recommended_posts)
            + len(data.plan.bundle_candidates)
            + len(data.plan.saved_for_later)
        ),
    }


def decision_action_for_story(decision_log: list[AuditEntry], story_id: str) -> HumanDecisionAction | None:
    actions = [
        entry.decision.action
        for entry in decision_log
        if entry.decision.target_id == story_id
    ]
    return actions[-1] if actions else None


def editorial_status_label(
    *,
    story_id: str,
    decision_log: list[AuditEntry],
    package: PublishableContentPackage | None = None,
) -> str:
    if package and package.review_state is PackageReviewState.APPROVED_FOR_RENDER:
        return "READY FOR RENDER"
    if package:
        return "DRAFT GENERATED"
    action = decision_action_for_story(decision_log, story_id)
    if action is HumanDecisionAction.APPROVE:
        return "APPROVED"
    if action is HumanDecisionAction.SAVE:
        return "SAVED"
    if action is HumanDecisionAction.HOLD:
        return "HELD"
    if action is HumanDecisionAction.REJECT:
        return "REJECTED"
    return "RECOMMENDED"


def primary_action_for_status(status_label: str) -> str:
    return {
        "RECOMMENDED": "Review Story",
        "APPROVED": "Create Draft",
        "DRAFT GENERATED": "Review Draft",
        "READY FOR RENDER": "View Ready Content",
        "SAVED": "Review Saved Story",
        "HELD": "Review Held Story",
        "REJECTED": "View Decision",
    }.get(status_label, "Review Story")


def priority_label(priority: float) -> str:
    if priority >= 0.95:
        return "TOP PICK"
    if priority >= 0.85:
        return "STRONG CANDIDATE"
    return "SAVE FOR LATER"


def timing_label(post: RecommendedPost) -> str:
    if post.urgency is EditorialUrgency.BREAKING:
        return "Publish today"
    if post.urgency is EditorialUrgency.CURRENT:
        return "Can wait 2-3 days"
    return "Evergreen"


def content_direction_label(angle: PotentialAngle | EvergreenItem) -> str:
    angle_type = angle.angle_type.value.replace("_", " ").title()
    if angle.angle_type in {AngleType.EXPLAINER, AngleType.TECHNOLOGY, AngleType.WORKFLOW_IMPACT}:
        return f"DEEP DIVE - {angle_type}"
    if angle.angle_type is AngleType.NEWS:
        return "THE AI BRIEF - News"
    return f"LEARN - {angle_type}"


def trust_summary(story: StoryPlanningInput) -> TrustSummary:
    sources = story.story.evidence_pack.sources
    claims = story.story.verified_claims
    rejected = story.story.rejected_claims
    fact_count = sum(1 for claim in claims if claim.claim_type is ClaimKind.FACT)
    inference_count = sum(1 for claim in claims if claim.claim_type is ClaimKind.INFERENCE)
    has_primary = any(source.evidence_role.value == "primary" for source in sources)
    label = f"Verified from {len(sources)} source{'s' if len(sources) != 1 else ''}"
    if has_primary:
        label += " including a primary source"
    return TrustSummary(
        label=label,
        source_count=len(sources),
        has_primary_source=has_primary,
        fact_count=fact_count,
        inference_count=inference_count,
        rejected_count=len(rejected),
    )


def story_card_view_model(
    *,
    post: RecommendedPost,
    story: StoryPlanningInput,
    decision_log: list[AuditEntry],
    package: PublishableContentPackage | None = None,
) -> StoryCardViewModel:
    status = editorial_status_label(
        story_id=story.story_id,
        decision_log=decision_log,
        package=package,
    )
    trust = trust_summary(story)
    return StoryCardViewModel(
        story_id=story.story_id,
        headline=story.story.canonical_title,
        what_happened=story.story.analysis.development_summary,
        why_it_matters=post.selected_angle.thesis,
        urgency_label=post.urgency.value.upper(),
        timing_label=timing_label(post),
        trust_label=trust.label,
        content_direction=content_direction_label(post.selected_angle),
        priority_label=priority_label(post.priority),
        status_label=status,
        primary_action=primary_action_for_status(status),
        secondary_actions=["Save for later", "Hold", "Reject"],
    )


def today_summary(data: DashboardData, decision_log: list[AuditEntry], packages: dict[str, PublishableContentPackage]) -> dict[str, int]:
    recommended_ids = [post.story_id for post in data.plan.recommended_posts if post.story_id]
    progressed_statuses = {"APPROVED", "DRAFT GENERATED", "READY FOR RENDER", "SAVED", "HELD", "REJECTED"}
    progressed = sum(
        1
        for story_id in recommended_ids
        if editorial_status_label(
            story_id=story_id,
            decision_log=decision_log,
            package=packages.get(story_id),
        )
        in progressed_statuses
    )
    draft_ready = sum(1 for story_id in recommended_ids if packages.get(story_id) is not None)
    ready_for_render = sum(
        1
        for story_id in recommended_ids
        if packages.get(story_id) is not None
        and packages[story_id].review_state is PackageReviewState.APPROVED_FOR_RENDER
    )
    return {
        "attention": len(data.plan.recommended_posts),
        "needs_decision": max(len(data.plan.recommended_posts) - progressed, 0),
        "draft_ready": draft_ready,
        "ready_for_render": ready_for_render,
    }


def saved_library_items(data: DashboardData, decision_log: list[AuditEntry]) -> list[LibraryItem]:
    story_by_id = {story.story_id: story for story in data.stories}
    items: list[LibraryItem] = []
    saved_ids = [
        entry.decision.target_id
        for entry in decision_log
        if entry.decision.action is HumanDecisionAction.SAVE
    ]
    for story_id in dict.fromkeys(saved_ids):
        story = story_by_id.get(story_id)
        if story:
            items.append(
                LibraryItem(
                    title=story.story.canonical_title,
                    helper=story.story.analysis.development_summary,
                    status="SAVED",
                )
            )
    for post in data.plan.saved_for_later:
        story = story_by_id.get(post.story_id or "")
        items.append(
            LibraryItem(
                title=story.story.canonical_title if story else post.story_id or "Saved story",
                helper=content_direction_label(post.selected_angle),
                status="SAVED FOR LATER",
            )
        )
    return items


def evergreen_library_items(data: DashboardData) -> list[LibraryItem]:
    return [
        LibraryItem(
            title=item.proposed_thesis,
            helper=f"{content_direction_label(item)} · Review {display_timestamp(item.review_at)}",
            status=item.status.value.upper(),
        )
        for item in data.evergreen_items
    ]


def display_timestamp(value: datetime | None) -> str:
    return value.isoformat() if value is not None else "UNKNOWN"


def hashtag_reach_label(candidate: HashtagCandidate) -> str:
    return candidate.estimated_reach_band or "UNKNOWN"


def can_select_angle(angle: PotentialAngle, rejected_angle_types: set[AngleType] | None = None) -> bool:
    rejected = rejected_angle_types or set()
    return not angle.rejected and angle.angle_type not in rejected


def select_angle(angle: PotentialAngle, rejected_angle_types: set[AngleType] | None = None) -> PotentialAngle:
    if not can_select_angle(angle, rejected_angle_types):
        raise ValueError("Rejected angles require explicit override and cannot be normally selected.")
    return angle


def select_title(title: TitleCandidate) -> TitleCandidate:
    if title.rejected:
        raise ValueError("Rejected titles cannot be selected.")
    return title


def manual_title_label(value: str) -> str:
    return f"MANUAL — NOT AUTOMATICALLY VERIFIED: {value.strip()}"


def claim_kind_label(kind: ClaimKind) -> str:
    if kind is ClaimKind.FACT:
        return "VERIFIED FACT"
    if kind is ClaimKind.INFERENCE:
        return "INTERPRETATION / REASONED INFERENCE"
    return "NOT ESTABLISHED / REJECTED"


def provenance_display_rows(story: StoryPlanningInput) -> list[ClaimDisplay]:
    return [
        ClaimDisplay(
            label=claim_kind_label(row.claim_kind),
            text=row.claim_text,
            evidence=row.evidence_text,
            source_name=row.source_name,
            source_url=row.source_url,
        )
        for row in provenance_rows(story)
    ]


def rejected_claim_display_rows(story: StoryPlanningInput) -> list[ClaimDisplay]:
    return [
        ClaimDisplay(
            label="NOT ESTABLISHED / REJECTED",
            text=getattr(claim, "text", getattr(claim, "item_id", "Rejected claim")),
            evidence=getattr(claim, "reason", None),
        )
        for claim in story.story.rejected_claims
    ]


def title_choices(
    titles: list[TitleCandidate],
    selected_title: str | None,
) -> list[TitleChoice]:
    fallback = titles[0].text if titles else None
    active = selected_title or fallback
    return [
        TitleChoice(
            text=title.text,
            label=title.text,
            helper=f"{title.title_type.value.title()} - Grounded",
            selected=title.text == active,
        )
        for title in titles
    ]


def hashtag_choices(tags: list[HashtagCandidate], selected_tags: set[str] | None) -> list[HashtagChoice]:
    selected = selected_tags or {tag.tag for tag in tags}
    return [
        HashtagChoice(
            tag=tag.tag,
            helper=f"Relevance: {'High' if tag.relevance_score >= 0.7 else 'Moderate'} | Reach: {hashtag_reach_label(tag)}",
            selected=tag.tag in selected,
        )
        for tag in tags
    ]


def package_preview(package: PublishableContentPackage) -> PackagePreview:
    return PackagePreview(
        reel_hook=package.reel.hook,
        reel_narration=package.reel.narration,
        reel_cta=package.reel.cta,
        reel_target_duration=package.reel.target_duration_seconds,
        reel_scenes=[
            ReelScenePreview(
                purpose=scene.purpose,
                narration=scene.narration,
                on_screen_text=scene.on_screen_text,
                visual_direction=scene.visual_intent.value.replace("_", " ").title(),
                duration_hint=scene.duration_hint,
            )
            for scene in package.reel.scenes
        ],
        instagram_caption=package.instagram.caption,
        instagram_hashtags=[tag.tag for tag in package.instagram.hashtags],
        blog_headline=package.blog.headline,
        blog_dek=package.blog.dek,
        blog_body=package.blog.body,
        linkedin_post=package.linkedin.post_copy,
        x_posts=list(package.x.posts),
        tiktok_caption=package.tiktok.caption,
        tiktok_hashtags=[tag.tag for tag in package.tiktok.hashtags],
        youtube_title=package.youtube_shorts.title,
        youtube_description=package.youtube_shorts.description,
    )


def validation_summary(package: PublishableContentPackage) -> ValidationSummary:
    validation = package.validation
    issues = validation.issues if validation else ["Validation has not run."]
    ready = bool(validation and validation.publish_ready)
    if ready:
        lines = [
            "Uses verified story claims",
            "Source references valid",
            "No unsupported numeric claims detected",
            "Selected angle is verified",
            "Hashtags preserve research status",
        ]
    else:
        lines = issues
    return ValidationSummary(lines=lines, ready=ready)


def manual_title_requires_acknowledgement(package: PublishableContentPackage) -> bool:
    return (
        package.selected_title.verification_status is TitleVerificationStatus.MANUAL_UNVERIFIED
        and not package.selected_title.manual_acknowledged
    )


def create_decision(
    *,
    action: HumanDecisionAction,
    target_id: str,
    decided_at: datetime,
    comment: str | None = None,
    confirmed: bool = False,
) -> HumanEditorialDecision:
    if action in {HumanDecisionAction.REJECT, HumanDecisionAction.APPROVE_BUNDLE} and not confirmed:
        raise ValueError(f"{action.value} requires confirmation")
    return record_human_decision(
        action=action,
        target_id=target_id,
        decided_at=decided_at,
        comment=comment,
    )


def audit_entry(decision: HumanEditorialDecision) -> AuditEntry:
    return AuditEntry(
        timestamp=decision.decided_at,
        decision=decision,
        label=f"{decision.decided_at.strftime('%H:%M')} {decision.action.value.upper()} — {decision.target_id}",
    )


def provenance_rows(story: StoryPlanningInput) -> list[ProvenanceRow]:
    evidence_by_id = {
        item.evidence_id: item
        for item in story.story.evidence_pack.evidence_items
    }
    sources_by_id = {
        source.source_id: source
        for source in story.story.evidence_pack.sources
    }
    rows: list[ProvenanceRow] = []
    for claim in story.story.verified_claims:
        rows.extend(_rows_for_claim(claim, evidence_by_id, sources_by_id))
    return rows


def _rows_for_claim(
    claim: VerifiedClaimCandidate,
    evidence_by_id,
    sources_by_id,
) -> list[ProvenanceRow]:
    rows = []
    for evidence_id in claim.evidence_ids:
        evidence = evidence_by_id.get(evidence_id)
        if evidence is None:
            continue
        source = sources_by_id.get(evidence.source_id)
        rows.append(
            ProvenanceRow(
                claim_id=claim.claim_id,
                claim_text=claim.text,
                claim_kind=claim.claim_type,
                evidence_id=evidence.evidence_id,
                evidence_text=evidence.supplied_text,
                source_id=evidence.source_id,
                source_name=source.source_name if source else "UNKNOWN",
                source_url=source.source_url if source else evidence.source_url,
                source_type=source.source_type.value if source else evidence.source_type.value,
            )
        )
    return rows


def post_slots(plan: DailyContentPlan) -> list[RecommendedPost]:
    return list(plan.recommended_posts)


def metrics_empty_state() -> str:
    return "No posts published yet."


def bundle_story_sections(bundle: BundleCandidate, stories: list[StoryPlanningInput]) -> dict[str, list[str]]:
    story_map = {story.story_id: story for story in stories}
    return {
        story_id: [claim.claim_id for claim in story_map[story_id].story.verified_claims]
        for story_id in bundle.story_ids
        if story_id in story_map
    }
