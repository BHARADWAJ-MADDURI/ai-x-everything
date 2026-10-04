import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.discovery.pipeline import LiveDiscoveryResearchRunner
from src.discovery.providers import RssFeedDiscoveryProvider, load_discovery_sources
from src.research.retrieval import SourceRetriever

DEFAULT_CONFIG = ROOT / "config" / "discovery_sources.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a small Everything × AI live discovery demo.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--query", default=None)
    parser.add_argument("--discover-limit", type=int, default=10)
    parser.add_argument("--retrieve-limit", type=int, default=3)
    parser.add_argument("--delay", type=float, default=0.5)
    args = parser.parse_args()

    sources = load_discovery_sources(args.config)
    provider = RssFeedDiscoveryProvider(sources)
    runner = LiveDiscoveryResearchRunner(
        provider=provider,
        retriever=SourceRetriever(),
        request_delay_seconds=args.delay,
    )
    run = runner.run(
        query=args.query,
        discovery_limit=args.discover_limit,
        retrieval_limit=args.retrieve_limit,
    )

    print("EVERYTHING × AI — LIVE DISCOVERY")
    print("Understand what's changing.")
    print()
    for index, candidate in enumerate(run.candidates, start=1):
        print("DISCOVERED")
        print("----------")
        print(f"Title: {candidate.title}")
        print(f"Source: {candidate.source_name} ({candidate.source_type.value})")
        print(f"Published: {candidate.published_at.isoformat() if candidate.published_at else 'unknown'}")
        print(f"URL: {candidate.source_url}")
        attempt = next((item for item in run.attempts if item.candidate.id == candidate.id), None)
        if attempt:
            print()
            print("RETRIEVAL")
            print("---------")
            print(f"Status: {attempt.retrieved_source.retrieval_status.value}")
            print(f"Content type: {attempt.retrieved_source.content_type or 'unknown'}")
            print(f"Characters extracted: {len(attempt.extracted_text.text)}")
            print(f"Extraction quality: {attempt.extracted_text.quality.value}")
            print()
            print("EVIDENCE")
            print("--------")
            print(f"Evidence items: {len(attempt.evidence_items)}")
            for evidence in attempt.evidence_items[:2]:
                preview = evidence.supplied_text[:180].replace("\n", " ")
                print(f"- {preview}")
            print()
            print(f"READY FOR INTELLIGENCE: {'YES' if attempt.ready_for_intelligence else 'NO'}")
            reason = "bounded evidence acquired" if attempt.ready_for_intelligence else (
                attempt.retrieved_source.error or "insufficient extracted evidence"
            )
            print(f"Reason: {reason}")
        print()
        if index >= args.discover_limit:
            break

    print("RUN METRICS")
    print("-----------")
    print(f"Provider: {run.metrics.provider}")
    print(f"Feeds checked: {run.metrics.queries_or_feeds_checked}")
    print(f"Results discovered: {run.metrics.results_discovered}")
    print(f"Duplicates removed: {run.metrics.duplicates_removed}")
    print(f"Retrieval attempts: {run.metrics.retrieval_attempts}")
    print(f"Retrieval successes: {run.metrics.retrieval_successes}")
    print(f"Retrieval failures: {run.metrics.retrieval_failures}")
    print(f"Evidence items created: {run.metrics.evidence_items_created}")
    print(f"Elapsed seconds: {run.metrics.elapsed_seconds:.2f}" if run.metrics.elapsed_seconds is not None else "Elapsed seconds: unknown")


if __name__ == "__main__":
    main()
