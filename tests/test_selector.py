import unittest

from src.intelligence.models import (
    AnalyzedStory,
    EditorialOutcome,
    EvidenceSource,
    PotentialAngle,
    SourceType,
    StoryAnalysis,
    StoryCluster,
    AngleType,
)
from src.intelligence.selector import decide_story, select_stories
from src.shared.models import Audience
from tests.fixtures.intelligence_candidates import FOUNDATION_MODEL, HYPE_WEAK, ROBOTICS_COMPANY


class SelectorTests(unittest.TestCase):
    def test_strong_technology_angle_selected_without_career_content(self) -> None:
        story = _story("cluster-tech", FOUNDATION_MODEL, [_angle(AngleType.TECHNOLOGY, score=0.72)])

        decision = decide_story(story)

        self.assertEqual(decision.outcome, EditorialOutcome.SELECT)

    def test_low_evidence_hype_story_can_be_rejected(self) -> None:
        angle = _angle(AngleType.NEWS, score=0.2)
        angle.rejected = True
        angle.rejection_reason = "editorial score below threshold"
        story = _story("cluster-hype", HYPE_WEAK, [angle])

        decision = decide_story(story)

        self.assertEqual(decision.outcome, EditorialOutcome.REJECT)

    def test_duplicate_stories_do_not_consume_multiple_selected_slots(self) -> None:
        first = _story("cluster-one", ROBOTICS_COMPANY, [_angle(AngleType.TECHNOLOGY, score=0.8)])
        second = _story("cluster-two", FOUNDATION_MODEL, [_angle(AngleType.NEWS, score=0.7)])

        selected = select_stories([first, second], limit=1)

        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0][0].cluster.id, "cluster-one")

    def test_selection_does_not_enforce_domain_quotas(self) -> None:
        first = _story("cluster-software", FOUNDATION_MODEL, [_angle(AngleType.TECHNOLOGY, score=0.8)])
        second = _story("cluster-software-two", FOUNDATION_MODEL, [_angle(AngleType.NEWS, score=0.78)])

        selected = select_stories([first, second], limit=2)

        self.assertEqual(len(selected), 2)


def _angle(angle_type: AngleType, score: float) -> PotentialAngle:
    return PotentialAngle(
        id=f"angle-{angle_type.value}",
        angle_type=angle_type,
        thesis="Strong angle",
        target_audiences=[Audience.ENTHUSIAST],
        evidence_strength=0.8,
        relevance=0.8,
        novelty=0.8,
        usefulness=0.8,
        speculation_risk=0.1,
        supporting_fact_ids=["fact-1"],
        score=score,
    )


def _story(cluster_id, candidate, angles):
    return AnalyzedStory(
        cluster=StoryCluster(id=cluster_id, candidates=[candidate]),
        evidence_sources=[
            EvidenceSource(
                candidate_id=candidate.id,
                source_name=candidate.source_name,
                source_url=candidate.source_url,
                source_type=SourceType.NEWS,
                evidence_role=__import__("src.intelligence.models", fromlist=["EvidenceRole"]).EvidenceRole.SECONDARY,
                is_independent=True,
            )
        ],
        facts=[],
        analysis=StoryAnalysis(development_summary=candidate.title),
        angles=angles,
    )
