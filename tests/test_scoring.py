import unittest

from src.intelligence.models import AngleType, PotentialAngle, StoryAnalysis
from src.intelligence.scoring import score_angle
from src.shared.models import Audience


class ScoringTests(unittest.TestCase):
    def test_speculation_risk_reduces_editorial_score(self) -> None:
        analysis = StoryAnalysis(development_summary="Story")
        low_risk = _angle(speculation_risk=0.1)
        high_risk = _angle(speculation_risk=0.8)

        self.assertGreater(
            score_angle(low_risk, analysis).score,
            score_angle(high_risk, analysis).score,
        )

    def test_evidence_strength_increases_editorial_score(self) -> None:
        analysis = StoryAnalysis(development_summary="Story")
        weak = _angle(evidence_strength=0.2)
        strong = _angle(evidence_strength=0.9)

        self.assertGreater(
            score_angle(strong, analysis).score,
            score_angle(weak, analysis).score,
        )


def _angle(evidence_strength: float = 0.7, speculation_risk: float = 0.2) -> PotentialAngle:
    return PotentialAngle(
        id=f"angle-{evidence_strength}-{speculation_risk}",
        angle_type=AngleType.TECHNOLOGY,
        thesis="Technology angle",
        target_audiences=[Audience.ENTHUSIAST],
        evidence_strength=evidence_strength,
        relevance=0.7,
        novelty=0.7,
        usefulness=0.7,
        speculation_risk=speculation_risk,
        supporting_fact_ids=["fact-1"],
    )
