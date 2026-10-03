import unittest

from pydantic import ValidationError

from src.generation.schemas import ArticleOutput, ShortVideoPlan


class GenerationSchemaTests(unittest.TestCase):
    def test_article_output_validates_correct_structured_data(self) -> None:
        output = ArticleOutput(
            title="AI changes code review",
            subtitle=None,
            tldr="AI assistants can help summarize and inspect code changes.",
            what_happened="Teams are using AI assistance in review workflows.",
            how_it_works="The assistant analyzes code diffs and surrounding context.",
            why_it_matters="Reviewers can focus more attention on judgment.",
            industry_impact="Software teams may adapt review practices.",
            career_impact="Developers may need stronger validation skills.",
            opportunities=["Faster summaries"],
            risks_and_limitations=["AI suggestions can be wrong"],
            key_concepts=["code review"],
        )

        self.assertEqual(output.title, "AI changes code review")
        self.assertEqual(output.key_concepts, ["code review"])

    def test_article_output_rejects_malformed_data(self) -> None:
        with self.assertRaises(ValidationError):
            ArticleOutput(
                title="",
                tldr="Valid TLDR",
                what_happened="Valid detail",
                why_it_matters="Valid reason",
                opportunities="not a list",
            )

    def test_short_video_plan_validates_correct_plan(self) -> None:
        plan = ShortVideoPlan(
            title="AI in code review",
            hook="AI is changing how developers review code.",
            target_duration_seconds=45,
            scenes=[
                {
                    "scene_number": 1,
                    "narration": "Code review is where teams protect quality.",
                    "on_screen_text": "Code review is changing",
                    "visual_direction": "software workflow diagram",
                }
            ],
            closing_line="Follow for practical AI explainers.",
            caption="AI is changing software workflows.",
            hashtags=["#AI", "#SoftwareEngineering"],
        )

        self.assertEqual(plan.scenes[0].scene_number, 1)
        self.assertEqual(plan.target_duration_seconds, 45)

    def test_short_video_plan_rejects_invalid_data(self) -> None:
        with self.assertRaises(ValidationError):
            ShortVideoPlan(
                title="AI in code review",
                hook="AI is changing code review.",
                target_duration_seconds=5,
                scenes=[],
                closing_line="Follow for more.",
                caption="Caption",
                hashtags=["#AI"],
            )
