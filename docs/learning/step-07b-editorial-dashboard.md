# Step 7B — Editorial Command Center

Everything × AI now has a local internal editorial dashboard. This is not the public website. It is the human decision surface for reviewing verified stories, daily recommendations, provenance, angles, bundles, evergreen opportunities, and session decisions.

## Why UI Is Justified Now

The backend can now discover sources, retrieve evidence, validate claims, create verified stories, score angles, and build daily editorial plans. A UI is justified because a human editor needs to inspect and approve the system's recommendations.

## Presentation vs Business Logic

The backend owns planning logic. The dashboard presents `DailyContentPlan`, `RecommendedPost`, `BundleCandidate`, `VerifiedGroundedStory`, `PotentialAngle`, `EvergreenItem`, and `HumanEditorialDecision` objects. It does not recalculate editorial thresholds.

## Streamlit Execution Model

Streamlit reruns the script after interactions. This makes it fast for local tools but requires session state for selections, pending confirmations, and decision logs.

## Session State

`dashboard/state.py` initializes session keys for the decision log, selected story, selected title, selected hashtags, and pending confirmations. This is local V1 state, not durable persistence.

## Event-Driven Interaction

Buttons map human actions to `HumanEditorialDecision`. Ordinary actions such as approve/save/hold are immediate. More significant actions such as reject and approve bundle require confirmation.

## View Models

`dashboard/view_models.py` converts backend objects into display-safe labels and rows. It handles missing timestamps, unknown hashtag reach, provenance rows, post slots, and metrics empty states.

## Human-in-the-Loop AI

The dashboard supports human judgment without pretending the model is the final publisher. The human can approve, save, hold, reject, keep stories separate, or approve a bundle.

## Provenance Visualization

Story Review shows claim-to-evidence-to-source rows. A user can expand a verified claim and inspect the evidence text plus source identity and URL.

## Decision Auditability

Each session decision becomes an audit entry such as `APPROVE — robotics-release`. Step 7B does not persist this to disk or a database.

## UI Trust Boundaries

The UI never turns raw candidates or unverified claims into approved facts. Manual titles are visibly marked `MANUAL — NOT AUTOMATICALLY VERIFIED`.

## Demo vs Live Data

Demo mode uses deterministic Step 7A fixture data and is clearly labeled `DEMO DATA`. Live boundary mode is honest: verified live orchestration is not wired yet, so it does not make network calls or pretend to be live.

## Empty and Error States

Empty plans, missing timestamps, unknown hashtag reach, no metrics, no bundles, and no evergreen items are valid states. The dashboard shows clear fallback messages instead of crashing.

## Why We Avoided React for V1

Streamlit is enough for a local internal editorial tool. React, an API layer, authentication, and database persistence would add complexity before the editorial workflow is proven.

## Future Evolution

Later, this could become a React app backed by a FastAPI service and database. At that point, decision logs, published records, metrics, and content-package state would move from session state into persistence.

## Python and Frontend/Backend Boundaries

Python dataclasses remain the backend contract. Streamlit renders those objects directly. This keeps the boundary easy to inspect during development.

## State Management

State is split into backend state models and UI session state. Backend models describe the editorial domain; session state describes the current local interaction.

## System Design

The dashboard sits after the planner and before future content packaging. That position protects the trust pipeline while giving the human a control surface.

## AI UX

Good AI UX explains why a recommendation exists, what evidence supports it, what is unknown, and what the human action will mean.

## FDE Workflows

This mirrors common FDE work: expose backend intelligence as an internal operator tool, preserve provenance, handle empty states, and make human decisions auditable.

## Human Oversight

Step 7B keeps the editor in charge. The system recommends; the human decides.

## Interview Questions

1. Why should dashboard code avoid duplicating planner thresholds?
2. What is the difference between session state and durable persistence?
3. How does provenance UI reduce trust risk in AI products?
4. Why should manual titles be marked as not automatically verified?
5. When would this Streamlit app need to evolve into React plus an API?

## Exercises Without Codex

1. Sketch a Story Review screen that shows claim, evidence, and source without JSON.
2. Add one decision-log entry by hand and identify what fields should be persisted later.
3. Describe how Live mode should work once verified live orchestration exists.

## UX Refactor — Guided Editorial Workflow

The first dashboard version was organized around backend capabilities: Daily Desk, Discovery, Story Review, Content Library, Published & Metrics, bundle review, provenance inspection, angle selection, and content package metadata. That structure was technically correct, but a dry run showed it did not match the editor's morning job.

The revised V1 workflow is organized around decisions:

```text
Today
-> understand the top story
-> choose direction, title, and hashtags
-> create the draft
-> approve for render
-> return to Today
```

Review and Create are stages inside the selected story workflow, not primary navigation destinations. This keeps the sidebar focused on the editor's durable workspaces: Today, Library, Published, and secondary Discovery.

Progressive disclosure is the central UX pattern. Today shows the headline, what happened, why it matters, timing, trust summary, status, and one primary next action. Claim IDs, package UUIDs, evidence IDs, raw ranking decimals, and model metadata stay out of the primary path. They remain available only where they help with trust or debugging.

Action hierarchy matters. The old story card displayed Review, Approve, Save, Hold, and Reject as equal actions. The refactor gives each story one primary action based on state: Review Story, Create Draft, Review Draft, or View Ready Content. Save, Hold, and Reject are secondary.

State visibility moved from the audit log into the interface. The audit log remains valuable, but the editor should see SAVED, HELD, APPROVED, DRAFT GENERATED, or READY FOR RENDER directly on the story. UI state is local Streamlit session state; domain state still lives in backend models such as `HumanEditorialDecision` and `PackageReviewState`.

Trust language now translates backend semantics. A verified fact is shown as VERIFIED FACT. An inference is shown as INTERPRETATION / REASONED INFERENCE. Rejected or unestablished material is shown as NOT ESTABLISHED / REJECTED. The claim -> evidence -> source chain is preserved behind View Sources & Evidence without making the editor read internal identifiers.

The Create stage previews actual generated content because a metadata summary cannot answer "what am I about to publish?" The editor now sees Reel hook, narration, scenes, CTA, Instagram caption and hashtags, plus compact previews for Blog, LinkedIn, X, TikTok, and YouTube.

Story approval and render approval are separate. Approving a story means the editor accepts the story direction for draft generation. Approving for render reuses the existing `APPROVED_FOR_RENDER` package review state after validation. This preserves the content safety boundary while making the workflow feel continuous.

Streamlit session state is enough for V1 because this is still a local internal command center. It holds selected story, selected angle/title/hashtags, generated packages, workflow stage, and recent decisions. Later persistence can move those records to a database without changing the core trust model.

Interview talking point:

> We initially built the dashboard around backend capabilities. A usability dry run exposed that technically correct information architecture was not the same as an effective user workflow. We redesigned around the editor's decisions while preserving the same underlying verification and provenance system.
