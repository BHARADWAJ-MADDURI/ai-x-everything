from datetime import datetime, timezone
import unittest

from src.discovery.models import DiscoveryResult, DiscoverySourceConfig
from src.discovery.pipeline import LiveDiscoveryResearchRunner, normalize_discovery_results
from src.discovery.providers import RssFeedDiscoveryProvider
from src.discovery.urls import is_safe_public_http_url, normalize_discovery_url
from src.intelligence.models import HashtagResearchStatus, SourceType, StoryCluster, TargetPlatform
from src.intelligence.sources import evidence_from_candidate
from src.research.evidence import EvidenceExtractor
from src.research.extraction import ArticleTextExtractor, ExtractionQuality
from src.research.hashtags import CurrentEvidenceHashtagResearchProvider
from src.research.retrieval import HttpResponse, RetrievalStatus, SourceRetriever


FIXED_NOW = datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc)


def result(
    *,
    title: str = "New AI Robotics System",
    url: str = "https://example.com/story?utm_source=test",
    source_type: SourceType = SourceType.NEWS,
    published_at: datetime | None = FIXED_NOW,
) -> DiscoveryResult:
    return DiscoveryResult(
        title=title,
        url=url,
        source_name="Example Source",
        source_type=source_type,
        published_at=published_at,
        excerpt="A short externally supplied excerpt.",
        discovered_at=FIXED_NOW,
        provider="fake",
    )


