# Step 7E — Editorial Content Formats

Everything × AI now has explicit editorial formats:

- AI Brief
- Deep Dive
- Learn

These formats describe how verified editorial opportunities are packaged. They do not change verification, provenance, ranking, human approval, or rendering.

## Format Is Separate From Story

A story is a verified intelligence unit with its own evidence pack, claims, sources, timing, and editorial context. A format is the packaging strategy used after that story or group of stories is eligible for editorial review.

This separation matters because the same verified story may later support different outputs:

- a Deep Dive Reel
- a carousel slide in an AI Brief
- a long-form article
- an evergreen Learn explainer, if the grounding supports it

The story remains the trust boundary. The format is a presentation and editorial decision layer.

## Multi-Story Aggregation Without Evidence Merging

The AI Brief is a multi-story editorial collection. It is not a merged mega-story.

Each Brief item keeps:

- `story_id`
- `cluster_id`
- supporting claim references
- evidence references
- source references

Story A never gets to borrow Story B's evidence. This preserves the closed-world grounding model even when multiple stories appear in one package.

## AI Brief Selection

Brief selection is deterministic and transparent. A story must already have verified claims, sources, AI relevance, current or breaking timing, and sufficient editorial score.

The selection helper ranks eligible stories by existing editorial score and chooses at most 10. It does not invent a new opaque scoring model.

## Dynamic 3-10 Count

An AI Brief can contain 3 to 10 items. The system never forces the count to 5 or 10.

If only 3 worthwhile developments qualify, the Brief contains 3. If 7 qualify, it contains 7. If 12 qualify, the strongest 10 are selected and the rest remain available outside the Brief.

## Quality Thresholds vs Quotas

The Brief should not lower quality just to fill slides. A weak story remains ineligible even if the Brief would otherwise be short.

This is a content quality principle and an AI safety principle: deterministic thresholds prevent the system from padding output with under-supported material.

## Deep Dive

Deep Dive is a single-story format. It explains one important development through a structure such as:

- what happened
- how it works
- why it matters
- what it could mean
- what to watch

Career, upskill, or workflow implications are allowed only when supported by the selected angle and evidence. They are not forced into every Deep Dive.

## Learn

Learn is evergreen education grounded in verified material. It can originate from a verified evergreen opportunity or from verified story context converted into an educational concept.

Learn cannot generate arbitrary facts from model memory. It still needs a grounding boundary.

## Closed-World Generation Across Multi-Story Content

The future LLM generation path for AI Brief should operate item-by-item:

```text
Story A claims + evidence -> Story A slide
Story B claims + evidence -> Story B slide
Story C claims + evidence -> Story C slide
```

Then the validated slides are assembled into one Brief. The model should never see all stories as one blended factual universe for an individual slide.

## Provenance Isolation

Validation checks that each item uses only valid claims, evidence IDs, and source URLs from its own story. It rejects duplicate stories, invented source URLs, cross-story claim leakage, cross-story evidence leakage, unsupported numeric claims, and incorrect item counts.

## Strategy and Polymorphism

The `EditorialFormat` enum acts like a small strategy selector. Different formats can have different package models and validation rules while sharing the same upstream verified stories.

This is useful system design: one pipeline can produce multiple content strategies without rewriting discovery, research, verification, or planner logic.

## Composition vs Inheritance

The format packages use composition. An AI Brief contains items that reference verified stories. A Deep Dive references one verified story and one selected angle. A Learn package references grounding material.

The code does not subclass `PublishableContentPackage` because format recommendation is earlier than rendering and distribution. This avoids forcing unrelated package shapes into one inheritance tree.

## Renderer Compatibility

A future renderer can consume format-specific packages:

- AI Brief -> carousel renderer
- Deep Dive -> Reel, article, or carousel renderer
- Learn -> evergreen carousel or explainer renderer

Step 7E does not render anything. It only makes the format package renderer-ready.

## Human Override

Format recommendation is advisory. The human editor remains final authority. Recommendations are marked as requiring human approval and overrideable.

## Concept Connections

Python: dataclasses and enums model clear contracts.

OOP: format packages use explicit types instead of loosely shaped dictionaries.

Data structures: Brief items preserve ordered lists and per-story references.

System design: format selection sits after verification and before generation/rendering.

LLM grounding: future generation must respect each story's closed-world evidence boundary.

AI evals: validation tests catch leakage, invented sources, unsupported numerics, and quota padding.

Content systems: formats let the same intelligence pipeline support carousels, Reels, articles, newsletters, and explainers later.

FDE/product engineering: the system adds business-facing packaging without destabilizing the trust pipeline.

## Interview Questions

1. Why should a multi-story AI Brief avoid merging evidence packs?
2. What is the difference between story selection and content format recommendation?
3. Why is a dynamic 3-10 Brief count safer than a fixed slide quota?
4. How does composition help avoid overfitting every package to one content model?
5. What validation would you add before letting a carousel renderer consume an AI Brief package?

## Exercises Without Codex

1. Draw the data flow from three verified stories into one AI Brief while keeping evidence isolated.
2. Write three examples of stories that should be Deep Dive, AI Brief, and Learn respectively.
3. Explain how a human editor could override a format recommendation without weakening provenance.
