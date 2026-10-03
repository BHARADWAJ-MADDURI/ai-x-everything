# AI × Everything

AI × Everything is an AI intelligence and multi-platform content pipeline.

The long-term flow is:

```text
Discover AI developments
-> research and source-ground them
-> normalize and deduplicate stories
-> analyze/classify/score them
-> generate platform-independent content
-> render media
-> distribute through platform adapters
-> collect analytics
-> evaluate performance
```

Instagram Reels is the first distribution target, but the core architecture is platform-independent so YouTube Shorts, TikTok, LinkedIn, X, and other platforms can be added later without changing the intelligence pipeline.

## Project Structure

- `src/discovery/` finds candidate AI developments and story signals.
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

This repository contains the initial Python project structure, foundational domain models, and the first content-generation layer for converting a grounded `Story` into an `Article` and platform-independent short-video plan.
