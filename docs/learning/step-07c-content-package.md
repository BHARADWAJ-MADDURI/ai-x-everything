# Step 7C — Content Package

Everything × AI now creates a grounded publishable content package after a human-approved verified story and selected angle. This is generation, not publication, and it does not render the final Reel.

## Generation Gates

`generation_readiness` requires a `VerifiedGroundedStory`, a human `APPROVE` decision, a validated angle, a selected title, verified claims, and provenance. `SAVE`, `HOLD`, and `REJECT` cannot enter generation.

## Canonical Content Architecture

The package starts with `CanonicalContentDraft`: hook, thesis, key points, explanation, implication, takeaway, CTA, and claim references. Platform outputs adapt from this shared knowledge base.

## Platform Adapters

Adapters create Reel, Instagram, blog, LinkedIn, X, TikTok, and YouTube Shorts outputs from the canonical draft. They change length, tone, and structure, not facts.

## Claim Allowlists

The selected angle determines the allowed claim IDs. Generation receives only those relevant verified claims, not every claim in the story.

## Closed-World Generation

Prompts tell the model to use only supplied verified claims and evidence. Missing information is omitted rather than filled from memory.

## Cross-Platform Factual Consistency

The package validator checks claim references, source references, platform emptiness, failed platform statuses, and numeric material. Deterministic checks cannot prove every sentence semantically, but they catch many common drift risks.

## Numeric Hallucination Validation

Percentages, currency figures, multipliers, and years in generated text must appear in the allowed verified claim text. Unsupported numbers fail validation.

## Partial Failure

Each platform output carries a status. If one adaptation fails, the package can exist, but publish readiness remains false.

## Human Approval Boundaries

Story approval is not final publication approval. Packages start as `DRAFT` or `NEEDS_REVIEW`; `APPROVED_FOR_RENDER` is a separate review state.

## Manual Titles

Manual titles are allowed but marked `MANUAL_UNVERIFIED`. They require explicit acknowledgement before render approval.

## Prompt Versioning

Step 7C adds `canonical_content_v1`, `reel_adaptation_v1`, and `platform_adaptation_v1` prompts so generation behavior can be audited and changed deliberately.

## Why Generation Is Not Publication

Generated copy can still contain mistakes or unsupported implications. The content package is a draft artifact for final human review and future rendering.

## Why One Canonical Draft Reduces Drift

Using one canonical draft prevents Instagram, LinkedIn, X, TikTok, and YouTube Shorts from each inventing separate narratives from raw evidence.

## Generative AI and Grounding

The LLM helps draft content, but the system constrains it with verified claims, claim IDs, source references, and deterministic validation.

## AI Evaluations

The validator is an evaluation layer. It checks reference integrity, numeric safety, manual-title state, platform failures, and review readiness.

## Python and Interfaces

Dataclasses model packages and adapters. A Pydantic schema validates structured canonical draft output from the LLM client.

## System Design

Step 7C sits between editorial approval and future rendering. This protects the pipeline from skipping from recommendation directly to published media.

## Content Systems

The package contains multiple platform views of one editorial artifact. This is closer to a content operating system than a single caption generator.

## Human-in-the-Loop AI

The editor approves the story, reviews the package, and later approves rendering. The model never becomes the final publisher.

## FDE Work

This step mirrors enterprise workflows where generated outputs need provenance, review states, validation, and auditability before entering an operational process.

## Interview Questions

1. Why should story approval be separate from package approval?
2. How does a claim allowlist reduce generation risk?
3. Why is one canonical draft safer than separate platform prompts from raw evidence?
4. What kinds of hallucinations can deterministic validation catch?
5. Why should manual titles require explicit acknowledgement?

## Exercises Without Codex

1. Take one verified claim and write three platform adaptations without changing the fact.
2. Identify which numbers in a draft need source support.
3. Design a package review checklist before rendering.
