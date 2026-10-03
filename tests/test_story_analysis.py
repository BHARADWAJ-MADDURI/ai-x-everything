import unittest

from src.generation.llm_client import LLMResult
from src.intelligence.analysis import StoryAnalysisOutput, analyze_story
from src.intelligence.dedup import cluster_candidates
from src.intelligence.grounding import extract_grounded_facts
from src.intelligence.normalize import normalize_candidate
from tests.fixtures.intelligence_candidates import FOUNDATION_MODEL, ROBOTICS_COMPANY


class FakeAnalysisClient:
    def generate_structured(self, *, system_prompt, user_prompt, response_schema):
        return LLMResult(
            output=response_schema.model_validate(
                {
                    "development_summary": "A robotics model targets factory maintenance workflows.",
                    "technologies": ["robotics", "vision-language-action"],
                    "applications": ["maintenance diagnostics"],
                    "industries": ["manufacturing"],
                    "workflows": ["maintenance diagnostics"],
                    "professions": ["maintenance technician"],
                    "demonstrated_capabilities": ["Connects visual input and language instructions to robot action."],
                    "limitations": [],
                    "uncertainties": ["Deployment results are not yet independently established."],
                    "novelty_summary": "Combines perception, language, and action for robotics workflows.",
                }
            ),
            model="fake",
            provider="fake",
            latency_ms=1,
            input_tokens=10,
            output_tokens=20,
        )


class StoryAnalysisTests(unittest.TestCase):
    def test_fake_llm_drives_analysis_tests(self) -> None:
        cluster = cluster_candidates([normalize_candidate(ROBOTICS_COMPANY)])[0]
        facts = extract_grounded_facts(cluster)

        analysis = analyze_story(cluster, facts, llm_client=FakeAnalysisClient())

        self.assertEqual(analysis.professions, ["maintenance technician"])
        self.assertIn("robotics", analysis.technologies)

    def test_story_analysis_may_contain_empty_professions(self) -> None:
        cluster = cluster_candidates([normalize_candidate(FOUNDATION_MODEL)])[0]
        output = StoryAnalysisOutput(
            development_summary="A general model update was announced.",
            technologies=["language model"],
            applications=[],
            industries=[],
            workflows=[],
            professions=[],
            demonstrated_capabilities=[],
            limitations=[],
            uncertainties=[],
            novelty_summary=None,
        )

        self.assertEqual(output.professions, [])
