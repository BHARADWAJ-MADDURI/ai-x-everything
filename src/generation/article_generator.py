from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from src.generation.llm_client import LLMResult, OpenAILLMClient
from src.generation.schemas import ArticleOutput
from src.shared.models import Article, GenerationMetadata, Story


PROMPT_VERSION = "article_v1"
PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "article_v1.txt"


def generate_article(
    story: Story,
    llm_client: OpenAILLMClient | None = None,
) -> tuple[Article, GenerationMetadata]:
    """Generate a canonical Article from a grounded Story."""

    client = llm_client or OpenAILLMClient()
    result = client.generate_structured(
        system_prompt=PROMPT_PATH.read_text(encoding="utf-8"),
        user_prompt=_story_prompt(story),
        response_schema=ArticleOutput,
    )
    output = result.output
    if not isinstance(output, ArticleOutput):
        output = ArticleOutput.model_validate(output)

    now = datetime.now(UTC)
    article = Article(
        id=f"article-{uuid4()}",
        story_id=story.id,
        title=output.title,
        subtitle=output.subtitle,
        tldr=output.tldr,
        what_happened=output.what_happened,
        how_it_works=output.how_it_works,
        why_it_matters=output.why_it_matters,
        industry_impact=output.industry_impact,
        career_impact=output.career_impact,
        opportunities=output.opportunities,
        risks_and_limitations=output.risks_and_limitations,
        key_concepts=output.key_concepts,
        source_ids=[source.id for source in story.sources],
        created_at=now,
        updated_at=now,
    )

    return article, _metadata_from_result(result, now)


def _story_prompt(story: Story) -> str:
    return f"Grounded Story:\n{asdict(story)}"


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
