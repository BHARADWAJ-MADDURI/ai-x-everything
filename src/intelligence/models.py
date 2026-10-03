from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.shared.models import Audience


class SourceType(Enum):
    """Type of discovered source material."""

    PRIMARY = "primary"
    NEWS = "news"
    RESEARCH = "research"
    COMPANY = "company"
    GOVERNMENT = "government"
    OTHER = "other"


class EvidenceRole(Enum):
    """How a source should be treated as evidence."""

    PRIMARY = "primary"
    SECONDARY = "secondary"


class ClaimKind(Enum):
    """Editorial epistemic status of a claim."""

    FACT = "fact"
    INFERENCE = "inference"
    INTERPRETATION = "interpretation"


class FactType(Enum):
    """Small fact taxonomy for grounded claims."""

    ANNOUNCEMENT = "announcement"
    CAPABILITY = "capability"
    LIMITATION = "limitation"
    METRIC = "metric"
    DEPLOYMENT = "deployment"
    RESEARCH_RESULT = "research_result"
    WORKFLOW_IMPACT = "workflow_impact"
    OTHER = "other"


class AngleType(Enum):
    """Controlled editorial angle types."""

    NEWS = "news"
    TECHNOLOGY = "technology"
    EXPLAINER = "explainer"
    INDUSTRY_IMPACT = "industry_impact"
    WORKFLOW_IMPACT = "workflow_impact"
    CAREER = "career"
    UPSKILL = "upskill"
    STUDENT = "student"
    RESEARCH = "research"
    COMPANY = "company"
    TOOL = "tool"
    RISK_LIMITATION = "risk_limitation"


class EditorialOutcome(Enum):
    """Selection outcome for a story or angle."""

    SELECT = "select"
    HOLD = "hold"
    REJECT = "reject"


class TitleType(Enum):
    """Small title taxonomy for grounded packaging."""

    NEWS = "news"
    EXPLAINER = "explainer"
    IMPACT = "impact"
    CAREER = "career"
    UPSKILL = "upskill"
    RESEARCH = "research"
    QUESTION = "question"


class TargetPlatform(Enum):
    """Future-facing metadata target, not a publishing adapter."""

    INSTAGRAM = "instagram"
    YOUTUBE_SHORTS = "youtube_shorts"
    TIKTOK = "tiktok"
    LINKEDIN = "linkedin"
    X = "x"
    WEBSITE = "website"


class HashtagResearchStatus(Enum):
    """Research freshness state for hashtag candidates."""

    UNRESEARCHED = "unresearched"
    RESEARCHED = "researched"
    STALE = "stale"


class HashtagSource(Enum):
    """Origin of a hashtag candidate."""

    VERIFIED_STORY = "verified_story"
    LIVE_RESEARCH = "live_research"
    PLATFORM_RESEARCH = "platform_research"


@dataclass(kw_only=True)
class CandidateItem:
    """Untrusted discovered item from a future discovery source."""

    id: str
    source_name: str
    source_url: str
    source_type: SourceType
    title: str
    summary: str | None
    published_at: datetime | None
    discovered_at: datetime
    author: str | None = None


@dataclass(frozen=True)
class EvidenceSource:
    """Normalized evidence context for one candidate source."""

    candidate_id: str
    source_name: str
    source_url: str
    source_type: SourceType
    evidence_role: EvidenceRole
    is_independent: bool
    authoritative_for: list[str] = field(default_factory=list)
    evidence_score: float = 0.5
    source_id: str = ""


@dataclass
class StoryCluster:
    """Conservative grouping of candidates covering one development."""

    id: str
    candidates: list[CandidateItem] = field(default_factory=list)

    @property
    def title(self) -> str:
        return self.candidates[0].title if self.candidates else ""


@dataclass(frozen=True)
class EvidenceItem:
    """Single evidence item scoped to exactly one story cluster."""

    evidence_id: str
    cluster_id: str
    source_id: str
    source_url: str
    source_type: SourceType
    supplied_text: str
    published_at: datetime | None


@dataclass(frozen=True)
class EvidencePack:
    """Closed-world evidence universe for one story cluster."""

    cluster_id: str
    canonical_title: str
    sources: list[EvidenceSource]
    evidence_items: list[EvidenceItem]


@dataclass(frozen=True)
class GroundedFact:
    """Claim with provenance and epistemic status."""

    id: str
    claim: str
    supporting_source_urls: list[str]
    confidence: float
    fact_type: FactType
    claim_kind: ClaimKind


