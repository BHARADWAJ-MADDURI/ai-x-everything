from datetime import datetime, timezone

from dashboard.demo_data import DashboardData
from src.content.package_generator import ContentPackageGenerator
from src.content.package_models import PublishableContentPackage, SelectedTitle, TitleVerificationStatus
from src.content.package_schemas import CanonicalContentDraftOutput
from src.editorial.decisions import record_human_decision
from src.editorial.models import HumanDecisionAction, RecommendedPost
from src.generation.llm_client import LLMResult


def has_approve_decision(decision_log: list, story_id: str) -> bool:
    return any(
        entry.decision.action is HumanDecisionAction.APPROVE and entry.decision.target_id == story_id
        for entry in decision_log
    )


def generate_session_package(data: DashboardData, post: RecommendedPost) -> PublishableContentPackage:
    story = next(item.story for item in data.stories if item.story_id == post.story_id)
    title_candidate = data.title_candidates_by_story.get(post.story_id or "", [None])[0]
    title = SelectedTitle(
        text=title_candidate.text if title_candidate else story.canonical_title,
        verification_status=TitleVerificationStatus.GROUNDED,
        supporting_claim_ids=list(post.selected_angle.supporting_fact_ids),
    )
    decision = record_human_decision(
        action=HumanDecisionAction.APPROVE,
        target_id=story.cluster_id,
        decided_at=datetime.now(timezone.utc),
        comment="approved in dashboard session for content package generation",
    )
    hashtags = data.hashtag_candidates_by_story.get(post.story_id or "", [])
    return ContentPackageGenerator(
        llm_client=DashboardPackageLLMClient(post.selected_angle.supporting_fact_ids)
    ).generate(
        story=story,
        decision=decision,
        selected_angle=post.selected_angle,
        selected_title=title,
        selected_hashtags=hashtags,
    )


class DashboardPackageLLMClient:
    def __init__(self, claim_ids: list[str]) -> None:
        self.claim_ids = list(claim_ids)

    def generate_structured(self, *, system_prompt, user_prompt, response_schema):
        claim_refs = self.claim_ids[:1]
        output = response_schema.model_validate(
            {
                "hook": "This story is ready for a grounded content package.",
                "thesis": "The approved angle is based on the selected verified claim.",
                "key_points": ["The package reuses the approved story, angle, title, and hashtags."],
                "technical_explanation": "The canonical draft is adapted across platforms without adding new facts.",
                "human_implication": "The editor still needs final package review before rendering.",
                "career_upskill_implication": None,
                "takeaway": "Generation creates a draft package, not an automatic publication.",
                "cta": "Follow Everything × AI to understand what's changing.",
                "claim_references": claim_refs,
            }
        )
        return LLMResult(
            output=output,
            model="dashboard-fake-package-model",
            provider="fake",
            latency_ms=4,
            input_tokens=60,
            output_tokens=90,
            estimated_cost_usd=None,
        )


def package_summary(package: PublishableContentPackage) -> list[str]:
    return [
        f"Package: {package.package_id}",
        f"Title: {package.selected_title.text}",
        f"Reel scenes: {len(package.reel.scenes)}",
        f"Instagram hashtags: {', '.join(tag.tag for tag in package.instagram.hashtags) or 'none'}",
        f"Validation: {package.validation.status.value if package.validation else 'unknown'}",
        f"Review state: {package.review_state.value}",
    ]
