from dataclasses import asdict
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from src.generation.llm_client import LLMResult, OpenAILLMClient
from src.intelligence.models import GroundedFact, StoryAnalysis, StoryCluster


PROMPT_VERSION = "story_analysis_v1"
PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "story_analysis_v1.txt"


class StoryAnalysisOutput(BaseModel):
    """Validated structured LLM output for story analysis."""

    model_config = ConfigDict(extra="forbid")

    development_summary: str = Field(min_length=1)
    technologies: list[str] = Field(default_factory=list)
    applications: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    workflows: list[str] = Field(default_factory=list)
    professions: list[str] = Field(default_factory=list)
    demonstrated_capabilities: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    novelty_summary: str | None = None


def analyze_story(
    cluster: StoryCluster,
    facts: list[GroundedFact],
    llm_client: OpenAILLMClient | None = None,
) -> StoryAnalysis:
    """Analyze a story cluster using injectable structured LLM output."""

    if llm_client is None:
        return deterministic_analysis(cluster, facts)

    result = llm_client.generate_structured(
        system_prompt=PROMPT_PATH.read_text(encoding="utf-8"),
        user_prompt=f"Cluster:\n{asdict(cluster)}\n\nGrounded facts:\n{[asdict(fact) for fact in facts]}",
        response_schema=StoryAnalysisOutput,
    )
    output = result.output
    if not isinstance(output, StoryAnalysisOutput):
        output = StoryAnalysisOutput.model_validate(output)
    return StoryAnalysis(**output.model_dump())


def deterministic_analysis(cluster: StoryCluster, facts: list[GroundedFact]) -> StoryAnalysis:
    """Offline deterministic analysis for demos and non-LLM test paths."""

    text = " ".join([cluster.title, *(fact.claim for fact in facts)]).lower()
    technologies = []
    if "robot" in text:
        technologies.append("robotics")
    if "language" in text or "foundation model" in text:
        technologies.append("language model")
    if "health" in text or "medical" in text:
        technologies.append("healthcare AI")
    if "vision" in text:
        technologies.append("computer vision")

    industries = []
    workflows = []
    professions = []
    limitations = []
    if "manufacturing" in text or "factory" in text:
        industries.append("manufacturing")
    if "maintenance" in text or "diagnostic" in text:
        workflows.append("maintenance diagnostics")
        professions.append("maintenance technician")
    if "health" in text or "medical" in text:
        industries.append("healthcare")
        limitations.append("Requires clinical validation before deployment.")
    if "hype" in text or "revolutionize" in text:
        limitations.append("Claims are broad and weakly supported.")

    return StoryAnalysis(
        development_summary=cluster.title,
        technologies=technologies,
        applications=workflows.copy(),
        industries=industries,
        workflows=workflows,
        professions=professions,
        demonstrated_capabilities=[fact.claim for fact in facts if fact.claim_kind.value == "fact"][:3],
        limitations=limitations,
        uncertainties=[],
        novelty_summary="Potentially useful if supported by evidence." if facts else None,
    )