@dataclass(frozen=True)
class VerifiedClaimCandidate:
    """Claim proposed by analysis before deterministic validation."""

    claim_id: str
    text: str
    claim_type: ClaimKind
    evidence_ids: list[str]
    reasoning: str | None = None
    numeric_claim: bool = False
    referenced_source_ids: list[str] = field(default_factory=list)
    referenced_source_urls: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ValidationFailure:
    """Structured validation failure for quarantined claims or metadata."""

    item_id: str
    reason: str


@dataclass(frozen=True)
class ClaimValidationResult:
    """Valid and rejected claims after deterministic validation."""

    valid_claims: list[VerifiedClaimCandidate]
    rejected_claims: list[ValidationFailure]


@dataclass
class StoryAnalysis:
    """Structured understanding of a grounded story cluster."""

    development_summary: str
    technologies: list[str] = field(default_factory=list)
    applications: list[str] = field(default_factory=list)
    industries: list[str] = field(default_factory=list)
    workflows: list[str] = field(default_factory=list)
    professions: list[str] = field(default_factory=list)
    demonstrated_capabilities: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    uncertainties: list[str] = field(default_factory=list)
    novelty_summary: str | None = None


@dataclass
class VerifiedStoryAnalysis:
    """Story analysis derived only from validated claims."""

    development_summary: str
    technologies: list[str] = field(default_factory=list)
    applications: list[str] = field(default_factory=list)
    industries: list[str] = field(default_factory=list)
    workflows: list[str] = field(default_factory=list)
    professions: list[str] = field(default_factory=list)
    demonstrated_capabilities: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    uncertainties: list[str] = field(default_factory=list)
    verified_claim_ids: list[str] = field(default_factory=list)


@dataclass
class PotentialAngle:
    """Possible editorial angle with transparent scoring inputs."""

    id: str
    angle_type: AngleType
    thesis: str
    target_audiences: list[Audience]
    evidence_strength: float
    relevance: float
    novelty: float
    usefulness: float
    speculation_risk: float
    supporting_fact_ids: list[str] = field(default_factory=list)
    rationale: str = ""
    score: float | None = None
    rejected: bool = False
    rejection_reason: str | None = None


@dataclass
class AnalyzedStory:
    """Analyzed story cluster with facts, analysis, and angles."""

    cluster: StoryCluster
    evidence_sources: list[EvidenceSource]
    facts: list[GroundedFact]
    analysis: StoryAnalysis
    angles: list[PotentialAngle]


@dataclass(frozen=True)
class EditorialDecision:
    """Editorial selection decision and reasons."""

    outcome: EditorialOutcome
    reasons: list[str]
    selected_angles: list[PotentialAngle] = field(default_factory=list)


@dataclass(frozen=True)
class PipelineResult:
    """Output of the deterministic intelligence pipeline."""

    analyzed_stories: list[AnalyzedStory]
    decisions: dict[str, EditorialDecision]


@dataclass(frozen=True)
class VerifiedGroundedStory:
    """Trust boundary consumed by generation and publishing metadata."""

    cluster_id: str
    canonical_title: str
    evidence_pack: EvidencePack
    verified_claims: list[VerifiedClaimCandidate]
    rejected_claims: list[ValidationFailure]
    analysis: VerifiedStoryAnalysis
    validated_angles: list[PotentialAngle]


@dataclass
class TitleCandidate:
    """Grounded title candidate for content packaging."""

    text: str
    title_type: TitleType
    supported_claim_ids: list[str]
    target_platform: TargetPlatform | None
    hook_strength: float
    clarity: float
    hype_risk: float
    rejected: bool = False
    rejection_reason: str | None = None


@dataclass
class HashtagCandidate:
    """Hashtag candidate with relevance and optional live research data."""

    tag: str
    relevance_score: float
    specificity_score: float
    source: HashtagSource
    research_status: HashtagResearchStatus
    platform: TargetPlatform
    estimated_reach_band: str | None = None
    competition_band: str | None = None
    researched_at: datetime | None = None
    supporting_topic_terms: list[str] = field(default_factory=list)
    selected: bool = False
    rejection_reason: str | None = None


@dataclass(frozen=True)
class PublishingMetadata:
    """Future-facing publishing metadata without platform publishing."""

    selected_title: TitleCandidate
    alternate_titles: list[TitleCandidate]
    selected_hashtags: list[HashtagCandidate]
    hashtag_research_status: HashtagResearchStatus
    selected_angle: PotentialAngle
    target_platform: TargetPlatform
