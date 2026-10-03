import unittest

from src.generation.llm_client import LLMResult
from src.generation.short_video_generator import generate_short_video
from src.shared.models import ContentFormat, Platform
from tests.fixtures.grounded_story import GROUNDED_STORY


class FakeShortVideoLLMClient:
    def generate_structured(self, *, system_prompt, user_prompt, response_schema):
        output = response_schema.model_validate(
            {
                "title": "AI in code review",
                "hook": "AI is changing how developers review code.",
                "target_duration_seconds": 45,
                "scenes": [
                    {
                        "scene_number": 1,
                        "narration": "Code review is where teams protect quality.",
                        "on_screen_text": "Code review is changing",
                        "visual_direction": "animated workflow diagram",
                    },
                    {
                        "scene_number": 2,
                        "narration": "AI assistants can summarize changes.",
                        "on_screen_text": "Summaries, not autopilot",
                        "visual_direction": "developer reviewing highlighted diff",
                    },
                ],
                "closing_line": "Follow for practical AI explainers.",
                "caption": "AI is changing software workflows, carefully.",
                "hashtags": ["#AI", "#SoftwareEngineering"],
            }
        )
        return LLMResult(
            output=output,
            model="fake-video-model",
            provider="fake",
            latency_ms=20,
            input_tokens=120,
            output_tokens=90,
            estimated_cost_usd=None,
        )


class ShortVideoGeneratorTests(unittest.TestCase):
    def test_short_video_generator_creates_short_video_content_asset(self) -> None:
        plan, asset, metadata = generate_short_video(
            GROUNDED_STORY,
            _article_fixture(),
            llm_client=FakeShortVideoLLMClient(),
        )

        self.assertEqual(asset.format, ContentFormat.SHORT_VIDEO)
        self.assertEqual(asset.title, plan.title)
        self.assertIn("Scene 1:", asset.body)
        self.assertEqual(metadata.model, "fake-video-model")

    def test_content_asset_targets_short_video_platforms(self) -> None:
        _plan, asset, _metadata = generate_short_video(
            GROUNDED_STORY,
            _article_fixture(),
            llm_client=FakeShortVideoLLMClient(),
        )

        self.assertEqual(
            asset.target_platforms,
            [Platform.INSTAGRAM, Platform.TIKTOK, Platform.YOUTUBE],
        )

    def test_target_audiences_come_from_story(self) -> None:
        _plan, asset, _metadata = generate_short_video(
            GROUNDED_STORY,
            _article_fixture(),
            llm_client=FakeShortVideoLLMClient(),
        )

        self.assertEqual(asset.target_audiences, GROUNDED_STORY.audiences)

    def test_short_video_metadata_records_prompt_version(self) -> None:
        _plan, _asset, metadata = generate_short_video(
            GROUNDED_STORY,
            _article_fixture(),
            llm_client=FakeShortVideoLLMClient(),
        )

        self.assertEqual(metadata.prompt_version, "short_video_v1")
        self.assertEqual(metadata.latency_ms, 20)


def _article_fixture():
    from datetime import datetime

    from src.shared.models import Article

    return Article(
        id="article-dev-1",
        story_id=GROUNDED_STORY.id,
        title="How AI assistants are changing code review",
        subtitle=None,
        tldr="AI assistants can help with review summaries and explanations.",
        what_happened="AI assistance is being applied to code review workflows.",
        how_it_works="The assistant uses code context to suggest explanations.",
        why_it_matters="Reviewers may spend more time on judgment.",
        industry_impact="Software teams may adapt review habits.",
        career_impact="Developers may need stronger verification habits.",
        opportunities=["Faster summaries"],
        risks_and_limitations=["AI suggestions can be wrong"],
        key_concepts=["code review", "AI coding assistant"],
        source_ids=[source.id for source in GROUNDED_STORY.sources],
        created_at=datetime(2026, 10, 3, 11, 0),
        updated_at=datetime(2026, 10, 3, 11, 0),
    )
