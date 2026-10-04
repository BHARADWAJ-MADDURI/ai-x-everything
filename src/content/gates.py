from src.content.package_models import GenerationReadinessResult, SelectedTitle, TitleVerificationStatus
from src.editorial.models import HumanDecisionAction, HumanEditorialDecision
from src.intelligence.models import PotentialAngle, VerifiedGroundedStory


def generation_readiness(
    *,
    story: VerifiedGroundedStory,
    decision: HumanEditorialDecision,
    selected_angle: PotentialAngle,
    selected_title: SelectedTitle,
) -> GenerationReadinessResult:
    issues = []
    if decision.action is not HumanDecisionAction.APPROVE:
        issues.append(f"human decision is {decision.action.value}, not approve")
    if selected_angle.rejected:
        issues.append("selected angle is rejected")
    if selected_angle not in story.validated_angles:
        issues.append("selected angle is not validated for this story")
    if not story.verified_claims:
        issues.append("story has no verified claims")
    if not story.evidence_pack.sources or not story.evidence_pack.evidence_items:
        issues.append("required provenance is missing")
    claim_ids = {claim.claim_id for claim in story.verified_claims}
    allowed = [claim_id for claim_id in selected_angle.supporting_fact_ids if claim_id in claim_ids]
    if not allowed:
        issues.append("selected angle has no allowed verified claim references")
    if selected_title.verification_status is TitleVerificationStatus.GROUNDED:
        missing_title_claims = [claim_id for claim_id in selected_title.supporting_claim_ids if claim_id not in claim_ids]
        if missing_title_claims:
            issues.append("grounded title references unknown claims")
    return GenerationReadinessResult(
        ready=not issues,
        issues=issues,
        allowed_claim_ids=allowed,
    )
