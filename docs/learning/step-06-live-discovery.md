# Step 6 — Live Discovery & Research

Everything × AI discovers meaningful AI developments, retrieves public source material, and prepares bounded evidence for the existing verified intelligence pipeline.

The key boundary is:

```text
Live Sources
-> Discovery
-> Retrieval
-> Evidence Acquisition
-> Existing Verified Intelligence Pipeline
```

Step 6 does not decide that retrieved text is true. It treats internet material as untrusted input and hands provenance-preserving evidence to Step 5B.

## Discovery vs Research vs Grounding

Discovery finds candidate developments. In this implementation, `RssFeedDiscoveryProvider` reads configured RSS/Atom feeds and produces `DiscoveryResult` records.

Research retrieves source material from candidate URLs using `SourceRetriever`. It records HTTP status, content type, final URL, retrieval time, and failure state.

Grounding remains downstream. Step 6 produces `EvidenceItem` objects, but claim validation and editorial judgment still belong to the existing verified intelligence pipeline.

## Provider Abstraction

`DiscoveryProvider` is a protocol:

```text
discover(query, since, limit) -> list[DiscoveryResult]
```

The rest of the system sees normalized discovery metadata, not vendor-specific feed objects. Future providers can be added without changing the intelligence pipeline.

## Dependency Injection

Network operations are injectable. RSS fetching and HTTP retrieval both accept fake transports in tests. This keeps unit tests deterministic and prevents accidental live network calls.

## HTTP Lifecycle

`SourceRetriever` checks URL safety, sends a bounded public HTTP/HTTPS request, follows only safe redirects, validates response size and content type, decodes text, and returns a `RetrievedSource`.

## HTTP Status Codes

Successful `2xx` and `3xx` responses may produce retrievable text after redirects. `404`, `429`, and other `4xx`/`5xx` responses are represented as explicit retrieval failures. They are not replaced with summaries.

## Timeouts

Requests use a timeout. Timeout failures become `RetrievalStatus.TIMEOUT`, allowing the run to continue with other sources.

## Redirects

Redirect destinations are checked with the same URL-safety boundary as original URLs. Redirects to localhost or private network addresses are rejected.

## Content Types

V1 accepts `text/html`, `application/xhtml+xml`, and `text/plain`. Unsupported types such as PDFs are rejected rather than parsed poorly.

## URL Normalization

`normalize_discovery_url` lowercases the scheme and host, removes fragments, and removes common tracking parameters such as `utm_*`, `fbclid`, and `gclid`. It avoids aggressive rewrites that might merge distinct resources.

## SSRF

Server-side request forgery is a risk whenever software retrieves externally supplied URLs. Step 6 rejects localhost, loopback IPs, private network ranges, link-local addresses, non-HTTP schemes, and malformed URLs.

## RSS/Atom

RSS/Atom is the first live discovery path because feeds are public, standards-based, and less brittle than search-result scraping. Feed parsing is defensive: malformed feeds or malformed entries do not crash the run.

## HTML Extraction

`ArticleTextExtractor` uses Python's `HTMLParser` to skip scripts, styles, navigation, headers, footers, forms, and other page chrome. It extracts readable text and marks extraction quality as `GOOD`, `POOR`, or `EMPTY`.

## Evidence Chunking

`EvidenceExtractor` chunks extracted text into deterministic bounded `EvidenceItem` records. This avoids dumping entire articles into later LLM analysis and preserves enough context for downstream validation.

## Provenance

Each evidence item keeps cluster ID, source ID, source URL, source type, supplied text, and publication timestamp when known. This lets later steps distinguish what a source actually supports.

## Primary vs Secondary Evidence

Source type is preserved from discovery configuration. A company feed can establish that the company reported something, but it does not automatically make that claim independently verified. Step 5B keeps that distinction through `EvidenceSource`.

## Rate Limiting

The live demo is bounded by discovery and retrieval limits and supports a delay between retrievals. It is not a crawler.

## Caching

No cache was added in Step 6. The current demo is small enough that cache complexity is not needed. If repeated development runs become noisy, a simple filesystem cache with TTL can be added later.

## Failure Isolation

Retrieval failure for one source does not stop the run. The runner records metrics and continues with the next candidate.

## Why Unit Tests Mock Network I/O

Unit tests must be fast, deterministic, and safe. Live network behavior changes over time and can fail for reasons unrelated to code correctness, so live behavior belongs in `scripts/discover_live.py`.

## Why LLMs Are Not Search Engines

An LLM can analyze supplied evidence, but it is not a current source of record. Step 6 uses live public sources for discovery and retrieval, then later analysis can work from bounded evidence.

## Precision vs Recall

Discovery can collect more candidates than the system publishes. Early filters remove only obvious duplicates. Semantically similar story clustering and editorial selection remain downstream.

## Hashtag Limitations

Step 6 does not scrape Instagram, TikTok, X, or other platforms and does not invent reach. It can generate relevance-first hashtag candidates from current topic terms, but reach stays unknown unless a defensible source exists.

## Scaling Considerations

Future scale would require stronger provider limits, persistent caching, retries with backoff, queueing, source-specific policies, and observability. Those are distributed-systems concerns and are intentionally out of scope for this bounded step.

For FDE work, this step mirrors common production boundaries: external APIs are wrapped, inputs are normalized, failures are explicit, security checks happen before network calls, and downstream systems receive typed data rather than raw vendor responses.

## Interview Questions

1. Why should discovery metadata be normalized before entering the intelligence pipeline?
2. What SSRF risks appear when a backend retrieves user-supplied URLs?
3. Why is a company announcement primary evidence but not necessarily independent evidence?
4. How does dependency injection make network-heavy code testable?
5. Why should retrieval failures be represented as data instead of exceptions that crash the run?

## Exercises Without Codex

1. Add one disabled RSS source to `config/discovery_sources.json` and explain which source type it should use.
2. Write a fake HTTP transport that returns a `429` response and verify the retriever result by hand.
3. Take a short HTML article and mark which parts should become evidence and which parts are page chrome.
