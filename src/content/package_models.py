from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.editorial.models import HumanEditorialDecision
from src.intelligence.models import (
    HashtagCandidate,
    PotentialAngle,
    TargetPlatform,
    TitleCandidate,
)
from src.shared.models import Audience, GenerationMetadata


class TitleVerificationStatus(Enum):
    GROUNDED = "grounded"
    MANUAL_UNVERIFIED = "manual_unverified"


class PackageValidationStatus(Enum):
    READY = "ready"
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"


class PackageReviewState(Enum):
    DRAFT = "draft"
    NEEDS_REVIEW = "needs_review"
    APPROVED_FOR_RENDER = "approved_for_render"
    REJECTED = "rejected"


class PlatformContentStatus(Enum):
    READY = "ready"
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"


class VisualIntent(Enum):
    SOURCE_HEADLINE = "source_headline"
    TECH_DIAGRAM = "tech_diagram"
    DATA_CARD = "data_card"
    CONCEPT_VISUAL = "concept_visual"
    WORKFLOW = "workflow"
    QUOTE_CARD = "quote_card"
    EDITORIAL_TEXT = "editorial_text"
    OUTRO = "outro"


@dataclass(frozen=True)
class SelectedTitle:
    text: str
    verification_status: TitleVerificationStatus
    supporting_claim_ids: list[str] = field(default_factory=list)
    manual_acknowledged: bool = False


@dataclass(frozen=True)
class SourceReference:
    source_id: str
    source_name: str
    source_url: str
    source_type: str


@dataclass(frozen=True)
class CanonicalContentDraft:
    hook: str
    thesis: str
    key_points: list[str]
    technical_explanation: str
    human_implication: str | None
    career_upskill_implication: str | None
    takeaway: str
    cta: str
    claim_references: list[str]


@dataclass(frozen=True)
class ReelScene:
    scene_id: str
    purpose: str
    duration_hint: str
    narration: str
    on_screen_text: str
    visual_intent: VisualIntent
    supporting_claim_ids: list[str]
    source_reference_ids: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ReelPackage:
    hook: str
    target_duration_seconds: int
    scenes: list[ReelScene]
    narration: str
    on_screen_text: list[str]
    cta: str
    status: PlatformContentStatus = PlatformContentStatus.READY


@dataclass(frozen=True)
class InstagramPackage:
    caption: str
    hashtags: list[HashtagCandidate]
    status: PlatformContentStatus = PlatformContentStatus.READY


@dataclass(frozen=True)
class BlogPackage:
    headline: str
    dek: str
    body: str
    source_references: list[SourceReference]
    status: PlatformContentStatus = PlatformContentStatus.READY


@dataclass(frozen=True)
class LinkedInPackage:
    post_copy: str
    status: PlatformContentStatus = PlatformContentStatus.READY


@dataclass(frozen=True)
class XPackage:
    posts: list[str]
    status: PlatformContentStatus = PlatformContentStatus.READY


@dataclass(frozen=True)
class TikTokPackage:
    caption: str
    hashtags: list[HashtagCandidate]
    status: PlatformContentStatus = PlatformContentStatus.READY


@dataclass(frozen=True)
class YouTubeShortsPackage:
    title: str
    description: str
    status: PlatformContentStatus = PlatformContentStatus.READY


@dataclass(frozen=True)
class PackageValidationResult:
    status: PackageValidationStatus
    issues: list[str]
    publish_ready: bool


@dataclass(frozen=True)
class GenerationReadinessResult:
    ready: bool
    issues: list[str]
    allowed_claim_ids: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PublishableContentPackage:
    package_id: str
    story_id: str
    cluster_id: str
    created_at: datetime
    selected_angle: PotentialAngle
    audience: list[Audience]
    selected_title: SelectedTitle
    human_decision: HumanEditorialDecision
    allowed_claim_ids: list[str]
    source_references: list[SourceReference]
    evidence_reference_ids: list[str]
    canonical_draft: CanonicalContentDraft
    reel: ReelPackage
    instagram: InstagramPackage
    blog: BlogPackage
    linkedin: LinkedInPackage
    x: XPackage
    tiktok: TikTokPackage
    youtube_shorts: YouTubeShortsPackage
    generation_metadata: GenerationMetadata
    validation: PackageValidationResult | None
    review_state: PackageReviewState = PackageReviewState.DRAFT

    @property
    def publish_ready(self) -> bool:
        return (
            self.validation is not None
            and self.validation.publish_ready
            and self.review_state is PackageReviewState.APPROVED_FOR_RENDER
        )
