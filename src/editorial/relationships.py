from src.editorial.models import BundleCandidate, StoryRelationship, StoryRelationshipType, StoryPlanningInput


def infer_story_relationships(stories: list[StoryPlanningInput]) -> list[StoryRelationship]:
    """Create lightweight relationship hints without merging stories."""

    relationships: list[StoryRelationship] = []
    for left_index, left in enumerate(stories):
        for right in stories[left_index + 1:]:
            overlap = _term_overlap(_story_terms(left), _story_terms(right))
            if overlap < 0.34:
                continue
            relationship_type = (
                StoryRelationshipType.SAME_TREND
                if overlap >= 0.55
                else StoryRelationshipType.RELATED_TECHNOLOGY
            )
            relationships.append(
                StoryRelationship(
                    left_story_id=left.story_id,
                    right_story_id=right.story_id,
                    relationship_type=relationship_type,
                    strength=round(overlap, 3),
                    rationale="Stories share specific technologies, workflows, or applications.",
                )
            )
    return relationships


def bundle_candidates(
    stories: list[StoryPlanningInput],
    relationships: list[StoryRelationship],
) -> list[BundleCandidate]:
    by_id = {story.story_id: story for story in stories}
    bundles: list[BundleCandidate] = []
    for index, relationship in enumerate(relationships, start=1):
        if relationship.strength < 0.55:
            continue
        left = by_id[relationship.left_story_id]
        right = by_id[relationship.right_story_id]
        if min(left.editorial_score, right.editorial_score) < 0.68:
            continue
        claim_refs = {
            left.story_id: _claim_refs(left),
            right.story_id: _claim_refs(right),
        }
        bundles.append(
            BundleCandidate(
                bundle_id=f"bundle-{index:03d}",
                story_ids=[left.story_id, right.story_id],
                proposed_thesis=f"{left.story.canonical_title} and {right.story.canonical_title} point to a broader AI trend.",
                relationship_type=relationship.relationship_type,
                coherence_score=relationship.strength,
                editorial_value=round((left.editorial_score + right.editorial_score) / 2, 3),
                rationale="Bundle only as a broader-trend interpretation; story claims remain separate.",
                claim_refs_by_story=claim_refs,
            )
        )
    return bundles


def _story_terms(story_input: StoryPlanningInput) -> set[str]:
    analysis = story_input.story.analysis
    values = [
        *analysis.technologies,
        *analysis.applications,
        *analysis.industries,
        *analysis.workflows,
        *analysis.professions,
    ]
    if story_input.domain:
        values.append(story_input.domain)
    return {value.lower() for value in values if value}


def _term_overlap(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / min(len(left), len(right))


def _claim_refs(story_input: StoryPlanningInput) -> list[str]:
    return [claim.claim_id for claim in story_input.story.verified_claims]
