from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from src.generation.llm_client import LLMResult, OpenAILLMClient
from src.generation.schemas import ShortVideoPlan
from src.shared.models import (
    Article,
    ContentAsset,
    ContentFormat,
    GenerationMetadata,
    Platform,
    Story,
)


PROMPT_VERSION = "short_video_v1"
PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "short_video_v1.txt"


def generate_short_video(
    story: Story,
    article: Article,
    llm_client: OpenAILLMClient | None = None,
) -> tuple[ShortVideoPlan, ContentAsset, GenerationMetadata]:
    """Generate a short-video plan and matching ContentAsset."""

    client = llm_client or OpenAILLMClient()
    result = client.generate_structured(
        system_prompt=PROMPT_PATH.read_text(encoding="utf-8"),
        user_prompt=_story_and_article_prompt(story, article),
        response_schema=ShortVideoPlan,
    )
    plan = result.output
    if not isinstance(plan, ShortVideoPlan):
        plan = ShortVideoPlan.model_validate(plan)

    now = datetime.now(UTC)
    asset = ContentAsset(
        id=f"content-asset-{uuid4()}",
        story_id=story.id,
        article_id=article.id,
        format=ContentFormat.SHORT_VIDEO,
        title=plan.title,
        hook=plan.hook,
        body=_script_from_plan(plan),
        call_to_action=plan.closing_line,
        generation_metadata=None,
        created_at=now,
        target_platforms=[Platform.INSTAGRAM, Platform.TIKTOK, Platform.YOUTUBE],
        target_audiences=list(story.audiences),
    )

    return plan, asset, _metadata_from_result(result, now)


def _story_and_article_prompt(story: Story, article: Article) -> str:
    return f"Grounded Story:\n{asdict(story)}\n\nCanonical Article:\n{asdict(article)}"


def _script_from_plan(plan: ShortVideoPlan) -> str:
    scene_lines = [
        f"Scene {scene.scene_number}: {scene.narration}" for scene in plan.scenes
    ]
    return "\n".join([plan.hook, *scene_lines, plan.closing_line])


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
