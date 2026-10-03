# AI × Everything

AI × Everything is an AI intelligence and multi-platform content pipeline.

The long-term flow is:

```text
Discover AI developments
-> normalize and cluster candidate coverage
-> build one-cluster EvidencePacks
-> run isolated closed-world analysis
-> validate claim-level provenance
-> create verified story analysis
-> score validated editorial angles
-> select stories for content generation
-> generate grounded title metadata
-> prepare researched-hashtag data contracts
-> generate platform-independent content
-> render media
-> distribute through platform adapters
-> collect analytics
-> evaluate performance
```

Instagram Reels is the first distribution target, but the core architecture is platform-independent so YouTube Shorts, TikTok, LinkedIn, X, and other platforms can be added later without changing the intelligence pipeline.

## Project Structure

- `src/discovery/` finds candidate AI developments and story signals.
- `src/intelligence/` normalizes candidates, clusters duplicate coverage, builds one-cluster evidence packs, validates claim provenance, creates verified story boundaries, scores angles, and prepares grounded title/hashtag metadata.
- `src/research/` gathers sources and grounds candidate stories in evidence.
- `src/analysis/` normalizes, deduplicates, classifies, and scores stories.
- `src/content/` produces platform-independent content plans, scripts, and metadata.
- `src/rendering/` turns content plans into media assets.
- `src/distribution/` contains platform adapters for publishing rendered content.
- `src/analytics/` collects performance data from distribution platforms.
- `src/shared/` holds cross-cutting types, utilities, and configuration helpers.
- `prompts/` stores prompt templates used by the pipeline.
- `data/` stores local input data and development fixtures.
- `output/` stores generated local artifacts.
- `tests/` contains automated tests.

## Current Status

This repository contains the initial Python project structure, foundational domain models, the first content-generation layer, a deterministic rendering proof, and a small testable intelligence pipeline for candidate normalization, clustering, evidence packs, claim validation, verified analysis, angle scoring, editorial selection, grounded titles, and hashtag metadata contracts. It does not perform live automated news discovery yet. Current hashtag popularity is not inferred by the LLM; live/current hashtag research will be connected separately.
