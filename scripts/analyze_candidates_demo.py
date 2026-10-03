from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.intelligence.models import EditorialOutcome
from src.intelligence.evidence import build_evidence_pack
from src.intelligence.hashtags import select_hashtags, unresearched_hashtag_candidates
from src.intelligence.models import AngleType, ClaimKind, PotentialAngle, TargetPlatform, VerifiedClaimCandidate
from src.intelligence.pipeline import run_intelligence_pipeline
from src.intelligence.titles import generate_title_candidates, validate_title
from src.intelligence.validation import validate_claims
from src.intelligence.verified import build_verified_grounded_story
from src.shared.models import Audience
from tests.fixtures.intelligence_candidates import ALL_CANDIDATES


def main() -> None:
    result = run_intelligence_pipeline(ALL_CANDIDATES)
    story = result.analyzed_stories[0]
    decision = result.decisions[story.cluster.id]
    evidence_pack = build_evidence_pack(story.cluster)
    claims = [
        VerifiedClaimCandidate(
            claim_id="claim_001",
            text=evidence_pack.evidence_items[0].supplied_text,
            claim_type=ClaimKind.FACT,
            evidence_ids=[evidence_pack.evidence_items[0].evidence_id],
            referenced_source_ids=[evidence_pack.sources[0].source_id],
        ),
        VerifiedClaimCandidate(
            claim_id="claim_002",
            text="Multiple sources cover the same robotics development.",
            claim_type=ClaimKind.INFERENCE,
            evidence_ids=[item.evidence_id for item in evidence_pack.evidence_items],
        ),
        VerifiedClaimCandidate(
            claim_id="claim_bad",
            text="The system improved factory inspection by 40%.",
            claim_type=ClaimKind.FACT,
            evidence_ids=[evidence_pack.evidence_items[0].evidence_id],
            numeric_claim=True,
        ),
    ]
    validation = validate_claims(claims, evidence_pack)
    verified_story = build_verified_grounded_story(
        evidence_pack=evidence_pack,
        raw_analysis=story.analysis,
        valid_claims=validation.valid_claims,
        rejected_claims=validation.rejected_claims,
        angles=[
            PotentialAngle(
                id="verified-tech-angle",
                angle_type=AngleType.TECHNOLOGY,
                thesis="How vision, language, and robot action connect in this robotics development.",
                target_audiences=[Audience.STUDENT, Audience.PROFESSIONAL, Audience.ENTHUSIAST],
                evidence_strength=0.8,
                relevance=0.8,
                novelty=0.7,
                usefulness=0.75,
                speculation_risk=0.2,
                supporting_fact_ids=["claim_001"],
            ),
            *story.angles,
        ],
    )
    titles = generate_title_candidates(verified_story, target_platform=TargetPlatform.INSTAGRAM)
    hashtag_candidates = unresearched_hashtag_candidates(verified_story, TargetPlatform.INSTAGRAM)
    selected_hashtags = select_hashtags(hashtag_candidates, limit=5)

    print("STORY")
    print("-----")
    print(f"cluster ID: {story.cluster.id}")
    print(f"title: {story.cluster.title}")
    print()
    print("verified facts")
    for claim in verified_story.verified_claims:
        if claim.claim_type is ClaimKind.FACT:
            print(f"- {claim.claim_id}: {claim.text}")
            print(f"  evidence: {', '.join(claim.evidence_ids)}")
    print()
    print("inferences")
    for claim in verified_story.verified_claims:
        if claim.claim_type is ClaimKind.INFERENCE:
            print(f"- {claim.claim_id}: {claim.text}")
    print()
    print("unknowns")
    print("- professions: UNKNOWN" if not verified_story.analysis.professions else "- professions: known")
    print()
    print("rejected claims + reasons")
    for failure in verified_story.rejected_claims:
        print(f"- {failure.item_id}: {failure.reason}")
    print()
    print("ANGLES")
    print("------")
    print("selected angles")
    for angle in verified_story.validated_angles:
        print(f"- {angle.angle_type.name}: {angle.thesis}")
    print("rejected career/upskill angle if unsupported")
    unsupported = [
        angle
        for angle in story.angles
        if angle.angle_type in {AngleType.CAREER, AngleType.UPSKILL} and angle.rejected
    ]
    print(unsupported[0].rejection_reason if unsupported else "none in this verified story")
    print()
    print("TITLE CANDIDATES")
    print("----------------")
    for index, title in enumerate(titles, start=1):
        validated, failure = validate_title(title, verified_story)
        print(f"{index}.")
        print(f"title: {validated.text}")
        print(f"supported claims: {', '.join(validated.supported_claim_ids)}")
        print(f"status: {'REJECTED - ' + failure.reason if failure else 'VALID'}")
    print()
    print("HASHTAG CANDIDATES")
    print("------------------")
    for tag in selected_hashtags:
        print(f"tag: {tag.tag}")
        print(f"relevance: {tag.relevance_score:.2f}")
        print(f"research status: {tag.research_status.name}")
        print(f"reach: {tag.estimated_reach_band or 'UNKNOWN'}")
        print(f"selection: {'SELECTED' if tag.selected else 'HOLD'}")
    print()
    print("EDITORIAL DECISION:")
    print(decision.outcome.name)
    if decision.outcome is not EditorialOutcome.SELECT:
        print("reason: " + "; ".join(decision.reasons))


if __name__ == "__main__":
    main()