class LiveDiscoveryTests(unittest.TestCase):
    def test_discovery_result_normalizes_to_candidate(self) -> None:
        candidate = normalize_discovery_results([result()])[0]

        self.assertTrue(candidate.id.startswith("candidate-"))
        self.assertEqual(candidate.source_url, "https://example.com/story")
        self.assertEqual(candidate.source_type, SourceType.NEWS)

    def test_missing_published_at_remains_none(self) -> None:
        candidate = normalize_discovery_results([result(published_at=None)])[0]

        self.assertIsNone(candidate.published_at)

    def test_timezone_aware_dates_are_preserved(self) -> None:
        candidate = normalize_discovery_results([result()])[0]

        self.assertIsNotNone(candidate.published_at)
        self.assertIsNotNone(candidate.published_at.tzinfo)

    def test_same_canonical_url_deduplicates(self) -> None:
        results = [
            result(url="https://example.com/story?utm_source=a"),
            result(url="https://EXAMPLE.com/story#section"),
        ]

        self.assertEqual(len(normalize_discovery_results(results)), 1)

    def test_utm_variants_deduplicate_where_safe(self) -> None:
        results = [
            result(url="https://example.com/story?utm_campaign=a"),
            result(url="https://example.com/story?utm_campaign=b"),
        ]

        self.assertEqual(len(normalize_discovery_results(results)), 1)

    def test_different_legitimate_urls_remain_separate(self) -> None:
        results = [
            result(url="https://example.com/story-a"),
            result(url="https://example.com/story-b", title="Different AI Story"),
        ]

        self.assertEqual(len(normalize_discovery_results(results)), 2)

    def test_url_safety_rejects_localhost(self) -> None:
        self.assertFalse(is_safe_public_http_url("http://localhost/story"))

    def test_url_safety_rejects_private_ipv4(self) -> None:
        self.assertFalse(is_safe_public_http_url("http://192.168.1.20/story"))

    def test_url_safety_rejects_link_local(self) -> None:
        self.assertFalse(is_safe_public_http_url("http://169.254.10.20/story"))

    def test_url_safety_rejects_non_http_scheme(self) -> None:
        self.assertFalse(is_safe_public_http_url("file:///etc/passwd"))

    def test_url_safety_accepts_public_https(self) -> None:
        self.assertTrue(is_safe_public_http_url("https://example.com/story"))

    def test_unsafe_redirect_is_rejected(self) -> None:
        retriever = SourceRetriever(
            transport=lambda *_: HttpResponse(
                status_code=200,
                final_url="http://127.0.0.1/internal",
                content_type="text/html",
                body=b"<p>text</p>",
            )
        )

        retrieved = retriever.retrieve("https://example.com/story")

        self.assertEqual(retrieved.retrieval_status, RetrievalStatus.UNSAFE_URL)

    def test_timeout_represented_as_failure(self) -> None:
        def timeout_transport(*_) -> HttpResponse:
            raise TimeoutError()

        retrieved = SourceRetriever(transport=timeout_transport).retrieve("https://example.com/story")

        self.assertEqual(retrieved.retrieval_status, RetrievalStatus.TIMEOUT)

    def test_404_represented_as_failure(self) -> None:
        retrieved = SourceRetriever(
            transport=lambda *_: HttpResponse(404, "https://example.com/missing", "text/html", b"")
        ).retrieve("https://example.com/missing")

        self.assertEqual(retrieved.retrieval_status, RetrievalStatus.HTTP_ERROR)

    def test_429_represented_as_failure(self) -> None:
        retrieved = SourceRetriever(
            transport=lambda *_: HttpResponse(429, "https://example.com/rate", "text/html", b"")
        ).retrieve("https://example.com/rate")

        self.assertEqual(retrieved.retrieval_status, RetrievalStatus.HTTP_ERROR)

    def test_unsupported_content_type_rejected(self) -> None:
        retrieved = SourceRetriever(
            transport=lambda *_: HttpResponse(200, "https://example.com/file", "application/pdf", b"%PDF")
        ).retrieve("https://example.com/file")

        self.assertEqual(retrieved.retrieval_status, RetrievalStatus.UNSUPPORTED_CONTENT_TYPE)

    def test_oversized_response_handled_safely(self) -> None:
        retrieved = SourceRetriever(
            max_response_bytes=5,
            transport=lambda *_: HttpResponse(200, "https://example.com/story", "text/html", b"abcdef"),
        ).retrieve("https://example.com/story")

        self.assertEqual(retrieved.retrieval_status, RetrievalStatus.TOO_LARGE)

    def test_useful_html_text_extraction_works(self) -> None:
        extracted = ArticleTextExtractor().extract(_html_with_article(), "text/html")

        self.assertEqual(extracted.title, "Useful AI Story")
        self.assertEqual(extracted.quality, ExtractionQuality.GOOD)
        self.assertIn("Robotics teams are testing AI systems", extracted.text)

    def test_empty_or_poor_extraction_is_marked(self) -> None:
        empty = ArticleTextExtractor().extract("<html><body><nav>menu</nav></body></html>", "text/html")
        poor = ArticleTextExtractor().extract("<p>Too short.</p>", "text/html")

        self.assertEqual(empty.quality, ExtractionQuality.EMPTY)
        self.assertEqual(poor.quality, ExtractionQuality.POOR)

    def test_article_boilerplate_is_reduced(self) -> None:
        extracted = ArticleTextExtractor().extract(
            "<html><body><nav>Navigation menu</nav><article><p>Important AI evidence appears in this paragraph with enough useful context for extraction.</p></article></body></html>",
            "text/html",
        )

        self.assertNotIn("Navigation menu", extracted.text)

    def test_evidence_retains_source_provenance_and_cluster_scope(self) -> None:
        candidate = normalize_discovery_results([result(source_type=SourceType.COMPANY)])[0]
        cluster = StoryCluster(id="cluster-1", candidates=[candidate])
        retrieved = _retrieved_success()
        extracted = ArticleTextExtractor().extract(_html_with_article(), "text/html")

        items = EvidenceExtractor(max_items_per_source=2, max_chars_per_item=300).extract(
            cluster=cluster,
            candidate=candidate,
            retrieved_source=retrieved,
            extracted_text=extracted,
            source_index=1,
        )

        self.assertEqual(items[0].cluster_id, "cluster-1")
        self.assertEqual(items[0].source_id, "source_001")
        self.assertEqual(items[0].source_url, "https://example.com/story")
        self.assertEqual(items[0].source_type, SourceType.COMPANY)

    def test_evidence_chunk_limits_work(self) -> None:
        candidate = normalize_discovery_results([result()])[0]
        cluster = StoryCluster(id="cluster-1", candidates=[candidate])
        extracted = ArticleTextExtractor().extract(_html_with_article(), "text/html")

        items = EvidenceExtractor(max_items_per_source=1, max_chars_per_item=180).extract(
            cluster=cluster,
            candidate=candidate,
            retrieved_source=_retrieved_success(),
            extracted_text=extracted,
        )

        self.assertEqual(len(items), 1)
        self.assertLessEqual(len(items[0].supplied_text), 181)

    def test_failed_source_does_not_crash_discovery_run(self) -> None:
        provider = FakeDiscoveryProvider([result(), result(title="Second AI Story", url="https://example.com/two")])
        retriever = SourceRetriever(
            transport=lambda *_: HttpResponse(404, "https://example.com/story", "text/html", b"")
        )

        run = LiveDiscoveryResearchRunner(provider=provider, retriever=retriever).run(retrieval_limit=2)

        self.assertEqual(run.metrics.retrieval_failures, 2)
        self.assertEqual(run.metrics.evidence_items_created, 0)

    def test_malformed_feed_entry_does_not_crash_feed(self) -> None:
        provider = RssFeedDiscoveryProvider(
            [DiscoverySourceConfig(name="Feed", url="https://example.com/feed", source_type=SourceType.NEWS)],
            fetcher=lambda *_: "<rss><channel><item><title>No link</title></item></channel></rss>",
            clock=lambda: FIXED_NOW,
        )

        self.assertEqual(provider.discover(limit=5), [])

    def test_feed_provider_preserves_source_type_and_missing_date(self) -> None:
        provider = RssFeedDiscoveryProvider(
            [DiscoverySourceConfig(name="Research Feed", url="https://example.com/feed", source_type=SourceType.RESEARCH)],
            fetcher=lambda *_: "<rss><channel><item><title>Paper</title><link>https://example.com/paper</link></item></channel></rss>",
            clock=lambda: FIXED_NOW,
        )

        discovered = provider.discover(limit=5)

        self.assertEqual(discovered[0].source_type, SourceType.RESEARCH)
        self.assertIsNone(discovered[0].published_at)

    def test_fake_discovery_provider_is_deterministic(self) -> None:
        provider = FakeDiscoveryProvider([result()])

        self.assertEqual(provider.discover(), provider.discover())

    def test_fake_retriever_is_deterministic(self) -> None:
        retriever = SourceRetriever(transport=lambda *_: _http_success())

        self.assertEqual(retriever.retrieve("https://example.com/story").raw_text, retriever.retrieve("https://example.com/story").raw_text)

    def test_primary_source_is_not_automatically_independent_evidence(self) -> None:
        candidate = normalize_discovery_results([result(source_type=SourceType.COMPANY)])[0]
        evidence_source = evidence_from_candidate(candidate)

        self.assertFalse(evidence_source.is_independent)
        self.assertIn("company_announcement", evidence_source.authoritative_for)

    def test_no_llm_is_used_as_discovery_source(self) -> None:
        provider = RssFeedDiscoveryProvider(
            [DiscoverySourceConfig(name="Feed", url="https://example.com/feed", source_type=SourceType.NEWS)],
            fetcher=lambda *_: "<rss />",
        )

        self.assertEqual(provider.name, "rss")

    def test_hashtag_research_never_invents_reach(self) -> None:
        results = CurrentEvidenceHashtagResearchProvider(researched_at=FIXED_NOW).research(
            ["robotics", "vision language action"],
            TargetPlatform.INSTAGRAM,
        )

        self.assertTrue(results)
        self.assertTrue(all(item.estimated_reach_band is None for item in results))
        self.assertTrue(all(item.competition_band is None for item in results))

    def test_unresearched_hashtag_status_remains_available_without_current_signal(self) -> None:
        self.assertEqual(HashtagResearchStatus.UNRESEARCHED.value, "unresearched")

    def test_run_metrics_count_successes_and_failures(self) -> None:
        responses = iter([
            _http_success(),
            HttpResponse(404, "https://example.com/two", "text/html", b""),
        ])
        provider = FakeDiscoveryProvider([result(), result(title="Second AI Story", url="https://example.com/two")])
        run = LiveDiscoveryResearchRunner(
            provider=provider,
            retriever=SourceRetriever(transport=lambda *_: next(responses)),
        ).run(retrieval_limit=2)

        self.assertEqual(run.metrics.results_discovered, 2)
        self.assertEqual(run.metrics.retrieval_attempts, 2)
        self.assertEqual(run.metrics.retrieval_successes, 1)
        self.assertEqual(run.metrics.retrieval_failures, 1)
        self.assertGreater(run.metrics.evidence_items_created, 0)

    def test_normalize_url_removes_fragments_without_aggressive_rewrite(self) -> None:
        self.assertEqual(
            normalize_discovery_url("https://Example.com/path?a=1&utm_source=x#frag"),
            "https://example.com/path?a=1",
        )


class FakeDiscoveryProvider:
    name = "fake"

    def __init__(self, results: list[DiscoveryResult]) -> None:
        self.results = results

    def discover(self, query=None, since=None, limit=20) -> list[DiscoveryResult]:
        return self.results[:limit]


def _http_success() -> HttpResponse:
    return HttpResponse(
        status_code=200,
        final_url="https://example.com/story",
        content_type="text/html; charset=utf-8",
        body=_html_with_article().encode("utf-8"),
    )


def _retrieved_success():
    return SourceRetriever(transport=lambda *_: _http_success()).retrieve("https://example.com/story")


def _html_with_article() -> str:
    return """
    <html>
      <head><title>Useful AI Story</title></head>
      <body>
        <nav>Navigation menu should disappear</nav>
        <article>
          <p>Robotics teams are testing AI systems that connect vision, language, and action planning in controlled factory settings.</p>
          <p>The reported development matters because it may change how technicians configure robots, but the source text still needs downstream validation.</p>
          <p>Researchers and companies describe the work as early, bounded, and dependent on careful evaluation before real deployment.</p>
        </article>
      </body>
    </html>
    """


if __name__ == "__main__":
    unittest.main()
