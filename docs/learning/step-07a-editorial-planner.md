# Step 7A — Editorial Planner

Everything × AI now has a deterministic layer that answers: what should I publish today?

The boundary is:

```text
Verified Stories
-> Editorial Planner
-> Timing + Lifecycle + Angle History
-> Daily Content Plan
-> Human Decision
-> future content generation
```

This step does not build a dashboard, generate a Reel, or publish to platforms. It produces auditable recommendations for a human editor.

## Editorial Planning

Editorial planning is a ranking and state-management problem. The planner receives verified stories and decides which angles are worth publishing now, which should be saved, which have expired, and which might belong in a bundle.

## State Machines and Lifecycle

`StoryLifecycleStatus` is a small state machine. Transitions such as `VERIFIED -> SELECTED` and `SELECTED -> PUBLISHED` are valid. Invalid transitions fail clearly. This keeps future dashboard actions predictable.

## Freshness vs Importance

`EditorialUrgency` describes timing: `BREAKING`, `CURRENT`, or `EVERGREEN`. It does not describe quality. A low-value breaking story can still be held, while a high-value evergreen explainer can still be useful.

## Shelf Life

`ShelfLife` describes how long the story remains useful as that angle. A news angle may expire, while a technology explainer from the same story can remain valid.

## Ranking

The planner combines editorial score, angle score, freshness, and urgency. It does not sort newest-first and does not lower thresholds to fill a quota.

## Scheduling

When source publication time exists, timing can produce a `publish_by` value. When publication time is unknown, the system does not invent one.

## Angle History

`AnglePublicationRecord` tracks what angle was already published for a story. This prevents republishing the same thesis with different wording while still allowing unused angles such as explainers or workflow impacts.

## Content Reuse

Follow-up logic depends on unused, materially different angles. A published story can remain valuable if strong unused angles still exist.

## Evergreen Strategy

`EvergreenItem` preserves a reusable opportunity with story ID, angle ID/type, thesis, claim references, audience, and review/expiry metadata. It is file-compatible and does not require a database.

## Story Relationships

`StoryRelationship` records lightweight relationships between stories without merging them. This keeps story isolation intact.

## Bundling

`BundleCandidate` recommends a possible combined post when multiple stories support a broader thesis. Bundles do not mutate the original stories and do not create a shared evidence pack.

## Provenance Across Bundles

Bundle candidates keep `claim_refs_by_story`, so each claim remains attributable to its originating verified story. Bundle-level interpretation stays an interpretation, not a new shared fact.

## Human-in-the-Loop Systems

`HumanEditorialDecision` records actions such as approve, save, hold, reject, keep separate, or approve bundle. These are human decisions, not model decisions.

## Deterministic vs Probabilistic Decisions

Timestamp math, expiration, angle-history checks, thresholds, lifecycle transitions, sorting, and duplicate publication prevention are deterministic. Future LLM assistance may help with relationship interpretation, but tests use no LLM.

## Auditability

Every `RecommendedPost` includes rationale strings: editorial score, angle score, timing rationale, and publication-history context. This makes recommendations inspectable in a future dashboard.

## Why 3 Posts Is a Target

Three posts per day is a planning target, not a quota. The planner can recommend fewer than three on weak days, more than three when multiple strong time-sensitive stories exist, or use evergreen/follow-up options on quiet days.

## Python and Data Structures

This step uses enums for controlled states, dataclasses for serializable planning records, and pure functions for deterministic lifecycle, timing, history, and relationship behavior.

## OOP and State Machines

`EditorialPlanner` coordinates smaller domain objects, while lifecycle transitions are isolated in `lifecycle.py`. This makes state behavior easier to test than if it were scattered across UI code.

## Ranking Systems

The planner is a simple ranking system with explicit weights. Production ranking systems often evolve into learned systems, but the first version should be understandable.

## System Design

The layer sits between verified intelligence and future UI/content generation. This gives the future dashboard stable objects to display without asking it to recalculate trust, timing, or duplicate-publication logic.

## AI Product Design and Safety

The system avoids engagement-bait pressure by refusing to manufacture weak posts to fill a slot. It separates verified claims, editorial recommendations, and human approval.

## FDE Workflows

In field engineering work, this pattern shows up often: translate trusted backend objects into planner recommendations, preserve provenance, expose rationale, and leave final approval to a human workflow.

## Interview Questions

1. Why should story urgency be separate from editorial value?
2. How does angle history prevent duplicate publication?
3. Why should bundles preserve claim provenance by originating story?
4. What makes a lifecycle enum safer than free-form status strings?
5. Why is a target post count different from a quota?

## Exercises Without Codex

1. Add a new lifecycle transition on paper and explain whether it should be valid.
2. Take one published story and list three materially different follow-up angles.
3. Design a bundle recommendation for two related stories while keeping their claims separate.
