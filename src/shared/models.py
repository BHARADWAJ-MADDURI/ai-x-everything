from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Audience(Enum):
    """Core audiences served by Everything × AI."""

    STUDENT = "student"
    PROFESSIONAL = "professional"
    ENTHUSIAST = "enthusiast"


class StoryType(Enum):
    """High-level editorial type for a canonical story."""

    NEWS = "news"
    IMPACT = "impact"
    CAREER = "career"
    EXPLAINER = "explainer"
    TOOL = "tool"
    COMPANY = "company"
    RESEARCH = "research"


class ContentFormat(Enum):
    """Platform-independent format for derived content assets."""

    SHORT_VIDEO = "short_video"
    CAROUSEL = "carousel"
    SHORT_TEXT = "short_text"
    LONG_TEXT = "long_text"
    ARTICLE = "article"
    NEWSLETTER = "newsletter"


class Platform(Enum):
    """Distribution surfaces supported by platform adapters."""

    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    LINKEDIN = "linkedin"
    X = "x"
    WEBSITE = "website"
    EMAIL = "email"


class PublicationStatus(Enum):
    """Lifecycle status for a publication instance."""

    DRAFT = "draft"
    READY_FOR_REVIEW = "ready_for_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"
    FAILED = "failed"


@dataclass
class Source:
    """External source used to research and ground a story."""

    id: str
    url: str
    title: str | None
    publisher: str | None
    published_at: datetime | None
    retrieved_at: datetime
    source_type: str | None


@dataclass
class StoryScores:
    """Editorial and intelligence scores assigned to a story."""

    relevance: float | None = None
    timeliness: float | None = None
    significance: float | None = None
    evidence_quality: float | None = None
    educational_value: float | None = None
    career_impact: float | None = None
    content_potential: float | None = None
    novelty: float | None = None


@dataclass
class AudienceValue:
    """Estimated usefulness of a story for each core audience."""

    student: float | None = None
    professional: float | None = None
    enthusiast: float | None = None


@dataclass(kw_only=True)
class Story:
    """Canonical, platform-independent understanding of an AI development."""

    id: str
    headline: str
    summary: str
    domain: str
    subdomain: str | None
    story_type: StoryType
    why_it_matters: str
    source_published_at: datetime | None
    discovered_at: datetime
    scores: StoryScores
    audience_value: AudienceValue
    audiences: list[Audience] = field(default_factory=list)
    professions_affected: list[str] = field(default_factory=list)
    industries_affected: list[str] = field(default_factory=list)
    companies: list[str] = field(default_factory=list)
    concepts: list[str] = field(default_factory=list)
    sources: list[Source] = field(default_factory=list)


@dataclass(kw_only=True)
class Article:
    """Long-form canonical explanation derived from a story."""

    id: str
    story_id: str
    title: str
    subtitle: str | None
    tldr: str
    what_happened: str
    how_it_works: str | None
    why_it_matters: str
    industry_impact: str | None
    career_impact: str | None
    created_at: datetime
    updated_at: datetime
    opportunities: list[str] = field(default_factory=list)
    risks_and_limitations: list[str] = field(default_factory=list)
    key_concepts: list[str] = field(default_factory=list)
    source_ids: list[str] = field(default_factory=list)


@dataclass
class GenerationMetadata:
    """Metadata describing AI generation cost and performance."""

    model: str | None
    provider: str | None
    generated_at: datetime
    latency_ms: int | None
    input_tokens: int | None
    output_tokens: int | None
    estimated_cost_usd: float | None
    prompt_version: str | None


@dataclass(kw_only=True)
class ContentAsset:
    """Platform-aware but platform-independent content derived from knowledge."""

    id: str
    story_id: str
    article_id: str | None
    format: ContentFormat
    title: str | None = None
    hook: str | None = None
    body: str = ""
    call_to_action: str | None = None
    generation_metadata: GenerationMetadata | None = None
    created_at: datetime
    target_platforms: list[Platform] = field(default_factory=list)
    target_audiences: list[Audience] = field(default_factory=list)


@dataclass
class Publication:
    """One publishing instance for a content asset on a platform."""

    id: str
    content_asset_id: str
    platform: Platform
    format: ContentFormat
    status: PublicationStatus
    platform_post_id: str | None
    platform_url: str | None
    published_at: datetime | None
    created_at: datetime


@dataclass
class MetricSnapshot:
    """Time-series snapshot of metrics for a publication."""

    id: str
    publication_id: str
    captured_at: datetime
    hours_since_publish: float | None = None
    views: int | None = None
    reach: int | None = None
    impressions: int | None = None
    likes: int | None = None
    comments: int | None = None
    shares: int | None = None
    saves: int | None = None
    watch_time_seconds: float | None = None
    average_watch_time_seconds: float | None = None
    completion_rate: float | None = None
    followers_gained: int | None = None
    website_clicks: int | None = None


@dataclass
class EditorialDecision:
    """Human approval or rejection decision for generated content."""

    id: str
    content_asset_id: str
    approved: bool
    reviewed_at: datetime
    rejection_reason: str | None
    review_notes: str | None
