# Step 7D-A — Production AI Brief Carousel Engine

Step 7D-A adds the first production media renderer for Everything × AI: a static AI Brief carousel engine.

It consumes a validated `AIBriefPackage` and renders Instagram-ready 1080×1350 PNG slides. It does not research, summarize with an LLM, render video, publish, or call external APIs.

## Data Boundary

The renderer accepts already validated editorial-format objects:

```text
AIBriefPackage
-> Carousel Director
-> Slide Models
-> Art Direction Resolver
-> Layout Engine
-> Pillow Renderer
-> Visual QA
-> PNG Slides + Contact Sheet
```

Rendering is presentation. It must not invent facts, change claims, merge stories, or replace source provenance.

## Carousel Structure

For `N` Brief items, the renderer produces:

- slide 1: cover
- slides 2 through `N + 1`: one story per slide
- final slide: outro

A 5-item Brief produces 7 slides.

## Canvas and Safe Margins

The carousel canvas is centralized in `CarouselCanvasConfig`:

- width: 1080
- height: 1350
- safe margins: left 84, top 90, right 996, bottom 1260

Critical text is checked against the safe area.

## Typography

Typography uses the existing `FontResolver` and semantic roles:

- editorial headline: serif where available
- dynamic headline: condensed display where available
- labels/source lines: mono
- body copy: readable sans

The layout fits text by wrapping first and then reducing font size within bounded limits. Overflow is surfaced to QA instead of silently hiding content.

## Art Direction

The carousel supports bounded semantic treatments:

- editorial neutral
- technical
- research
- clinical
- industrial
- policy

The resolver uses story category/headline semantics with a neutral fallback. It does not blindly assign colors based only on domain.

## Two Variants

### Editorial

The Editorial variant is a premium publication treatment: light paper background, serif headlines, spacious composition, restrained rules, and editorial motifs.

### Dynamic

The Dynamic variant is a technology intelligence treatment: dark structured background, technical grid, condensed headlines, diagram-like motifs, and stronger label hierarchy.

Both variants retain the Everything × AI identity.

## Contact Sheets

Each variant generates a contact sheet so a human can quickly inspect:

- sequence
- hierarchy
- pacing
- density
- consistency
- branding

## Visual QA

Automated QA checks:

- expected dimensions
- slide count
- missing headline
- missing source attribution
- duplicate slide positions
- cover count mismatch
- text outside safe margins
- text overlap
- tiny font warnings
- PNG validity

Automated QA is not a substitute for human review. It catches mechanical failures and obvious layout defects.

## Visual Dry Run

Rendered demo outputs:

- `output/carousels/ai_brief_editorial/`
- `output/carousels/ai_brief_dynamic/`

Observed after the correction pass:

- slide count matched the 5-item Brief: 7 slides per variant
- cover hierarchy was readable
- story slides preserved one story per slide
- source attribution was visible without raw URLs
- contact sheets were useful for comparing pacing
- no clipping or duplicate slide-key/rendering issue was observed
- variants were structurally different, not merely recolored

Known visual limitations:

- fixture text is intentionally plain, so visual quality is better than editorial copy quality
- deterministic abstract motifs are placeholders for future grounded imagery
- automated QA does not measure aesthetics, only layout contracts

## Correction Pass

The first QA pass flagged story-slide brand labels above the safe top margin. The layout was corrected so brand labels sit inside centralized safe margins. Rendering was then repeated.

## Future Renderer Consumption

The renderer-ready package structure can later support:

- carousel export workflows
- human review in the dashboard
- image asset sourcing
- platform-specific packaging

Step 7D-A intentionally stops before video, TTS, music, publishing, scheduling, or asset APIs.

## Interview Questions

1. Why should rendering accept validated package objects rather than raw discovered stories?
2. What is the difference between visual QA and human design review?
3. Why centralize canvas dimensions and safe margins?
4. How do art-direction presets avoid both chaos and one-template monotony?
5. Why is source attribution visible while raw source URLs remain hidden?

## Exercises Without Codex

1. Sketch a 5-slide AI Brief contact sheet and label which data object feeds each slide.
2. List three layout failures automated QA can catch and three it cannot.
3. Propose a grounded-image extension that does not weaken story provenance.
