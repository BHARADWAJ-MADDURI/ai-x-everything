from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from src.intelligence.models import (
    HashtagCandidate,
    HashtagResearchStatus,
    HashtagSource,
    TargetPlatform,
    VerifiedGroundedStory,
)


GENERIC_FILLER = {"#viral", "#fyp", "#trending", "#explorepage", "#success", "#motivation"}


@dataclass(frozen=True)
class HashtagResearchResult:
    """Future live-research result for a hashtag."""

    tag: str
    relevance_score: float
    specificity_score: float
    estimated_reach_band: str | None
    competition_band: str | None
    researched_at: datetime | None


class HashtagResearchProvider(Protocol):
    """Interface for future live/current hashtag research."""

    def research(self, topic_terms: list[str], platform: TargetPlatform) -> list[HashtagResearchResult]:
        ...


class FakeHashtagResearchProvider:
    """Deterministic test provider with caller-supplied results."""

    def __init__(self, results: list[HashtagResearchResult]) -> None:
        self.results = results

    def research(self, topic_terms: list[str], platform: TargetPlatform) -> list[HashtagResearchResult]:
        return self.results


def topic_terms_from_story(story: VerifiedGroundedStory) -> list[str]:
    terms = [
        *story.analysis.technologies,
        *story.analysis.applications,
        *story.analysis.industries,
        *story.analysis.workflows,
    ]
    return [term for term in dict.fromkeys(terms) if term]


def unresearched_hashtag_candidates(
    story: VerifiedGroundedStory,
    platform: TargetPlatform,
) -> list[HashtagCandidate]:
    candidates = []
    for term in topic_terms_from_story(story):
        tag = "#" + "".join(ch for ch in term.title() if ch.isalnum())
        candidates.append(
            HashtagCandidate(
                tag=tag,
                relevance_score=0.8,
                specificity_score=0.7,
                source=HashtagSource.VERIFIED_STORY,
                research_status=HashtagResearchStatus.UNRESEARCHED,
                platform=platform,
                estimated_reach_band=None,
                competition_band=None,
                researched_at=None,
                supporting_topic_terms=[term],
            )
        )
    return candidates


def select_hashtags(
    candidates: list[HashtagCandidate],
    *,
    limit: int = 5,
) -> list[HashtagCandidate]:
    """Select relevant hashtags; popularity never overrides near-zero relevance."""

    viable = []
    for candidate in candidates:
        if candidate.tag.lower() in GENERIC_FILLER and candidate.relevance_score < 0.8:
            candidate.rejection_reason = "generic filler hashtag"
            continue
        if candidate.relevance_score < 0.25:
            candidate.rejection_reason = "low relevance"
            continue
        viable.append(candidate)
    viable.sort(key=_hashtag_score, reverse=True)
    for candidate in viable[:limit]:
        candidate.selected = True
    return viable[:limit]


def _hashtag_score(candidate: HashtagCandidate) -> float:
    research_bonus = 0.1 if candidate.research_status is HashtagResearchStatus.RESEARCHED else 0.0
    return candidate.relevance_score * 0.6 + candidate.specificity_score * 0.3 + research_bonus
