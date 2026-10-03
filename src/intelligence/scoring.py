from dataclasses import dataclass

from src.intelligence.angles import apply_career_upskill_gate
from src.intelligence.models import PotentialAngle, StoryAnalysis


@dataclass(frozen=True)
class ScoringWeights:
    """Transparent editorial scoring weights."""

    evidence: float = 0.32
    relevance: float = 0.22
    novelty: float = 0.16
    usefulness: float = 0.22
    speculation_penalty: float = 0.28


DEFAULT_WEIGHTS = ScoringWeights()


def score_angle(
    angle: PotentialAngle,
    analysis: StoryAnalysis,
    weights: ScoringWeights = DEFAULT_WEIGHTS,
) -> PotentialAngle:
    """Apply deterministic editorial scoring and gates."""

    angle = apply_career_upskill_gate(angle, analysis)
    raw_score = (
        angle.evidence_strength * weights.evidence
        + angle.relevance * weights.relevance
        + angle.novelty * weights.novelty
        + angle.usefulness * weights.usefulness
        - angle.speculation_risk * weights.speculation_penalty
    )
    angle.score = max(0.0, min(1.0, raw_score))
    if angle.score < 0.42 and not angle.rejected:
        angle.rejected = True
        angle.rejection_reason = "editorial score below threshold"
    return angle
