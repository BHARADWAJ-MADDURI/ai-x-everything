from dataclasses import dataclass, field
from datetime import date
from enum import Enum
import re

from src.content.package_models import PackageReviewState
from src.editorial.models import EditorialUrgency, EvergreenItem, StoryLifecycleStatus, StoryPlanningInput
from src.intelligence.models import AngleType, PotentialAngle


class EditorialFormat(Enum):
    AI_BRIEF = "ai_brief"
    DEEP_DIVE = "deep_dive"
    LEARN = "learn"


@dataclass(frozen=True)
class FormatValidationResult:
    ready: bool
    issues: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class FormatRecommendation:
    editorial_format: EditorialFormat
    reason: str
    story_ids: list[str] = field(default_factory=list)
    evergreen_item_ids: list[str] = field(default_factory=list)
    requires_human_approval: bool = True
    override_allowed: bool = True


@dataclass(frozen=True)
class BriefSourceRef:
    story_id: str
    source_id: str
    source_name: str
    source_url: str


@dataclass(frozen=True)
class AIBriefItem:
    position: int
    story_id: str
    cluster_id: str
    headline: str
    category: str
    what_happened: str
    why_it_matters: str
    supporting_claim_ids: list[str]
    evidence_reference_ids: list[str]
    source_refs: list[BriefSourceRef]


@dataclass(frozen=True)
class AIBriefPackage:
    brief_id: str
    date: date
    title: str
    subtitle: str
    items: list[AIBriefItem]
    validation: FormatValidationResult
    review_state: PackageReviewState = PackageReviewState.DRAFT

    @property
    def item_count(self) -> int:
        return len(self.items)


@dataclass(frozen=True)
class BriefSelection:
    selected: list[StoryPlanningInput]
    overflow: list[StoryPlanningInput]
    ineligible: list[StoryPlanningInput]


@dataclass(frozen=True)
class DeepDivePackage:
    story_id: str
    cluster_id: str
    headline: str
    selected_angle: PotentialAngle
    sections: dict[str, str]
    validation: FormatValidationResult
    review_state: PackageReviewState = PackageReviewState.DRAFT


@dataclass(frozen=True)
class LearnPackage:
    topic: str
    grounding_story_id: str | None
    supporting_claim_ids: list[str]
    source_refs: list[BriefSourceRef]
    summary: str
    validation: FormatValidationResult
    review_state: PackageReviewState = PackageReviewState.DRAFT


MIN_BRIEF_ITEMS = 3
MAX_BRIEF_ITEMS = 10
MIN_BRIEF_EDITORIAL_SCORE = 0.7
NUMERIC_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])(?:[$]\d[\d,]*(?:\.\d+)?(?:\s+(?:million|billion|trillion))?|\d[\d,]*(?:\.\d+)?%|\d[\d,]*(?:\.\d+)?x|\d{4})(?![A-Za-z0-9])",
    re.IGNORECASE,
)


def brief_title(item_count: int) -> tuple[str, str]:
    noun = "development" if item_count == 1 else "developments"
    return "The AI Brief", f"{item_count} AI {noun} worth knowing today"


def story_qualifies_for_brief(story: StoryPlanningInput) -> bool:
    return (
        story.lifecycle_status is StoryLifecycleStatus.VERIFIED
        and story.editorial_score >= MIN_BRIEF_EDITORIAL_SCORE
        and story.timing.urgency in {EditorialUrgency.BREAKING, EditorialUrgency.CURRENT}
        and bool(story.story.verified_claims)
        and bool(story.story.evidence_pack.sources)
        and _has_ai_relevance(story)
    )


def select_ai_brief_candidates(stories: list[StoryPlanningInput]) -> BriefSelection:
    eligible = [story for story in stories if story_qualifies_for_brief(story)]
    ranked = sorted(eligible, key=lambda story: story.editorial_score, reverse=True)
    selected = ranked[:MAX_BRIEF_ITEMS]
    overflow = ranked[MAX_BRIEF_ITEMS:]
    ineligible = [story for story in stories if story not in eligible]
    return BriefSelection(selected=selected, overflow=overflow, ineligible=ineligible)


def build_ai_brief_package(
    *,
    brief_id: str,
    package_date: date,
    stories: list[StoryPlanningInput],
) -> AIBriefPackage:
    title, subtitle = brief_title(len(stories))
    items = [_brief_item(index, story) for index, story in enumerate(stories, start=1)]
    package = AIBriefPackage(
        brief_id=brief_id,
        date=package_date,
        title=title,
        subtitle=subtitle,
        items=items,
        validation=FormatValidationResult(ready=False, issues=["validation not run"]),
    )
    return AIBriefPackage(
        brief_id=package.brief_id,
        date=package.date,
        title=package.title,
        subtitle=package.subtitle,
        items=package.items,
        validation=validate_ai_brief_package(package, stories),
        review_state=package.review_state,
    )


