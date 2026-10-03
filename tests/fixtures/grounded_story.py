from datetime import datetime

from src.shared.models import (
    Audience,
    AudienceValue,
    Source,
    Story,
    StoryScores,
    StoryType,
)


# TEST / DEVELOPMENT DATA
# Stable fixture for exercising the generation pipeline. This is not current news.
GROUNDED_STORY = Story(
    id="story-dev-ai-code-review",
    headline="AI assistants are changing software code review workflows",
    summary=(
        "AI coding assistants can help developers summarize changes, identify "
        "possible issues, and explain unfamiliar code during review."
    ),
    domain="software",
    subdomain="software engineering",
    story_type=StoryType.IMPACT,
    why_it_matters=(
        "Code review is a common bottleneck in software teams, and AI assistance "
        "could shift developer time toward judgment, testing, and architecture."
    ),
    source_published_at=datetime(2025, 1, 15, 9, 0),
    discovered_at=datetime(2026, 10, 3, 10, 0),
    scores=StoryScores(
        relevance=0.9,
        timeliness=0.7,
        significance=0.8,
        evidence_quality=0.75,
        educational_value=0.85,
        career_impact=0.8,
        content_potential=0.9,
        novelty=0.6,
    ),
    audience_value=AudienceValue(
        student=0.8,
        professional=0.9,
        enthusiast=0.75,
    ),
    audiences=[Audience.STUDENT, Audience.PROFESSIONAL],
    professions_affected=["software engineer", "engineering manager", "QA analyst"],
    industries_affected=["technology", "software"],
    companies=["GitHub", "OpenAI"],
    concepts=["code review", "AI coding assistant", "developer productivity"],
    sources=[
        Source(
            id="source-dev-1",
            url="https://example.com/development/ai-code-review-overview",
            title="AI-assisted code review overview",
            publisher="Example Development Source",
            published_at=datetime(2025, 1, 15, 9, 0),
            retrieved_at=datetime(2026, 10, 3, 10, 0),
            source_type="article",
        ),
        Source(
            id="source-dev-2",
            url="https://example.com/development/developer-workflows",
            title="Developer workflow research summary",
            publisher="Example Research Source",
            published_at=datetime(2025, 2, 20, 11, 30),
            retrieved_at=datetime(2026, 10, 3, 10, 5),
            source_type="research_summary",
        ),
    ],
)
