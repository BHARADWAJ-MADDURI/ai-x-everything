from datetime import datetime, timezone

from src.content.package_generator import ContentPackageGenerator
from src.content.package_models import SelectedTitle, TitleVerificationStatus
from src.content.package_schemas import CanonicalContentDraftOutput
from src.editorial.decisions import record_human_decision
from src.editorial.demo_fixture import busy_news_day_fixture
from src.editorial.models import HumanDecisionAction
from src.generation.llm_client import LLMResult
from src.intelligence.models import (
    HashtagCandidate,
    HashtagResearchStatus,
    HashtagSource,
    TargetPlatform,
)


PACKAGE_DEMO_NOW = datetime(2026, 10, 3, 13, 0, tzinfo=timezone.utc)


def deterministic_content_package_demo():
    stories, _evergreen = busy_news_day_fixture()
    story_input = stories[0]
    story = story_input.story
    angle = story.validated_angles[0]
    claim_ids = list(angle.supporting_fact_ids)
    title = SelectedTitle(
        text=story.canonical_title,
        verification_status=TitleVerificationStatus.GROUNDED,
        supporting_claim_ids=claim_ids,
    )
    decision = record_human_decision(
        action=HumanDecisionAction.APPROVE,
        target_id=story.cluster_id,
        decided_at=PACKAGE_DEMO_NOW,
        comment="approved for package demo",
    )
    return ContentPackageGenerator(llm_client=DeterministicPackageLLMClient()).generate(
        story=story,
        decision=decision,
        selected_angle=angle,
        selected_title=title,
        selected_hashtags=[
            HashtagCandidate(
                tag="#RoboticsAI",
                relevance_score=0.82,
                specificity_score=0.76,
                source=HashtagSource.VERIFIED_STORY,
                research_status=HashtagResearchStatus.UNRESEARCHED,
                platform=TargetPlatform.INSTAGRAM,
                estimated_reach_band=None,
                competition_band=None,
                supporting_topic_terms=["robotics"],
            )
        ],
    )


class DeterministicPackageLLMClient:
    def generate_structured(self, *, system_prompt, user_prompt, response_schema):
        output = response_schema.model_validate(
            {
                "hook": "A robotics release is worth watching because the evidence is specific.",
                "thesis": "Major robotics release has verified evidence in robotics.",
                "key_points": ["The story is grounded in a verified claim."],
                "technical_explanation": "The useful angle is how robotics capabilities are being framed for real workflows.",
                "human_implication": "Teams should watch what the technology can actually support before generalizing.",
                "career_upskill_implication": None,
                "takeaway": "The strongest package stays close to the verified claim and avoids inflated deployment claims.",
                "cta": "Follow Everything × AI to understand what's changing.",
                "claim_references": ["robotics-release-claim"],
            }
        )
        return LLMResult(
            output=output,
            model="fake-content-package-model",
            provider="fake",
            latency_ms=7,
            input_tokens=80,
            output_tokens=120,
            estimated_cost_usd=None,
        )
