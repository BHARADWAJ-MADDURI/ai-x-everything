from src.intelligence.angles import apply_career_upskill_gate
from src.intelligence.models import (
    AngleType,
    ClaimKind,
    EvidencePack,
    PotentialAngle,
    StoryAnalysis,
    ValidationFailure,
    VerifiedClaimCandidate,
    VerifiedGroundedStory,
    VerifiedStoryAnalysis,
)


def build_verified_analysis(
    raw_analysis: StoryAnalysis,
    valid_claims: list[VerifiedClaimCandidate],
) -> VerifiedStoryAnalysis:
    """Build analysis fields only when at least one validated claim exists."""

    if not valid_claims:
        return VerifiedStoryAnalysis(
            development_summary="UNKNOWN",
            uncertainties=["Insufficient validated evidence."],
        )
    claim_text = " ".join(claim.text.lower() for claim in valid_claims)
    return VerifiedStoryAnalysis(
        development_summary=raw_analysis.development_summary if raw_analysis.development_summary else "UNKNOWN",
        technologies=_keep_if_supported(raw_analysis.technologies, claim_text),
        applications=_keep_if_supported(raw_analysis.applications, claim_text),
        industries=_keep_if_supported(raw_analysis.industries, claim_text),
        workflows=_keep_if_supported(raw_analysis.workflows, claim_text),
        professions=_keep_if_supported(raw_analysis.professions, claim_text),
        demonstrated_capabilities=raw_analysis.demonstrated_capabilities,
        limitations=raw_analysis.limitations,
        uncertainties=raw_analysis.uncertainties,
        verified_claim_ids=[claim.claim_id for claim in valid_claims],
    )


def validate_angles(
    angles: list[PotentialAngle],
    valid_claims: list[VerifiedClaimCandidate],
    analysis: VerifiedStoryAnalysis,
) -> list[PotentialAngle]:
    """Allow angles to reference only validated claims from this story."""

    valid_ids = {claim.claim_id for claim in valid_claims}
    story_analysis = StoryAnalysis(
        development_summary=analysis.development_summary,
        technologies=analysis.technologies,
        applications=analysis.applications,
        industries=analysis.industries,
        workflows=analysis.workflows,
        professions=analysis.professions,
        demonstrated_capabilities=analysis.demonstrated_capabilities,
        limitations=analysis.limitations,
        uncertainties=analysis.uncertainties,
    )
    validated = []
    for angle in angles:
        if any(fact_id not in valid_ids for fact_id in angle.supporting_fact_ids):
            angle.rejected = True
            angle.rejection_reason = "angle references unverified claim"
        if angle.angle_type in {AngleType.CAREER, AngleType.UPSKILL}:
            apply_career_upskill_gate(angle, story_analysis)
        validated.append(angle)
    return validated


def build_verified_grounded_story(
    *,
    evidence_pack: EvidencePack,
    raw_analysis: StoryAnalysis,
    valid_claims: list[VerifiedClaimCandidate],
    rejected_claims: list[ValidationFailure],
    angles: list[PotentialAngle],
) -> VerifiedGroundedStory:
    """Create the final verified story boundary for downstream generation."""

    verified_analysis = build_verified_analysis(raw_analysis, valid_claims)
    validated_angles = validate_angles(angles, valid_claims, verified_analysis)
    return VerifiedGroundedStory(
        cluster_id=evidence_pack.cluster_id,
        canonical_title=evidence_pack.canonical_title,
        evidence_pack=evidence_pack,
        verified_claims=valid_claims,
        rejected_claims=rejected_claims,
        analysis=verified_analysis,
        validated_angles=[angle for angle in validated_angles if not angle.rejected],
    )


def _keep_if_supported(values: list[str], claim_text: str) -> list[str]:
    kept = []
    for value in values:
        if value.lower() in claim_text:
            kept.append(value)
    return kept
