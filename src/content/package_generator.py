from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from src.content.adapters import (
    build_blog_package,
    build_instagram_package,
    build_linkedin_package,
    build_reel_package,
    build_tiktok_package,
    build_x_package,
    build_youtube_shorts_package,
)
from src.content.gates import generation_readiness
from src.content.package_models import (
    CanonicalContentDraft,
    PublishableContentPackage,
    SelectedTitle,
    SourceReference,
)
from src.content.package_schemas import CanonicalContentDraftOutput
from src.content.validation import validate_package
from src.editorial.models import HumanEditorialDecision
from src.generation.llm_client import LLMResult, OpenAILLMClient
from src.intelligence.models import HashtagCandidate, PotentialAngle, VerifiedGroundedStory
from src.shared.models import GenerationMetadata


PROMPT_VERSION = "canonical_content_v1"
PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "canonical_content_v1.txt"


class ContentPackageGenerationError(Exception):
    """Raised when generation inputs fail the approval/grounding gate."""


class ContentPackageGenerator:
    """Generate a grounded package from one approved verified story and angle."""

    def __init__(self, llm_client: OpenAILLMClient | None = None) -> None:
        self.llm_client = llm_client

    def generate(
        self,
        *,
        story: VerifiedGroundedStory,
        decision: HumanEditorialDecision,
        selected_angle: PotentialAngle,
        selected_title: SelectedTitle,
        selected_hashtags: list[HashtagCandidate],
    ) -> PublishableContentPackage:
        readiness = generation_readiness(
            story=story,
            decision=decision,
            selected_angle=selected_angle,
            selected_title=selected_title,
        )
        if not readiness.ready:
            raise ContentPackageGenerationError("; ".join(readiness.issues))
        result = self._generate_canonical_draft(
            story=story,
            selected_angle=selected_angle,
            allowed_claim_ids=readiness.allowed_claim_ids,
        )
        draft = _draft_from_output(result.output)
        source_references = _source_references(story)
        source_ids = [source.source_id for source in source_references]
        package = PublishableContentPackage(
            package_id=f"package-{uuid4()}",
            story_id=story.cluster_id,
            cluster_id=story.cluster_id,
            created_at=datetime.now(UTC),
            selected_angle=selected_angle,
            audience=list(selected_angle.target_audiences),
            selected_title=selected_title,
            human_decision=decision,
            allowed_claim_ids=readiness.allowed_claim_ids,
            source_references=source_references,
            evidence_reference_ids=[
                item.evidence_id
                for item in story.evidence_pack.evidence_items
                if item.source_id in source_ids
            ],
            canonical_draft=draft,
            reel=build_reel_package(draft, source_reference_ids=source_ids),
            instagram=build_instagram_package(draft, selected_hashtags),
            blog=build_blog_package(draft, title=selected_title.text, source_references=source_references),
            linkedin=build_linkedin_package(draft),
            x=build_x_package(draft),
            tiktok=build_tiktok_package(draft, selected_hashtags),
            youtube_shorts=build_youtube_shorts_package(draft, title=selected_title.text),
            generation_metadata=_metadata_from_result(result, datetime.now(UTC)),
            validation=None,
        )
        validation = validate_package(package, story)
        return replace(package, validation=validation)

    def _generate_canonical_draft(
        self,
        *,
        story: VerifiedGroundedStory,
        selected_angle: PotentialAngle,
        allowed_claim_ids: list[str],
    ) -> LLMResult:
        if self.llm_client is None:
            raise ContentPackageGenerationError("llm_client is required for content package generation")
        return self.llm_client.generate_structured(
            system_prompt=PROMPT_PATH.read_text(encoding="utf-8"),
            user_prompt=_package_prompt(story, selected_angle, allowed_claim_ids),
            response_schema=CanonicalContentDraftOutput,
        )


def _package_prompt(
    story: VerifiedGroundedStory,
    selected_angle: PotentialAngle,
    allowed_claim_ids: list[str],
) -> str:
    allowed_claims = [
        claim
        for claim in story.verified_claims
        if claim.claim_id in allowed_claim_ids
    ]
    evidence = [
        item
        for item in story.evidence_pack.evidence_items
        if any(claim_id in allowed_claim_ids for claim_id in [item.evidence_id, *allowed_claim_ids])
    ]
    return (
        "VerifiedGroundedStory:\n"
        f"{asdict(story)}\n\n"
        f"Selected angle:\n{asdict(selected_angle)}\n\n"
        f"Allowed claims only:\n{[asdict(claim) for claim in allowed_claims]}\n\n"
        f"Evidence context:\n{[asdict(item) for item in evidence]}"
    )


def _draft_from_output(output) -> CanonicalContentDraft:
    if not isinstance(output, CanonicalContentDraftOutput):
        output = CanonicalContentDraftOutput.model_validate(output)
    return CanonicalContentDraft(
        hook=output.hook,
        thesis=output.thesis,
        key_points=list(output.key_points),
        technical_explanation=output.technical_explanation,
        human_implication=output.human_implication,
        career_upskill_implication=output.career_upskill_implication,
        takeaway=output.takeaway,
        cta=output.cta,
        claim_references=list(output.claim_references),
    )


def _source_references(story: VerifiedGroundedStory) -> list[SourceReference]:
    return [
        SourceReference(
            source_id=source.source_id,
            source_name=source.source_name,
            source_url=source.source_url,
            source_type=source.source_type.value,
        )
        for source in story.evidence_pack.sources
    ]


def _metadata_from_result(result: LLMResult, generated_at: datetime) -> GenerationMetadata:
    return GenerationMetadata(
        model=result.model,
        provider=result.provider,
        generated_at=generated_at,
        latency_ms=result.latency_ms,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        estimated_cost_usd=result.estimated_cost_usd,
        prompt_version=PROMPT_VERSION,
    )
