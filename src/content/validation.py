import re
from dataclasses import replace

from src.content.package_models import (
    PackageReviewState,
    PackageValidationResult,
    PackageValidationStatus,
    PlatformContentStatus,
    PublishableContentPackage,
    TitleVerificationStatus,
)
from src.intelligence.models import AngleType, ClaimKind, VerifiedGroundedStory


NUMERIC_PATTERN = re.compile(r"(?<![A-Za-z0-9])(?:[$]\d[\d,]*(?:\.\d+)?(?:\s+(?:million|billion|trillion))?|\d[\d,]*(?:\.\d+)?%|\d[\d,]*(?:\.\d+)?x|\d{4})(?![A-Za-z0-9])", re.IGNORECASE)


def validate_package(package: PublishableContentPackage, story: VerifiedGroundedStory) -> PackageValidationResult:
    issues: list[str] = []
    claim_ids = {claim.claim_id for claim in story.verified_claims}
    allowed = set(package.allowed_claim_ids)
    source_ids = {source.source_id for source in story.evidence_pack.sources}
    source_urls = {source.source_url for source in story.evidence_pack.sources}
    allowed_claim_text = " ".join(
        claim.text for claim in story.verified_claims if claim.claim_id in allowed
    )

    if not allowed or not allowed <= claim_ids:
        issues.append("allowed claim IDs must exist on verified story")
    _validate_claim_refs(package.canonical_draft.claim_references, allowed, issues, "canonical draft")
    for scene in package.reel.scenes:
        _validate_claim_refs(scene.supporting_claim_ids, allowed, issues, f"scene {scene.scene_id}")
        for source_id in scene.source_reference_ids:
            if source_id not in source_ids:
                issues.append(f"scene {scene.scene_id} references unknown source ID {source_id}")
    for source in package.source_references:
        if source.source_id not in source_ids:
            issues.append(f"invented source ID {source.source_id}")
        if source.source_url not in source_urls:
            issues.append(f"invented source URL {source.source_url}")
    if package.selected_angle.rejected:
        issues.append("rejected angle used")
    if (
        package.selected_angle.angle_type not in {AngleType.CAREER, AngleType.UPSKILL}
        and package.canonical_draft.career_upskill_implication
    ):
        issues.append("career/upskill content present without supported career/upskill angle")
    if package.human_decision.action.value != "approve":
        issues.append("package lacks human APPROVE decision")
    for label, text in _texts(package).items():
        unsupported = _unsupported_numerics(text, allowed_claim_text)
        if unsupported:
            issues.append(f"{label} contains unsupported numeric material: {', '.join(unsupported)}")
    for label, status in _platform_statuses(package).items():
        if status is PlatformContentStatus.FAILED:
            issues.append(f"{label} adaptation failed")
    for claim in story.verified_claims:
        if claim.claim_id in allowed and claim.claim_type is ClaimKind.INFERENCE:
            continue
    required_texts = _texts(package)
    for label, text in required_texts.items():
        if not text.strip():
            issues.append(f"{label} is empty")
    manual_title_issue = (
        package.selected_title.verification_status is TitleVerificationStatus.MANUAL_UNVERIFIED
        and not package.selected_title.manual_acknowledged
    )
    if manual_title_issue:
        issues.append("manual title requires final human acknowledgement")
    status = PackageValidationStatus.READY if not issues else PackageValidationStatus.NEEDS_REVIEW
    return PackageValidationResult(status=status, issues=issues, publish_ready=not issues)


def approve_for_render(package: PublishableContentPackage, story: VerifiedGroundedStory) -> PublishableContentPackage:
    validation = validate_package(package, story)
    if not validation.publish_ready:
        return replace(package, validation=validation, review_state=PackageReviewState.NEEDS_REVIEW)
    return replace(package, validation=validation, review_state=PackageReviewState.APPROVED_FOR_RENDER)


def _validate_claim_refs(refs: list[str], allowed: set[str], issues: list[str], label: str) -> None:
    for claim_id in refs:
        if claim_id not in allowed:
            issues.append(f"{label} references unsupported claim ID {claim_id}")


def _unsupported_numerics(text: str, allowed_claim_text: str) -> list[str]:
    unsupported = []
    for match in NUMERIC_PATTERN.findall(text):
        if match not in allowed_claim_text:
            unsupported.append(match)
    return unsupported


def _texts(package: PublishableContentPackage) -> dict[str, str]:
    return {
        "canonical hook": package.canonical_draft.hook,
        "canonical thesis": package.canonical_draft.thesis,
        "reel narration": package.reel.narration,
        "instagram caption": package.instagram.caption,
        "blog body": package.blog.body,
        "linkedin post": package.linkedin.post_copy,
        "x post": " ".join(package.x.posts),
        "tiktok caption": package.tiktok.caption,
        "youtube description": package.youtube_shorts.description,
    }


def _platform_statuses(package: PublishableContentPackage) -> dict[str, PlatformContentStatus]:
    return {
        "reel": package.reel.status,
        "instagram": package.instagram.status,
        "blog": package.blog.status,
        "linkedin": package.linkedin.status,
        "x": package.x.status,
        "tiktok": package.tiktok.status,
        "youtube_shorts": package.youtube_shorts.status,
    }
