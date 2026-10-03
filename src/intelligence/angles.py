from src.intelligence.models import AngleType, ClaimKind, GroundedFact, PotentialAngle, StoryAnalysis
from src.shared.models import Audience


CAREER_MIN_EVIDENCE = 0.62
CAREER_MAX_SPECULATION = 0.45


def generate_angles(analysis: StoryAnalysis, facts: list[GroundedFact], evidence_strength: float) -> list[PotentialAngle]:
    """Create defensible potential angles without forcing career/upskill."""

    fact_ids = [fact.id for fact in facts if fact.claim_kind is ClaimKind.FACT]
    weak_hype = _has_weak_hype_signal(analysis)
    angles = [
        PotentialAngle(
            id="angle-news",
            angle_type=AngleType.NEWS,
            thesis=analysis.development_summary,
            target_audiences=[Audience.STUDENT, Audience.PROFESSIONAL, Audience.ENTHUSIAST],
            evidence_strength=evidence_strength,
            relevance=0.42 if weak_hype else 0.72,
            novelty=0.35 if weak_hype else 0.65,
            usefulness=0.35 if weak_hype else 0.62,
            speculation_risk=0.75 if weak_hype else 0.2,
            supporting_fact_ids=fact_ids,
            rationale="Grounded summary has enough evidence for a news/update angle.",
        )
    ]
    if analysis.technologies:
        angles.append(
            PotentialAngle(
                id="angle-technology",
                angle_type=AngleType.TECHNOLOGY,
                thesis=f"How {' and '.join(analysis.technologies[:2])} relates to this development.",
                target_audiences=[Audience.STUDENT, Audience.ENTHUSIAST],
                evidence_strength=evidence_strength,
                relevance=0.8,
                novelty=0.72,
                usefulness=0.75,
                speculation_risk=0.25,
                supporting_fact_ids=fact_ids,
                rationale="Technology involved is identifiable from the grounded material.",
            )
        )
    if analysis.industries:
        angles.append(
            PotentialAngle(
                id="angle-industry",
                angle_type=AngleType.INDUSTRY_IMPACT,
                thesis=f"Where this may matter in {analysis.industries[0]}.",
                target_audiences=[Audience.PROFESSIONAL, Audience.ENTHUSIAST],
                evidence_strength=evidence_strength,
                relevance=0.76,
                novelty=0.65,
                usefulness=0.78,
                speculation_risk=0.35,
                supporting_fact_ids=fact_ids,
                rationale="Industry connection is present in analysis.",
            )
        )
    if analysis.limitations:
        angles.append(
            PotentialAngle(
                id="angle-risk",
                angle_type=AngleType.RISK_LIMITATION,
                thesis="What remains uncertain or limited.",
                target_audiences=[Audience.STUDENT, Audience.PROFESSIONAL, Audience.ENTHUSIAST],
                evidence_strength=evidence_strength,
                relevance=0.7,
                novelty=0.55,
                usefulness=0.5 if weak_hype else 0.82,
                speculation_risk=0.55 if weak_hype else 0.18,
                supporting_fact_ids=fact_ids,
                rationale="Limitations are explicitly present.",
            )
        )

    angles.extend(_career_and_upskill_angles(analysis, fact_ids, evidence_strength))
    return angles


def _has_weak_hype_signal(analysis: StoryAnalysis) -> bool:
    text = " ".join([analysis.development_summary, *analysis.limitations, *analysis.uncertainties]).lower()
    return any(signal in text for signal in ("hype", "weakly supported", "insufficient", "revolutionize"))


def _career_and_upskill_angles(
    analysis: StoryAnalysis,
    fact_ids: list[str],
    evidence_strength: float,
) -> list[PotentialAngle]:
    has_chain = bool(analysis.workflows and analysis.professions and fact_ids)
    speculation_risk = 0.3 if has_chain else 0.75
    if not has_chain:
        return []
    return [
        PotentialAngle(
            id="angle-career",
            angle_type=AngleType.CAREER,
            thesis=f"How {analysis.professions[0]} work may be affected.",
            target_audiences=[Audience.PROFESSIONAL, Audience.STUDENT],
            evidence_strength=evidence_strength,
            relevance=0.78,
            novelty=0.62,
            usefulness=0.82,
            speculation_risk=speculation_risk,
            supporting_fact_ids=fact_ids,
            rationale="Workflow and profession are both connected by grounded evidence.",
        ),
        PotentialAngle(
            id="angle-upskill",
            angle_type=AngleType.UPSKILL,
            thesis=f"Complementary skills around {analysis.workflows[0]} may become useful.",
            target_audiences=[Audience.PROFESSIONAL, Audience.STUDENT],
            evidence_strength=evidence_strength,
            relevance=0.72,
            novelty=0.58,
            usefulness=0.8,
            speculation_risk=speculation_risk,
            supporting_fact_ids=fact_ids,
            rationale="Upskill framing preserves existing domain expertise and follows the workflow evidence.",
        ),
    ]


def apply_career_upskill_gate(angle: PotentialAngle, analysis: StoryAnalysis) -> PotentialAngle:
    """Reject unsupported career/upskill angles deterministically."""

    if angle.angle_type not in {AngleType.CAREER, AngleType.UPSKILL}:
        return angle
    has_chain = bool(analysis.workflows and analysis.professions and angle.supporting_fact_ids)
    if not has_chain:
        angle.rejected = True
        angle.rejection_reason = "missing workflow/profession/evidence chain"
    elif angle.evidence_strength < CAREER_MIN_EVIDENCE:
        angle.rejected = True
        angle.rejection_reason = "career/upskill evidence strength below threshold"
    elif angle.speculation_risk > CAREER_MAX_SPECULATION:
        angle.rejected = True
        angle.rejection_reason = "career/upskill speculation risk too high"
    return angle
