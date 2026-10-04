from dataclasses import dataclass
from datetime import datetime, timezone
from time import sleep

from src.discovery.models import DiscoveryProvider, DiscoveryResult, DiscoveryRunMetrics
from src.discovery.urls import normalize_discovery_url
from src.intelligence.dedup import cluster_candidates
from src.intelligence.models import CandidateItem, EvidenceItem, StoryCluster
from src.intelligence.normalize import normalize_candidate
from src.research.evidence import EvidenceExtractor
from src.research.extraction import ArticleTextExtractor, ExtractedText
from src.research.retrieval import RetrievedSource, RetrievalStatus, SourceRetriever


@dataclass(frozen=True)
class ResearchAttempt:
    candidate: CandidateItem
    cluster: StoryCluster
    retrieved_source: RetrievedSource
    extracted_text: ExtractedText
    evidence_items: list[EvidenceItem]

    @property
    def ready_for_intelligence(self) -> bool:
        return bool(self.evidence_items)


@dataclass(frozen=True)
class DiscoveryResearchRun:
    discovered_results: list[DiscoveryResult]
    candidates: list[CandidateItem]
    clusters: list[StoryCluster]
    attempts: list[ResearchAttempt]
    metrics: DiscoveryRunMetrics


class LiveDiscoveryResearchRunner:
    """Bounded discovery/research run for developer demos and future schedulers."""

    def __init__(
        self,
        *,
        provider: DiscoveryProvider,
        retriever: SourceRetriever,
        text_extractor: ArticleTextExtractor | None = None,
        evidence_extractor: EvidenceExtractor | None = None,
        request_delay_seconds: float = 0.0,
    ) -> None:
        self.provider = provider
        self.retriever = retriever
        self.text_extractor = text_extractor or ArticleTextExtractor()
        self.evidence_extractor = evidence_extractor or EvidenceExtractor()
        self.request_delay_seconds = request_delay_seconds

    def run(
        self,
        *,
        query: str | None = None,
        since: datetime | None = None,
        discovery_limit: int = 20,
        retrieval_limit: int = 3,
    ) -> DiscoveryResearchRun:
        metrics = DiscoveryRunMetrics(provider=self.provider.name)
        discovered = self.provider.discover(query=query, since=since, limit=discovery_limit)
        metrics.queries_or_feeds_checked = getattr(self.provider, "feeds_checked", 0) or 1
        metrics.results_discovered = len(discovered)

        candidates = normalize_discovery_results(discovered)
        metrics.duplicates_removed = len(discovered) - len(candidates)
        clusters = cluster_candidates(candidates)

        attempts: list[ResearchAttempt] = []
        candidate_to_cluster = {
            candidate.id: cluster
            for cluster in clusters
            for candidate in cluster.candidates
        }
        for index, candidate in enumerate(candidates[:retrieval_limit], start=1):
            if index > 1 and self.request_delay_seconds > 0:
                sleep(self.request_delay_seconds)
            metrics.retrieval_attempts += 1
            retrieved = self.retriever.retrieve(candidate.source_url)
            if retrieved.retrieval_status is RetrievalStatus.SUCCESS:
                metrics.retrieval_successes += 1
            else:
                metrics.retrieval_failures += 1
            extracted = self.text_extractor.extract(retrieved.raw_text, retrieved.content_type)
            cluster = candidate_to_cluster[candidate.id]
            evidence_items = self.evidence_extractor.extract(
                cluster=cluster,
                candidate=candidate,
                retrieved_source=retrieved,
                extracted_text=extracted,
                source_index=index,
            )
            metrics.evidence_items_created += len(evidence_items)
            attempts.append(
                ResearchAttempt(
                    candidate=candidate,
                    cluster=cluster,
                    retrieved_source=retrieved,
                    extracted_text=extracted,
                    evidence_items=evidence_items,
                )
            )
        metrics.finished_at = datetime.now(timezone.utc)
        return DiscoveryResearchRun(
            discovered_results=discovered,
            candidates=candidates,
            clusters=clusters,
            attempts=attempts,
            metrics=metrics,
        )


def normalize_discovery_results(results: list[DiscoveryResult]) -> list[CandidateItem]:
    """Convert provider results to CandidateItems and remove obvious duplicates."""

    seen_urls: set[str] = set()
    seen_titles: set[tuple[str, str]] = set()
    candidates: list[CandidateItem] = []
    for result in results:
        normalized_url = normalize_discovery_url(result.url)
        title_key = (" ".join(result.title.lower().split()), result.source_name.lower())
        if normalized_url in seen_urls or title_key in seen_titles:
            continue
        seen_urls.add(normalized_url)
        seen_titles.add(title_key)
        candidates.append(normalize_candidate(result.to_candidate(normalized_url=normalized_url)))
    return candidates