def validate_ai_brief_package(package: AIBriefPackage, stories: list[StoryPlanningInput]) -> FormatValidationResult:
    issues: list[str] = []
    story_by_id = {story.story_id: story for story in stories}
    seen_story_ids: set[str] = set()

    if not MIN_BRIEF_ITEMS <= len(package.items) <= MAX_BRIEF_ITEMS:
        issues.append("AI Brief must contain 3-10 items")
    if package.subtitle != brief_title(len(package.items))[1]:
        issues.append("brief title must reflect actual item count")

    for expected_position, item in enumerate(package.items, start=1):
        if item.position != expected_position:
            issues.append("brief item ordering must be preserved")
        if item.story_id in seen_story_ids:
            issues.append(f"duplicate story {item.story_id}")
        seen_story_ids.add(item.story_id)

        story = story_by_id.get(item.story_id)
        if story is None:
            issues.append(f"unknown story {item.story_id}")
            continue
        if item.cluster_id != story.story.cluster_id:
            issues.append(f"item {item.story_id} references the wrong cluster")
        claim_ids = {claim.claim_id for claim in story.story.verified_claims}
        evidence_ids = {evidence.evidence_id for evidence in story.story.evidence_pack.evidence_items}
        source_ids = {source.source_id for source in story.story.evidence_pack.sources}
        source_urls = {source.source_url for source in story.story.evidence_pack.sources}
        claim_text = " ".join(
            claim.text for claim in story.story.verified_claims if claim.claim_id in item.supporting_claim_ids
        )

        if not item.supporting_claim_ids:
            issues.append(f"item {item.story_id} needs supporting claims")
        for claim_id in item.supporting_claim_ids:
            if claim_id not in claim_ids:
                issues.append(f"cross-story or unknown claim reference {claim_id}")
        for evidence_id in item.evidence_reference_ids:
            if evidence_id not in evidence_ids:
                issues.append(f"cross-story or unknown evidence reference {evidence_id}")
        for source in item.source_refs:
            if source.story_id != item.story_id:
                issues.append(f"source reference leaks from story {source.story_id} into {item.story_id}")
            if source.source_id not in source_ids:
                issues.append(f"unknown source ID {source.source_id}")
            if source.source_url not in source_urls:
                issues.append(f"invented source URL {source.source_url}")
        unsupported = _unsupported_numerics(
            " ".join([item.headline, item.what_happened, item.why_it_matters]),
            claim_text,
        )
        if unsupported:
            issues.append(f"item {item.story_id} contains unsupported numeric material: {', '.join(unsupported)}")

    return FormatValidationResult(ready=not issues, issues=issues)


def build_deep_dive_package(
    *,
    story: StoryPlanningInput,
    selected_angle: PotentialAngle,
) -> DeepDivePackage:
    sections = {
        "what_happened": story.story.analysis.development_summary,
        "how_it_works": selected_angle.thesis,
        "why_it_matters": selected_angle.thesis,
        "what_it_could_mean": story.timing.timing_rationale,
        "what_to_watch": "Watch for verified follow-up evidence before expanding the claim.",
    }
    package = DeepDivePackage(
        story_id=story.story_id,
        cluster_id=story.story.cluster_id,
        headline=story.story.canonical_title,
        selected_angle=selected_angle,
        sections=sections,
        validation=FormatValidationResult(ready=False, issues=["validation not run"]),
    )
    return DeepDivePackage(
        story_id=package.story_id,
        cluster_id=package.cluster_id,
        headline=package.headline,
        selected_angle=package.selected_angle,
        sections=package.sections,
        validation=validate_deep_dive_package(package, story),
        review_state=package.review_state,
    )


def validate_deep_dive_package(package: DeepDivePackage, story: StoryPlanningInput) -> FormatValidationResult:
    issues: list[str] = []
    if package.story_id != story.story_id or package.cluster_id != story.story.cluster_id:
        issues.append("Deep Dive must reference exactly one primary story")
    if package.selected_angle not in story.story.validated_angles:
        issues.append("Deep Dive selected angle must belong to the primary story")
    angle_claim_ids = set(package.selected_angle.supporting_fact_ids)
    story_claim_ids = {claim.claim_id for claim in story.story.verified_claims}
    if not angle_claim_ids or not angle_claim_ids <= story_claim_ids:
        issues.append("Deep Dive angle must be grounded in verified story claims")
    if package.selected_angle.angle_type not in {AngleType.CAREER, AngleType.UPSKILL}:
        career_text = " ".join(package.sections.values()).lower()
        if "career advice" in career_text or "upskill plan" in career_text:
            issues.append("career/upskill content cannot be forced without a supported angle")
    return FormatValidationResult(ready=not issues, issues=issues)


