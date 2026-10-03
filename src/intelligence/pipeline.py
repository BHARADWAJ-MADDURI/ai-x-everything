from src.intelligence.analysis import analyze_story
from src.intelligence.angles import generate_angles
from src.intelligence.dedup import cluster_candidates
from src.intelligence.grounding import extract_grounded_facts
from src.intelligence.models import AnalyzedStory, CandidateItem, PipelineResult
from src.intelligence.normalize import normalize_candidate
from src.intelligence.scoring import score_angle
from src.intelligence.selector import decide_story
from src.intelligence.sources import evidence_from_candidate, evidence_quality


def run_intelligence_pipeline(
    candidates: list[CandidateItem],
    *,
    llm_client=None,
) -> PipelineResult:
    """Run deterministic Step 5 intelligence pipeline over candidates."""

    normalized = [normalize_candidate(candidate) for candidate in candidates]
    clusters = cluster_candidates(normalized)
    analyzed: list[AnalyzedStory] = []
    decisions = {}
    for cluster in clusters:
        evidence_sources = [evidence_from_candidate(candidate) for candidate in cluster.candidates]
        facts = extract_grounded_facts(cluster)
        analysis = analyze_story(cluster, facts, llm_client=llm_client)
        quality = evidence_quality(evidence_sources)
        angles = [
            score_angle(angle, analysis)
            for angle in generate_angles(analysis, facts, quality)
        ]
        story = AnalyzedStory(
            cluster=cluster,
            evidence_sources=evidence_sources,
            facts=facts,
            analysis=analysis,
            angles=angles,
        )
        analyzed.append(story)
        decisions[cluster.id] = decide_story(story)
    return PipelineResult(analyzed_stories=analyzed, decisions=decisions)
