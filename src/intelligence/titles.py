from src.intelligence.models import (
    TargetPlatform,
    TitleCandidate,
    TitleType,
    ValidationFailure,
    VerifiedGroundedStory,
)


HYPE_PHRASES = (
    "changes everything",
    "will replace",
    "revolutionary",
    "game-changing",
    "the end of",
    "you need to",
    "eliminates",
)


def generate_title_candidates(
    story: VerifiedGroundedStory,
    *,
    target_platform: TargetPlatform | None = None,
) -> list[TitleCandidate]:
    """Generate a small deterministic set of grounded title candidates."""

    claim_ids = [claim.claim_id for claim in story.verified_claims]
    base = story.analysis.development_summary
    titles = [
        TitleCandidate(base, TitleType.NEWS, claim_ids[:1], target_platform, 0.55, 0.8, 0.15),
        TitleCandidate(f"How {base}", TitleType.EXPLAINER, claim_ids[:2] or claim_ids[:1], target_platform, 0.65, 0.75, 0.2),
    ]
    if story.analysis.industries:
        titles.append(
            TitleCandidate(
                f"How AI could affect {story.analysis.industries[0]}",
                TitleType.IMPACT,
                claim_ids[:2] or claim_ids[:1],
                target_platform,
                0.7,
                0.72,
                0.3,
            )
        )
    return titles[:5]


def validate_title(candidate: TitleCandidate, story: VerifiedGroundedStory) -> tuple[TitleCandidate, ValidationFailure | None]:
    """Reject title candidates unsupported by verified claims."""

    verified_ids = {claim.claim_id for claim in story.verified_claims}
    if not candidate.supported_claim_ids:
        candidate.rejected = True
        candidate.rejection_reason = "title lacks supporting verified claim IDs"
    elif any(claim_id not in verified_ids for claim_id in candidate.supported_claim_ids):
        candidate.rejected = True
        candidate.rejection_reason = "title references unknown verified claim ID"
    elif any(phrase in candidate.text.lower() for phrase in HYPE_PHRASES):
        candidate.rejected = True
        candidate.rejection_reason = "title contains unsupported hype or certainty"
    if candidate.rejected:
        return candidate, ValidationFailure(candidate.text, candidate.rejection_reason or "invalid title")
    return candidate, None
