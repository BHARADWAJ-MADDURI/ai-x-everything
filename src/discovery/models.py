from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Protocol

from src.intelligence.models import CandidateItem, SourceType


@dataclass(frozen=True)
class DiscoveryResult:
    """Externally observed metadata from a discovery provider."""

    title: str
    url: str
    source_name: str
    source_type: SourceType
    published_at: datetime | None
    excerpt: str | None
    discovered_at: datetime
    provider: str
    provider_metadata: dict[str, str] = field(default_factory=dict)
    author: str | None = None

    def to_candidate(self, *, normalized_url: str | None = None) -> CandidateItem:
        source_url = normalized_url or self.url
        stable_id = sha256(f"{source_url}|{self.title}".encode("utf-8")).hexdigest()[:16]
        return CandidateItem(
            id=f"candidate-{stable_id}",
            source_name=self.source_name,
            source_url=source_url,
            source_type=self.source_type,
            title=self.title,
            summary=self.excerpt,
            published_at=self.published_at,
            discovered_at=self.discovered_at,
            author=self.author,
        )


class DiscoveryProvider(Protocol):
    """Provider boundary for current, externally observed story candidates."""

    name: str

    def discover(
        self,
        query: str | None = None,
        since: datetime | None = None,
        limit: int = 20,
    ) -> list[DiscoveryResult]:
        ...


@dataclass(frozen=True)
class DiscoverySourceConfig:
    """Small configuration record for a discovery source/feed."""

    name: str
    url: str
    source_type: SourceType
    enabled: bool = True
    topics: list[str] = field(default_factory=list)


@dataclass
class DiscoveryRunMetrics:
    """Lightweight counters for a bounded discovery/research run."""

    provider: str
    queries_or_feeds_checked: int = 0
    results_discovered: int = 0
    duplicates_removed: int = 0
    retrieval_attempts: int = 0
    retrieval_successes: int = 0
    retrieval_failures: int = 0
    evidence_items_created: int = 0
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None

    @property
    def elapsed_seconds(self) -> float | None:
        if self.finished_at is None:
            return None
        return (self.finished_at - self.started_at).total_seconds()
