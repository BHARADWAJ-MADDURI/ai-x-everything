# Step 04 Media Engine

Step 4B proves that the media layer can produce visually respectable, deterministic vertical video without paid or network calls.

## Pillow Owns Typography

This local FFmpeg build does not include `drawtext`, so typography is rendered into still scene assets with Pillow. That keeps wrapping, hierarchy, emphasis, labels, subtitles, and editorial primitives in Python where they are testable.

## FFmpeg Owns Composition

FFmpeg remains the composer and encoder. It turns deterministic scene frames into timed video, adds synthetic demo audio, and encodes the final MP4 as H.264 video with AAC audio.

## Typography Roles

The visual system resolves semantic typography roles instead of scattering font paths through render code:

- `DISPLAY`
- `EDITORIAL_SERIF`
- `SANS`
- `MONO`
- `CONDENSED_DISPLAY`

Dynamic Tech uses stronger condensed/display and mono accents. Editorial Human uses a serif headline with quieter sans support.

## Font Fallback

The `FontResolver` checks macOS system-font fallbacks in order and falls back safely to Pillow's default font if no preferred font exists. No font files are downloaded or bundled.

## Editorial Primitives

The reusable primitives include editorial rules, label pills, marker highlights, subtle grids, diagram cards/connectors, annotation/callout marks, and mobile-safe subtitles. They are deterministic and used intentionally per scene rather than applied everywhere.

## Safe Zones

The shared safe zone keeps important text and subtitles away from extreme top, bottom, and right edges so the same base output can later adapt to Instagram Reels, TikTok, and YouTube Shorts.

## Deterministic Style Resolution

`StyleResolver` maps `domain`, `ContentStyle`, and `EditorialTone` into a repeatable visual system. Domains remain strings so the taxonomy can evolve.

## Two Styles, Same Content

The same robotics demo content is rendered twice to prove art direction can change without changing the intelligence/content pipeline:

- `DYNAMIC_TECH`
- `EDITORIAL_HUMAN`

## Fixed Identity Across Themes

Across styles, AI × Everything keeps the same vertical format, series-label behavior, safe-zone discipline, subtitle philosophy, four-scene editorial structure, and outro signature.

## Scene-Level Art Direction

Step 4C adds a small `ScenePresentation` layer so each scene can request an existing content style while the video still has a global default. This lets a hook use an editorial treatment, a technology scene use a technical treatment, and the outro keep the brand signature without creating another style engine.

## Global Style vs Scene Override

The global `ContentStyle` remains the default. A scene override is explicit, deterministic, and caller-selected. There is no automatic tone detection, visual resolver, LLM classification, or domain-specific inference in the renderer.

## Semantic Decoration

Editorial primitives should earn their place. A rule, underline, callout, diagram connector, or label should emphasize, group, point, relate, or communicate progress. Step 4C removes decorative marks that did not communicate anything.

## Composition Before Decoration

The first response to empty space should be hierarchy, scale, spacing, and content-block placement. More shapes are not a substitute for better composition.

## Hybrid Visual Language

AI × Everything benefits from mixed visual language because the content often moves from editorial framing to technical explanation to human impact. A hybrid proof shows that the same canonical content can shift art direction by scene while preserving a recognizable publication identity.

## Stop Point for Local Renderer Polish

After 4C, local Pillow primitives have done enough to prove the rendering path. Future visual quality should primarily come from grounded source imagery, properly licensed photography or B-roll, real narration, richer source/data cards, stronger content quality, and selective motion rather than endlessly expanding programmatic primitives.
