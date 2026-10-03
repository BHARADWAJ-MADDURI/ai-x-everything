import unittest

from src.generation.llm_client import LLMResult
from src.intelligence.analysis import StoryAnalysisOutput
from src.intelligence.models import AngleType, EditorialOutcome
from src.intelligence.pipeline import run_intelligence_pipeline
from tests.fixtures.intelligence_candidates import ALL_CANDIDATES


class PipelineAnalysisClient:
    def generate_structured(self, *, system_prompt, user_prompt, response_schema):
        if "factory maintenance" in user_prompt:
            payload = {
                "development_summary": "Robotics model for factory maintenance workflows.",
                "technologies": ["robotics", "vision-language-action"],
                "applications": ["maintenance diagnostics"],
                "industries": ["manufacturing"],
                "workflows": ["maintenance diagnostics"],
                "professions": ["maintenance technician"],
                "demonstrated_capabilities": ["Targets maintenance diagnostics."],
                "limitations": [],
                "uncertainties": ["Real-world deployment evidence remains limited."],
                "novelty_summary": "Connects perception, language, and action.",
            }
        elif "triage" in user_prompt:
            payload = {
                "development_summary": "Healthcare AI triage prediction research result.",
                "technologies": ["healthcare AI"],
                "applications": ["triage prediction"],
                "industries": ["healthcare"],
                "workflows": [],
                "professions": [],
                "demonstrated_capabilities": ["Improved retrospective prediction."],
                "limitations": ["Requires clinical validation before deployment."],
                "uncertainties": ["Prospective deployment performance is unknown."],
                "novelty_summary": "Research evidence with deployment caveats.",
            }
        elif "revolutionize" in user_prompt:
            payload = {
                "development_summary": "A hype-heavy article makes broad unsupported claims.",
                "technologies": [],
                "applications": [],
                "industries": [],
                "workflows": [],
                "professions": [],
                "demonstrated_capabilities": [],
                "limitations": ["Claims are broad and weakly supported."],
                "uncertainties": ["Evidence is insufficient."],
                "novelty_summary": None,
            }
        else:
            payload = {
                "development_summary": "A general language model update was announced.",
                "technologies": ["language model"],
                "applications": [],
                "industries": [],
                "workflows": [],
                "professions": [],
                "demonstrated_capabilities": ["Better coding and reasoning benchmarks were claimed."],
                "limitations": [],
                "uncertainties": ["No specific farming workflow evidence was supplied."],
                "novelty_summary": "General model update.",
            }
        return LLMResult(
            output=response_schema.model_validate(payload),
            model="fake",
            provider="fake",
            latency_ms=1,
            input_tokens=1,
            output_tokens=1,
        )


class IntelligencePipelineTests(unittest.TestCase):
    def test_pipeline_clusters_duplicates_and_keeps_fact_distinctions(self) -> None:
        result = run_intelligence_pipeline(ALL_CANDIDATES, llm_client=PipelineAnalysisClient())

        self.assertEqual(len(result.analyzed_stories), 4)
        robotics = result.analyzed_stories[0]
        self.assertEqual(len(robotics.cluster.candidates), 2)
        self.assertGreaterEqual(len(robotics.facts), 3)

    def test_pipeline_allows_general_model_story_without_career_or_upskill(self) -> None:
        result = run_intelligence_pipeline(ALL_CANDIDATES, llm_client=PipelineAnalysisClient())
        general = next(story for story in result.analyzed_stories if "language model" in story.analysis.technologies)
        angle_types = {angle.angle_type for angle in general.angles}

        self.assertNotIn(AngleType.CAREER, angle_types)
        self.assertNotIn(AngleType.UPSKILL, angle_types)

    def test_pipeline_selects_strong_story_and_rejects_hype(self) -> None:
        result = run_intelligence_pipeline(ALL_CANDIDATES, llm_client=PipelineAnalysisClient())
        outcomes = {cluster_id: decision.outcome for cluster_id, decision in result.decisions.items()}

        self.assertIn(EditorialOutcome.SELECT, outcomes.values())
        self.assertIn(EditorialOutcome.REJECT, outcomes.values())

    def test_no_network_calls_are_needed_for_pipeline_tests(self) -> None:
        result = run_intelligence_pipeline(ALL_CANDIDATES, llm_client=PipelineAnalysisClient())

        self.assertEqual(len(result.analyzed_stories), 4)
