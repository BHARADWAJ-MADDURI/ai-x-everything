import unittest

from src.generation.article_generator import generate_article
from src.generation.llm_client import LLMResult
from src.generation.schemas import ArticleOutput
from src.shared.models import Article
from tests.fixtures.grounded_story import GROUNDED_STORY


class FakeArticleLLMClient:
    def generate_structured(self, *, system_prompt, user_prompt, response_schema):
        output = response_schema.model_validate(
            {
                "title": "How AI assistants are changing code review",
                "subtitle": "A practical look at software workflow shifts",
                "tldr": "AI assistants can help summarize and inspect code changes.",
                "what_happened": "AI assistance is being applied to code review tasks.",
                "how_it_works": "The assistant uses code context to suggest explanations.",
                "why_it_matters": "Reviewers may spend more time on judgment.",
                "industry_impact": "Software teams may adjust review processes.",
                "career_impact": "Developers may need stronger AI verification habits.",
                "opportunities": ["Faster review summaries"],
                "risks_and_limitations": ["AI can miss context or be wrong"],
                "key_concepts": ["code review", "AI coding assistant"],
            }
        )
        return LLMResult(
            output=output,
            model="fake-model",
            provider="fake",
            latency_ms=12,
            input_tokens=100,
            output_tokens=80,
            estimated_cost_usd=0.01,
        )


class ArticleGeneratorTests(unittest.TestCase):
    def test_article_generator_converts_fake_llm_output_to_article(self) -> None:
        article, metadata = generate_article(
            GROUNDED_STORY,
            llm_client=FakeArticleLLMClient(),
        )

        self.assertIsInstance(article, Article)
        self.assertEqual(article.story_id, GROUNDED_STORY.id)
        self.assertEqual(article.title, "How AI assistants are changing code review")
        self.assertEqual(metadata.model, "fake-model")

    def test_article_source_ids_come_from_story_sources(self) -> None:
        article, _metadata = generate_article(
            GROUNDED_STORY,
            llm_client=FakeArticleLLMClient(),
        )

        self.assertEqual(
            article.source_ids,
            [source.id for source in GROUNDED_STORY.sources],
        )
        self.assertNotEqual(article.source_ids, [])

    def test_article_generator_records_generation_metadata(self) -> None:
        _article, metadata = generate_article(
            GROUNDED_STORY,
            llm_client=FakeArticleLLMClient(),
        )

        self.assertEqual(metadata.provider, "fake")
        self.assertEqual(metadata.latency_ms, 12)
        self.assertEqual(metadata.input_tokens, 100)
        self.assertEqual(metadata.output_tokens, 80)
        self.assertEqual(metadata.prompt_version, "article_v1")

    def test_fake_client_returns_valid_article_output(self) -> None:
        result = FakeArticleLLMClient().generate_structured(
            system_prompt="prompt",
            user_prompt="story",
            response_schema=ArticleOutput,
        )

        self.assertIsInstance(result.output, ArticleOutput)
