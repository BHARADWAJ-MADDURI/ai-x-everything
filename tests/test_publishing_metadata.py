import unittest

from src.intelligence.models import AngleType, PotentialAngle, TargetPlatform
from src.intelligence.publishing import create_publishing_metadata
from src.intelligence.titles import generate_title_candidates
from src.shared.models import Audience
from tests.test_hashtags import _tag
from tests.test_titles import _verified_story


class PublishingMetadataTests(unittest.TestCase):
    def test_publishing_metadata_can_be_created(self) -> None:
        story = _verified_story()
        metadata = create_publishing_metadata(
            story,
            titles=generate_title_candidates(story, target_platform=TargetPlatform.INSTAGRAM),
            hashtags=[_tag("#industrialrobotics", 0.9, None)],
            selected_angle=PotentialAngle(
                id="angle-tech",
                angle_type=AngleType.TECHNOLOGY,
                thesis="Explain visual inspection assistance.",
                target_audiences=[Audience.ENTHUSIAST],
                evidence_strength=0.8,
                relevance=0.8,
                novelty=0.6,
                usefulness=0.8,
                speculation_risk=0.2,
                supporting_fact_ids=["claim_001"],
            ),
            target_platform=TargetPlatform.INSTAGRAM,
        )

        self.assertEqual(metadata.target_platform, TargetPlatform.INSTAGRAM)
        self.assertTrue(metadata.selected_hashtags)
