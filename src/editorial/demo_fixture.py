from datetime import datetime, timedelta, timezone

from src.editorial.evergreen import evergreen_from_angle
from src.editorial.models import EvergreenItem, StoryPlanningInput
from src.editorial.timing import assess_timing
from src.intelligence.models import (
    AngleType,
    ClaimKind,
    EvidenceItem,
    EvidencePack,
    EvidenceRole,
    EvidenceSource,
    PotentialAngle,
    SourceType,
    VerifiedClaimCandidate,
    VerifiedGroundedStory,
    VerifiedStoryAnalysis,
)
from src.shared.models import Audience


DEMO_NOW = datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc)


def busy_news_day_fixture() -> tuple[list[StoryPlanningInput], list[EvergreenItem]]:
    stories = [
        _planning_story("robotics-release", "Major robotics release", "robotics", 0.94, DEMO_NOW - timedelta(hours=3)),
        _planning_story("healthcare-research", "Healthcare AI research", "healthcare", 0.88, DEMO_NOW - timedelta(days=2)),
        _planning_story("model-announcement", "AI model announcement", "models", 0.91, DEMO_NOW - timedelta(hours=5)),
        _planning_story("manufacturing-deployment", "Manufacturing deployment", "robotics", 0.86, DEMO_NOW - timedelta(days=1)),
        _planning_story("weak-hype", "Weak hype story", "hype", 0.22, DEMO_NOW - timedelta(hours=1)),
        _planning_story("expired-news-valid-explainer", "Expired news with reusable explainer", "education", 0.82, DEMO_NOW - timedelta(days=12)),
    ]
    evergreen_source = _planning_story(
        "evergreen-vla-explainer",
        "How VLA models work",
        "robotics",
        0.9,
        DEMO_NOW - timedelta(days=30),
        evergreen=True,
    )
    evergreen = evergreen_from_angle(
        evergreen_source.story,
        evergreen_source.story.validated_angles[1],
        created_at=DEMO_NOW - timedelta(days=2),
        review_at=DEMO_NOW + timedelta(days=30),
    )
    return stories, [evergreen]


def _planning_story(
    story_id: str,
    title: str,
    domain: str,
    score: float,
    published_at: datetime,
    *,
    evergreen: bool = False,
) -> StoryPlanningInput:
    story = _verified_story(story_id, title, domain)
    return StoryPlanningInput(
        story_id=story_id,
        story=story,
        timing=assess_timing(published_at=published_at, now=DEMO_NOW, evergreen=evergreen),
        editorial_score=score,
        domain=domain,
    )


def _verified_story(story_id: str, title: str, domain: str) -> VerifiedGroundedStory:
    claim = VerifiedClaimCandidate(
        f"{story_id}-claim",
        f"{title} has verified evidence in {domain}.",
        ClaimKind.FACT,
        [f"{story_id}-evidence"],
    )
    evidence_pack = EvidencePack(
        cluster_id=story_id,
        canonical_title=title,
        sources=[
            EvidenceSource(
                candidate_id=f"{story_id}-candidate",
                source_name="Demo Source",
                source_url=f"https://example.com/{story_id}",
                source_type=SourceType.NEWS,
                evidence_role=EvidenceRole.SECONDARY,
                is_independent=True,
                source_id="source_001",
            )
        ],
        evidence_items=[
            EvidenceItem(
                evidence_id=f"{story_id}-evidence",
                cluster_id=story_id,
                source_id="source_001",
                source_url=f"https://example.com/{story_id}",
                source_type=SourceType.NEWS,
                supplied_text="Demo evidence text.",
                published_at=DEMO_NOW,
            )
        ],
    )
    return VerifiedGroundedStory(
        cluster_id=story_id,
        canonical_title=title,
        evidence_pack=evidence_pack,
        verified_claims=[claim],
        rejected_claims=[],
        analysis=VerifiedStoryAnalysis(
            development_summary=title,
            technologies=[domain, "AI"],
            applications=[f"{domain} application"],
            industries=[domain],
            workflows=[f"{domain} workflow"],
            verified_claim_ids=[claim.claim_id],
        ),
        validated_angles=[
            _angle("news", AngleType.NEWS, f"What changed in {title}", 0.84, claim.claim_id),
            _angle("explainer", AngleType.EXPLAINER, f"How to understand {title}", 0.82, claim.claim_id),
            _angle("technology", AngleType.TECHNOLOGY, f"The technical layer behind {title}", 0.8, claim.claim_id),
            _angle("workflow", AngleType.WORKFLOW_IMPACT, f"What {title} could change in workflows", 0.78, claim.claim_id),
        ],
    )


def _angle(angle_id: str, angle_type: AngleType, thesis: str, score: float, claim_id: str) -> PotentialAngle:
    return PotentialAngle(
        id=angle_id,
        angle_type=angle_type,
        thesis=thesis,
        target_audiences=[Audience.STUDENT, Audience.PROFESSIONAL, Audience.ENTHUSIAST],
        evidence_strength=0.84,
        relevance=0.84,
        novelty=0.72,
        usefulness=0.82,
        speculation_risk=0.15,
        supporting_fact_ids=[claim_id],
        score=score,
    )
