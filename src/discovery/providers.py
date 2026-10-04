from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
from pathlib import Path
import ssl
from typing import Callable
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from src.discovery.models import DiscoveryResult, DiscoverySourceConfig
from src.intelligence.models import SourceType


FeedFetcher = Callable[[str, float], str]
Clock = Callable[[], datetime]


def load_discovery_sources(path: str | Path) -> list[DiscoverySourceConfig]:
    raw_sources = json.loads(Path(path).read_text(encoding="utf-8"))
    sources = []
    for raw in raw_sources:
        sources.append(
            DiscoverySourceConfig(
                name=raw["name"],
                url=raw["url"],
                source_type=SourceType(raw.get("source_type", SourceType.OTHER.value)),
                enabled=raw.get("enabled", True),
                topics=list(raw.get("topics", [])),
            )
        )
    return sources


class RssFeedDiscoveryProvider:
    """RSS/Atom discovery provider with injectable network I/O."""

    name = "rss"

    def __init__(
        self,
        sources: list[DiscoverySourceConfig],
        *,
        fetcher: FeedFetcher | None = None,
        clock: Clock | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.sources = [source for source in sources if source.enabled]
        self.fetcher = fetcher or _default_feed_fetcher
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.timeout_seconds = timeout_seconds
        self.feeds_checked = 0

    def discover(
        self,
        query: str | None = None,
        since: datetime | None = None,
        limit: int = 20,
    ) -> list[DiscoveryResult]:
        results: list[DiscoveryResult] = []
        self.feeds_checked = 0
        matching_sources = [
            source
            for source in self.sources
            if not query or not source.topics or query.lower() in {topic.lower() for topic in source.topics}
        ]
        per_source_limit = max(1, limit // max(1, len(matching_sources)))
        for source in self.sources:
            if query and source.topics and query.lower() not in {topic.lower() for topic in source.topics}:
                continue
            self.feeds_checked += 1
            try:
                feed_text = self.fetcher(source.url, self.timeout_seconds)
            except Exception:
                continue
            results.extend(_parse_feed(feed_text, source, discovered_at=self.clock(), since=since)[:per_source_limit])
        return results[:limit]


def _default_feed_fetcher(url: str, timeout_seconds: float) -> str:
    request = Request(url, headers={"User-Agent": "Everything-x-AI/0.1 discovery"})
    with urlopen(request, timeout=timeout_seconds, context=_ssl_context()) as response:
        return response.read(5_000_000).decode("utf-8", errors="replace")


def _ssl_context() -> ssl.SSLContext:
    cafile = Path("/etc/ssl/cert.pem")
    if cafile.exists():
        return ssl.create_default_context(cafile=str(cafile))
    return ssl.create_default_context()


def _parse_feed(
    feed_text: str,
    source: DiscoverySourceConfig,
    *,
    discovered_at: datetime,
    since: datetime | None,
) -> list[DiscoveryResult]:
    try:
        root = ET.fromstring(feed_text)
    except ET.ParseError:
        return []
    entries = _rss_entries(root) or _atom_entries(root)
    results = []
    for entry in entries:
        title = _entry_text(entry, ("title",))
        url = _entry_link(entry)
        if not title or not url:
            continue
        published_at = _parse_datetime(
            _entry_text(entry, ("pubDate", "published", "updated", "date"))
        )
        if since and published_at and published_at < since:
            continue
        results.append(
            DiscoveryResult(
                title=_clean(title),
                url=_clean(url),
                source_name=source.name,
                source_type=source.source_type,
                published_at=published_at,
                excerpt=_clean(_entry_text(entry, ("description", "summary", "content")) or "") or None,
                discovered_at=discovered_at,
                provider="rss",
                provider_metadata={"feed_url": source.url},
                author=_clean(_entry_text(entry, ("author", "creator")) or "") or None,
            )
        )
    return results


def _rss_entries(root: ET.Element) -> list[ET.Element]:
    return [element for element in root.iter() if _local_name(element.tag) == "item"]


def _atom_entries(root: ET.Element) -> list[ET.Element]:
    return [element for element in root.iter() if _local_name(element.tag) == "entry"]


def _entry_text(entry: ET.Element, names: tuple[str, ...]) -> str | None:
    for child in entry.iter():
        if _local_name(child.tag) in names and child.text:
            return child.text
    return None


def _entry_link(entry: ET.Element) -> str | None:
    for child in entry.iter():
        if _local_name(child.tag) != "link":
            continue
        href = child.attrib.get("href")
        if href:
            return href
        if child.text:
            return child.text
    return None


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _clean(value: str) -> str:
    return " ".join(value.split())
