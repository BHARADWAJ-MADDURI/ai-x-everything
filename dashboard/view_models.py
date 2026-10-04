from dataclasses import dataclass
from datetime import datetime

from dashboard.demo_data import DashboardData
from src.editorial.decisions import record_human_decision
from src.editorial.models import (
    BundleCandidate,
    DailyContentPlan,
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
    return "No published metrics recorded yet."


def bundle_story_sections(bundle: BundleCandidate, stories: list[StoryPlanningInput]) -> dict[str, list[str]]:
    story_map = {story.story_id: story for story in stories}
    return {
        story_id: [claim.claim_id for claim in story_map[story_id].story.verified_claims]
        for story_id in bundle.story_ids
        if story_id in story_map
    }
