from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum

from src.intelligence.models import AngleType, PotentialAngle, TargetPlatform
from src.shared.models import Audience


class StoryLifecycleStatus(Enum):
    DISCOVERED = "discovered"
    VERIFIED = "verified"
    SELECTED = "selected"
    PUBLISHED = "published"
    FOLLOW_UP_ELIGIBLE = "follow_up_eligible"
    EVERGREEN_LIBRARY = "evergreen_library"
    HOLD = "hold"
    REJECTED = "rejected"
    EXPIRED = "expired"


class EditorialUrgency(Enum):
    BREAKING = "breaking"
    CURRENT = "current"
    EVERGREEN = "evergreen"


class ShelfLife(Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class FollowUpPotential(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class EvergreenStatus(Enum):
    AVAILABLE = "available"
    USED = "used"
    EXPIRED = "expired"


class StoryRelationshipType(Enum):
    SAME_TREND = "same_trend"
    FOLLOW_UP = "follow_up"
    DEPLOYMENT_OF = "deployment_of"
    RELATED_RESEARCH = "related_research"
    RELATED_TECHNOLOGY = "related_technology"


class RecommendationStatus(Enum):
    RECOMMENDED = "recommended"
    APPROVED = "approved"
    SKIPPED = "skipped"
    SAVED = "saved"


class HumanDecisionAction(Enum):
    APPROVE = "approve"
    SAVE = "save"
    HOLD = "hold"
    REJECT = "reject"
    KEEP_SEPARATE = "keep_separate"
    APPROVE_BUNDLE = "approve_bundle"


@dataclass(frozen=True)
class EditorialTiming:
    urgency: EditorialUrgency
    shelf_life: ShelfLife
    publish_by: datetime | None
    freshness_score: float
    timing_rationale: str


@dataclass(frozen=True)
class AnglePublicationRecord:
    story_id: str
    angle_type: AngleType
    title_used: str
    published_at: datetime
    platform: TargetPlatform
    content_id: str
    angle_id: str | None = None


@dataclass(frozen=True)
class AngleHistory:
    publication_records: list[AnglePublicationRecord] = field(default_factory=list)
    rejected_angle_ids: set[str] = field(default_factory=set)
    rejected_angle_types: set[AngleType] = field(default_factory=set)


@dataclass(frozen=True)
class EvergreenItem:
    item_id: str
    originating_story_id: str
    angle_id: str
    angle_type: AngleType
    proposed_thesis: str
    evidence_claim_refs: list[str]
    created_at: datetime
    audience: list[Audience]
    status: EvergreenStatus = EvergreenStatus.AVAILABLE
    review_at: datetime | None = None
    expires_at: datetime | None = None


@dataclass(frozen=True)
class StoryRelationship:
    left_story_id: str
    right_story_id: str
    relationship_type: StoryRelationshipType
    strength: float
    rationale: str


@dataclass(frozen=True)
class BundleCandidate:
    bundle_id: str
    story_ids: list[str]
    proposed_thesis: str
    relationship_type: StoryRelationshipType
    coherence_score: float
    editorial_value: float
    rationale: str
    claim_refs_by_story: dict[str, list[str]] = field(default_factory=dict)


@dataclass(frozen=True)
class RecommendedPost:
    story_id: str | None
    bundle_id: str | None
    selected_angle: PotentialAngle | EvergreenItem
    priority: float
    urgency: EditorialUrgency
    recommended_publish_window: str | None
    rationale: list[str]
    audience: list[Audience]
    status: RecommendationStatus = RecommendationStatus.RECOMMENDED


@dataclass(frozen=True)
class HeldItem:
    story_id: str
    reason: str


@dataclass(frozen=True)
class ExpiredItem:
    story_id: str
    expired_angle_types: list[AngleType]
    still_valid_angle_types: list[AngleType]
    reason: str


@dataclass(frozen=True)
class DailyContentPlan:
    plan_date: date
    recommended_posts: list[RecommendedPost]
    saved_for_later: list[RecommendedPost]
    bundle_candidates: list[BundleCandidate]
    held_items: list[HeldItem]
    expired_items: list[ExpiredItem]
    planner_summary: str


@dataclass(frozen=True)
class HumanEditorialDecision:
    action: HumanDecisionAction
    target_id: str
    decided_at: datetime
    editor: str | None = None
    comment: str | None = None


@dataclass(frozen=True)
class StoryPlanningInput:
    story_id: str
    story: object
    timing: EditorialTiming
    editorial_score: float
    lifecycle_status: StoryLifecycleStatus = StoryLifecycleStatus.VERIFIED
    domain: str | None = None
