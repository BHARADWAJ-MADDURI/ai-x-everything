import unittest

from src.intelligence.angles import apply_career_upskill_gate, generate_angles
from src.intelligence.models import AngleType, GroundedFact, PotentialAngle, StoryAnalysis
from src.shared.models import Audience


class AngleTests(unittest.TestCase):
    def test_potential_story_can_have_no_career_or_upskill_angle(self) -> None:
        analysis = StoryAnalysis(
            development_summary="A general model update was announced.",
            technologies=["language model"],
        )
        angles = generate_angles(analysis, [_fact()], 0.7)
        angle_types = {angle.angle_type for angle in angles}

        self.assertNotIn(AngleType.CAREER, angle_types)
        self.assertNotIn(AngleType.UPSKILL, angle_types)

    def test_strong_career_angle_survives_when_evidence_chain_exists(self) -> None:
        analysis = StoryAnalysis(
            development_summary="Robotics affects maintenance diagnostics.",
            workflows=["maintenance diagnostics"],
            professions=["maintenance technician"],
        )
        angle = PotentialAngle(
            id="career",
            angle_type=AngleType.CAREER,
            thesis="Maintenance technicians may use diagnostics tools.",
            target_audiences=[Audience.PROFESSIONAL],
            evidence_strength=0.8,
            relevance=0.8,
            novelty=0.6,
            usefulness=0.8,
            speculation_risk=0.3,
            supporting_fact_ids=["fact-1"],
        )

        gated = apply_career_upskill_gate(angle, analysis)

        self.assertFalse(gated.rejected)

    def test_weak_career_angle_rejected_when_chain_missing(self) -> None:
        analysis = StoryAnalysis(development_summary="A model was announced.")
        angle = PotentialAngle(
            id="career",
            angle_type=AngleType.CAREER,
            thesis="Farmers should learn Python.",
            target_audiences=[Audience.PROFESSIONAL],
            evidence_strength=0.8,
            relevance=0.6,
            novelty=0.6,
            usefulness=0.6,
            speculation_risk=0.3,
            supporting_fact_ids=["fact-1"],
        )

        gated = apply_career_upskill_gate(angle, analysis)

        self.assertTrue(gated.rejected)

    def test_weak_upskill_angle_rejected_when_unsupported(self) -> None:
        analysis = StoryAnalysis(
            development_summary="A model was announced.",
            workflows=["maintenance diagnostics"],
            professions=["maintenance technician"],
        )
        angle = PotentialAngle(
            id="upskill",
            angle_type=AngleType.UPSKILL,
            thesis="Learn unrelated ML engineering.",
            target_audiences=[Audience.STUDENT],
            evidence_strength=0.3,
            relevance=0.8,
            novelty=0.6,
            usefulness=0.7,
            speculation_risk=0.2,
            supporting_fact_ids=["fact-1"],
        )

        gated = apply_career_upskill_gate(angle, analysis)

        self.assertTrue(gated.rejected)

    def test_audience_targeting_supports_core_audiences(self) -> None:
        angle = generate_angles(StoryAnalysis(development_summary="News"), [_fact()], 0.7)[0]

        self.assertIn(Audience.STUDENT, angle.target_audiences)
        self.assertIn(Audience.PROFESSIONAL, angle.target_audiences)
        self.assertIn(Audience.ENTHUSIAST, angle.target_audiences)


def _fact() -> GroundedFact:
    from src.intelligence.models import ClaimKind, FactType

    return GroundedFact(
        id="fact-1",
        claim="A company announced a model.",
        supporting_source_urls=["https://example.com"],
        confidence=0.8,
        fact_type=FactType.ANNOUNCEMENT,
        claim_kind=ClaimKind.FACT,
    )
