from src.intelligence.models import AnalyzedStory, EditorialDecision, EditorialOutcome, PotentialAngle


def decide_story(story: AnalyzedStory, min_select_score: float = 0.58) -> EditorialDecision:
    """Return SELECT/HOLD/REJECT for an analyzed story."""

    viable = [angle for angle in story.angles if not angle.rejected]
    viable.sort(key=lambda angle: angle.score or 0.0, reverse=True)
    if viable and (viable[0].score or 0.0) >= min_select_score:
        return EditorialDecision(
            outcome=EditorialOutcome.SELECT,
            reasons=["strongest angle meets editorial threshold"],
            selected_angles=viable[:3],
        )
    if viable:
        return EditorialDecision(
            outcome=EditorialOutcome.HOLD,
            reasons=["some viable angles exist but score is not yet strong"],
            selected_angles=viable[:2],
        )
    return EditorialDecision(
        outcome=EditorialOutcome.REJECT,
        reasons=["no viable evidence-backed angles"],
        selected_angles=[],
    )


def select_stories(stories: list[AnalyzedStory], limit: int = 3) -> list[tuple[AnalyzedStory, EditorialDecision]]:
    """Select strongest non-duplicate story clusters by editorial value."""

    decisions = [(story, decide_story(story)) for story in stories]
    selected = [item for item in decisions if item[1].outcome is EditorialOutcome.SELECT]
    selected.sort(key=lambda item: _best_score(item[1].selected_angles), reverse=True)
    return selected[:limit]


def _best_score(angles: list[PotentialAngle]) -> float:
    if not angles:
        return 0.0
    return max(angle.score or 0.0 for angle in angles)
