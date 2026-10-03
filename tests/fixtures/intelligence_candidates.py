from datetime import datetime

from src.intelligence.models import CandidateItem, SourceType


NOW = datetime(2026, 10, 3, 12, 0)


ROBOTICS_COMPANY = CandidateItem(
    id="candidate-robotics-company",
    source_name="Example Robotics",
    source_url="https://example.com/news/robotics-model?utm_source=social",
    source_type=SourceType.COMPANY,
    title="Example Robotics launches vision-language-action model for factory robots",
    summary=(
        "Example Robotics announced a robotics model that connects vision, language, "
        "and robot actions for factory maintenance diagnostic workflows."
    ),
    published_at=datetime(2026, 9, 30, 9, 0),
    discovered_at=NOW,
    author=None,
)

ROBOTICS_NEWS_DUPLICATE = CandidateItem(
    id="candidate-robotics-news",
    source_name="Industrial AI Review",
    source_url="https://industry.example/articles/company-robotics-model",
    source_type=SourceType.NEWS,
    title="Example Robotics introduces new robotics AI for factory maintenance",
    summary=(
        "Independent coverage says the system targets factory maintenance diagnostics "
        "and may affect reliability technician workflows."
    ),
    published_at=datetime(2026, 9, 30, 12, 0),
    discovered_at=NOW,
    author="A. Reporter",
)

FOUNDATION_MODEL = CandidateItem(
    id="candidate-foundation-model",
    source_name="Model Lab",
    source_url="https://example.com/model-lab/general-model",
    source_type=SourceType.COMPANY,
    title="Model Lab announces a general language model update",
    summary="Model Lab announced a general-purpose language model with better coding and reasoning benchmarks.",
    published_at=datetime(2026, 9, 29, 8, 0),
    discovered_at=NOW,
    author=None,
)

HEALTHCARE_RESEARCH = CandidateItem(
    id="candidate-healthcare-research",
    source_name="Journal Example",
    source_url="https://research.example/healthcare-ai-study",
    source_type=SourceType.RESEARCH,
    title="Healthcare AI research result improves triage prediction in retrospective study",
    summary=(
        "A research study reports improved triage prediction on retrospective data, "
        "with limitations around clinical validation and deployment."
    ),
    published_at=datetime(2026, 9, 28, 10, 0),
    discovered_at=NOW,
    author="Research Team",
)

HYPE_WEAK = CandidateItem(
    id="candidate-hype",
    source_name="AI Hype Daily",
    source_url="https://hype.example/ai-revolution-every-job",
    source_type=SourceType.OTHER,
    title="This AI tool will revolutionize every job overnight",
    summary="A hype-heavy article claims AI will transform all industries but provides no concrete evidence.",
    published_at=datetime(2026, 9, 27, 7, 0),
    discovered_at=NOW,
    author=None,
)

ALL_CANDIDATES = [
    ROBOTICS_COMPANY,
    ROBOTICS_NEWS_DUPLICATE,
    FOUNDATION_MODEL,
    HEALTHCARE_RESEARCH,
    HYPE_WEAK,
]
