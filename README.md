# Everything × AI

Everything × AI is an AI intelligence and multi-platform content pipeline.

The long-term flow is:

```text
Discover AI developments
-> retrieve public source material
-> acquire bounded evidence with provenance
-> normalize and cluster candidate coverage
-> build one-cluster EvidencePacks
-> run isolated closed-world analysis
-> validate claim-level provenance
-> create verified story analysis
-> score validated editorial angles
-> plan daily editorial recommendations
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

- `src/discovery/` finds candidate AI developments from replaceable providers, normalizes discovery metadata, and deduplicates obvious duplicate URLs before research.
- `src/intelligence/` normalizes candidates, clusters duplicate coverage, builds one-cluster evidence packs, validates claim provenance, creates verified story boundaries, scores angles, and prepares grounded title/hashtag metadata.
- `src/editorial/` plans what should be published next using timing, lifecycle state, angle history, bundle suggestions, evergreen opportunities, and human decision records.
- `src/research/` safely retrieves public sources, extracts useful text, chunks bounded evidence, and preserves provenance for the verified intelligence pipeline.
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

This repository contains the initial Python project structure, foundational domain models, the first content-generation layer, a deterministic rendering proof, a small testable intelligence pipeline, and a bounded live discovery/research layer.

Current architecture boundary:

```text
Live Sources
-> Discovery
-> Retrieval
-> Evidence Acquisition
-> Existing Verified Intelligence Pipeline
```

Editorial planning boundary:

```text
Verified Stories
-> Editorial Planner
-> Timing + Lifecycle + Angle History
-> Daily Content Plan
-> Human Decision
-> future content generation
```

Editorial format boundary:

```text
Verified Editorial Opportunities
        ↓
Editorial Format
        ↓
Human Approval
        ↓
Grounded Content
        ↓
Approved for Render
        ↓
Carousel Director
        ↓
Art Direction + Layout
        ↓
Visual QA
        ↓
PNG Carousel
        ↓
future Renderer
```

Local internal editorial dashboard:

```text
Editorial Planner
-> Editorial Command Center
-> Guided Story Review
-> Human Decision
-> Content Package Preview
-> Approve for Render
```

Content package boundary:

```text
Verified Story
-> Editorial Approval
-> Canonical Content Draft
-> Grounded Platform Adaptations
-> Content Validation
-> PublishableContentPackage
-> Human Review
-> future Renderer
```

Launch the LOCAL INTERNAL EDITORIAL DASHBOARD with:

```bash
streamlit run dashboard/app.py
```

The live discovery demo is manually invoked and bounded. It does not perform autonomous publishing, platform automation, or daily scheduling. Current hashtag popularity is not inferred by the LLM; Step 6 only preserves relevance signals when no defensible current reach data is available.