def build_learn_package(
    *,
    topic: str,
    grounding_story: StoryPlanningInput | None = None,
    evergreen_item: EvergreenItem | None = None,
) -> LearnPackage:
    source_story = grounding_story
    claim_ids = []
    source_refs: list[BriefSourceRef] = []
    if source_story is not None:
        claim_ids = [claim.claim_id for claim in source_story.story.verified_claims]
        source_refs = _source_refs(source_story)
    elif evergreen_item is not None:
        claim_ids = list(evergreen_item.evidence_claim_refs)
    package = LearnPackage(
        topic=topic,
        grounding_story_id=source_story.story_id if source_story else evergreen_item.originating_story_id if evergreen_item else None,
        supporting_claim_ids=claim_ids,
        source_refs=source_refs,
        summary=f"Evergreen explainer grounded in verified material: {topic}",
        validation=FormatValidationResult(ready=False, issues=["validation not run"]),
    )
    return LearnPackage(
        topic=package.topic,
        grounding_story_id=package.grounding_story_id,
        supporting_claim_ids=package.supporting_claim_ids,
        source_refs=package.source_refs,
        summary=package.summary,
        validation=validate_learn_package(package),
        review_state=package.review_state,
    )


def validate_learn_package(package: LearnPackage) -> FormatValidationResult:
    issues: list[str] = []
    if not package.grounding_story_id:
        issues.append("Learn requires a grounding story or evergreen evidence boundary")
    if not package.supporting_claim_ids:
        issues.append("Learn requires supporting verified claim references")
    return FormatValidationResult(ready=not issues, issues=issues)


def recommend_formats(
    *,
    stories: list[StoryPlanningInput],
    evergreen_items: list[EvergreenItem],
) -> list[FormatRecommendation]:
    recommendations: list[FormatRecommendation] = []
    brief_selection = select_ai_brief_candidates(stories)
    if len(brief_selection.selected) >= MIN_BRIEF_ITEMS:
        recommendations.append(
            FormatRecommendation(
                editorial_format=EditorialFormat.AI_BRIEF,
                reason=f"{len(brief_selection.selected)} verified current stories qualify for a Brief.",
                story_ids=[story.story_id for story in brief_selection.selected],
            )
        )
    strong_story = next(
        (
            story
            for story in sorted(stories, key=lambda item: item.editorial_score, reverse=True)
            if story_qualifies_for_brief(story)
        ),
        None,
    )
    if strong_story is not None:
        recommendations.append(
            FormatRecommendation(
                editorial_format=EditorialFormat.DEEP_DIVE,
                reason="One high-impact verified story has enough grounding for a focused explanation.",
                story_ids=[strong_story.story_id],
            )
        )
    if evergreen_items:
        recommendations.append(
            FormatRecommendation(
                editorial_format=EditorialFormat.LEARN,
                reason="Grounded evergreen material is available for an educational explainer.",
                evergreen_item_ids=[item.item_id for item in evergreen_items],
            )
        )
    return recommendations


def _brief_item(position: int, story: StoryPlanningInput) -> AIBriefItem:
    angle = story.story.validated_angles[0]
    return AIBriefItem(
        position=position,
        story_id=story.story_id,
        cluster_id=story.story.cluster_id,
        headline=story.story.canonical_title,
        category=story.domain or "AI",
        what_happened=story.story.analysis.development_summary,
        why_it_matters=angle.thesis,
        supporting_claim_ids=list(angle.supporting_fact_ids),
        evidence_reference_ids=[
            evidence.evidence_id
            for evidence in story.story.evidence_pack.evidence_items
        ],
        source_refs=_source_refs(story),
    )


def _source_refs(story: StoryPlanningInput) -> list[BriefSourceRef]:
    return [
        BriefSourceRef(
            story_id=story.story_id,
            source_id=source.source_id,
            source_name=source.source_name,
            source_url=source.source_url,
        )
        for source in story.story.evidence_pack.sources
    ]


def _has_ai_relevance(story: StoryPlanningInput) -> bool:
    analysis = story.story.analysis
    text = " ".join(
        [
            story.story.canonical_title,
            analysis.development_summary,
            *analysis.technologies,
            *analysis.applications,
            *analysis.industries,
            *analysis.workflows,
        ]
    ).lower()
    return "ai" in text or bool(analysis.technologies)


def _unsupported_numerics(text: str, allowed_claim_text: str) -> list[str]:
    return [
        match
        for match in NUMERIC_PATTERN.findall(text)
        if match not in allowed_claim_text
    ]
