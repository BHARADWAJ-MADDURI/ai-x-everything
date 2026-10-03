# Step 05 Intelligence Engine

Step 5 adds the upstream intelligence layer that turns discovered candidate items into grounded, scored editorial possibilities. It is intentionally small and deterministic: no crawler, no scraping, no network calls, no vector database, and no autonomous agent.

## Candidate Ingestion vs Trusted Information

`CandidateItem` represents untrusted discovery input. It is something found elsewhere, not a verified story. Treating candidates as untrusted data is a basic API and system-design boundary: input models are not the same as domain truth.

## Normalization

Normalization cleans whitespace, removes safe URL tracking parameters, normalizes source names, and preserves factual meaning. This is a data-structure hygiene step that makes later comparison more reliable without rewriting the story.

## Deduplication And Story Clustering

`StoryCluster` groups likely duplicate coverage using canonical URLs and conservative title-token overlap. This is a precision-over-recall information retrieval choice: it is better to miss a duplicate than merge unrelated developments.

## Primary vs Secondary Evidence

`EvidenceSource` distinguishes evidence role and independence. A company source can be authoritative about what it announced, but it is not automatically independent proof that the announcement will transform an industry.

## Fact vs Inference vs Interpretation

`GroundedFact` stores `ClaimKind`: `FACT`, `INFERENCE`, or `INTERPRETATION`. Downstream content needs this distinction so it can avoid presenting possible implications as established facts.

## Provenance

Every grounded fact keeps supporting source URLs. Provenance is the trace from a claim back to evidence, and it is essential for source-grounded writing, evaluation, and editorial review.

## Structured LLM Analysis

`StoryAnalysisOutput` is a Pydantic boundary for structured LLM output. The internal representation remains dataclass-based, while Pydantic validates external model output. Tests use fake clients.

## LLMs Are Not Sources

The LLM may summarize supplied evidence, but it does not create evidence. It receives candidates and grounded facts, and its output must not invent industries, professions, metrics, or implications.

## Angle Generation

`PotentialAngle` captures possible editorial frames such as `TECHNOLOGY`, `INDUSTRY_IMPACT`, `CAREER`, `UPSKILL`, and `RISK_LIMITATION`. Fewer defensible angles are preferred over many weak ones.

## Career And Upskill Gates

Career and upskill angles require a chain from development to technology/application to workflow to profession/task to useful implication. Missing that chain causes deterministic rejection.

## Deterministic Scoring

The scoring formula rewards evidence strength, relevance, novelty, and usefulness, and penalizes speculation risk. This is a transparent ranking system, not a mysterious AI quality score.

## Selection

Selection returns `SELECT`, `HOLD`, or `REJECT`. It avoids selecting duplicate clusters twice, allows strong technology stories without career content, and rejects low-evidence hype.

## Precision vs Recall

The current system prefers precision. It may miss some weak or ambiguous opportunities, but that is better than fabricating relevance. This is especially important for career and upskill content.

## Prefer Missing Weak Angles

AI × Everything should not force AI into every domain or profession. Missing a weak angle is acceptable; inventing one damages trust.

## Current Limitations

The implementation does not crawl the web, search social platforms, use embeddings, persist to a database, or perform real-time discovery. Deduplication is conservative and lexical. Analysis quality depends on supplied evidence and, when used, structured LLM output.

## Story Isolation

Step 5B hardens analysis around one story cluster at a time. Each `EvidencePack` belongs to one `StoryCluster`, and analysis should receive only that pack. This is a system-design boundary that prevents cross-story information leakage.

## Closed-World LLM Calls

The LLM is not a source of truth. A structured analysis call treats the supplied evidence pack as the complete factual universe. If the pack does not establish a field, `UNKNOWN` or an empty list is a valid output.

## Evidence Packs And Stable IDs

`EvidencePack` contains stable application-assigned source and evidence IDs. The LLM may reference these IDs, but it may not create source IDs, evidence IDs, URLs, authors, dates, or organizations.

## Claim-Level Provenance

`VerifiedClaimCandidate` makes claim provenance explicit. Every `FACT` requires evidence IDs. `INFERENCE` and `INTERPRETATION` keep their labels rather than being silently upgraded into facts.

## Deterministic Claim Validation

`validate_claims` rejects unknown evidence IDs, invented source IDs, invented URLs, FACT claims with no evidence, and unsupported numeric facts. Invalid claims are quarantined and cannot enter the verified story boundary.

## Hallucination Containment

The system cannot guarantee that an LLM never proposes a bad claim. Instead, it contains hallucination risk by validating claims before downstream generation. This is hallucination containment, not hallucination elimination.

## Numeric Claims

Numbers require direct evidence. If a claim says `40%`, the supporting evidence text must establish `40%`. The system does not estimate missing numbers.

## Generation Trust Boundary

`VerifiedGroundedStory` is the object downstream generation and publishing metadata should consume. Raw candidates, raw LLM output, and rejected claims should not cross this boundary.

## Grounded Title Generation

`TitleCandidate` tracks type, target platform, clarity, hype risk, and supporting verified claim IDs. Unsupported hype or unsupported factual titles are rejected rather than rewritten with invented claims.

## Hashtag Popularity Requires Live Research

The system does not ask an LLM for "popular hashtags." Popularity changes by platform and time, so reach must come from future live research. Without research, `estimated_reach_band` remains `None`.

## Relevance vs Reach

Hashtag selection prioritizes story relevance and specificity. A broad or high-reach tag with near-zero relevance is rejected. Relevance beats fake popularity.

## Why We Do Not Invent Popular Hashtags

LLM memory is not current platform research. Step 5B defines the data contract and deterministic selection logic; Step 6 can connect real research sources.

## Interview Questions

1. Why separate untrusted candidate input from grounded story models?
2. How does provenance reduce hallucination risk in an LLM-assisted pipeline?
3. Why is conservative deduplication preferable for editorial systems?
4. How would you explain the scoring formula to an editor?
5. What tests would you add before connecting live discovery APIs?
6. Why is an evidence pack a useful boundary for closed-world LLM calls?
7. How should a system handle useful but unsupported numeric claims?
8. Why is `UNKNOWN` often better than a plausible guess?
9. Why should hashtag reach come from live research instead of LLM output?
10. What belongs inside `VerifiedGroundedStory`, and what should stay outside?

## Exercises Without Codex

1. Add two new candidate fixtures and predict how they should cluster.
2. Write a new weak upskill angle and explain why the gate should reject it.
3. Manually rank three selected angles using the scoring formula and compare the output.
4. Create three title candidates and mark which verified claim IDs support each.
5. Design a fake hashtag research result and explain why relevance should beat reach.
6. Write one FACT, one INFERENCE, and one INTERPRETATION from the same evidence text.
