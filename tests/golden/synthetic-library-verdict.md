# Guru Verdict

**conditional_go** — Adopt immutable pins after the synthetic replay test proves compatibility.

# Guru Score

| Measure | Value | Confidence |
| --- | --- | --- |
| Current Score | 5 | high |
| North Star Score | 8.5 | medium |
| Score dispersion | 1 | — |
| Verdict | conditional_go | medium |

## Hard gates

| Gate | Status | Effect | Evidence refs |
| --- | --- | --- | --- |
| correctness | pass | none | current.manifest-test |

## Current Score

| Dimension | Score | Evidence refs |
| --- | --- | --- |
| reproducibility | 5 | current.manifest-test |

Observed evidence:

- `current.manifest-test` (test_result, observed 2026-09-06T11:45:00Z): The synthetic replay test resolves a mutable alias in the current fixture. Source refs: None.

## North Star Score

| Dimension | Score | Evidence refs |
| --- | --- | --- |
| reproducibility | 8.5 | north-star.immutable-pin |

Conditional evidence:

- `north-star.immutable-pin`: An immutable release pin would make the synthetic replay deterministic. Condition: The compatibility suite passes against the pinned synthetic release. Basis refs: current.manifest-test.

Unmet assumptions:

- The pinned synthetic release remains compatible with every fixture.

# Ultimate Design

Resolve every synthetic dependency through an immutable local release manifest.

Explicit non-actions:

- Do not present the synthetic evidence as a personal attribution.

# Opheldering

Required: no.

None material.

# Guru Contributions

| Public role | Role | Weight | Weight rationale | Contribution | Confidence | Evidence refs | Lens claim refs |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Model Guru | primary | 1 | This is the only supplied evidence with relevant, source-backed contract expertise. | Prefer a replayable immutable input over a moving alias. | medium | north-star.immutable-pin | contract-first |
| Type Guru | abstain | 0 | No relevant source-backed evidence was supplied for this participant. | No relevant synthetic evidence was supplied. | low | None | None |
| Skill Guru | abstain | 0 | No relevant source-backed evidence was supplied for this participant. | No relevant synthetic evidence was supplied. | low | None | None |
| Simplicity Guru | abstain | 0 | No relevant source-backed evidence was supplied for this participant. | No relevant synthetic evidence was supplied. | low | None | None |
| Delivery Guru | abstain | 0 | No relevant source-backed evidence was supplied for this participant. | No relevant synthetic evidence was supplied. | low | None | None |
| Security Guru | abstain | 0 | No relevant source-backed evidence was supplied for this participant. | No relevant synthetic evidence was supplied. | low | None | None |
| Automation Guru | abstain | 0 | No relevant source-backed evidence was supplied for this participant. | No relevant synthetic evidence was supplied. | low | None | None |

# Next Moves

1. Pin the synthetic release manifest. Expected evidence: The replay test passes twice with the same resolved identifier.

# Pins & Evidence

| Artifact | Identifier | Version | As of |
| --- | --- | --- | --- |
| Benchmark | guru-synthetic-evaluation-contract | 2026.09 | 2026-09-05 |
| Context | context.synthetic-library | 2026.09.1 | 2026-09-06 |
| Source cutoff | source-cutoff | 2026.09.1 | 2026-09-06 |

Public role pins:

| Public role | Version | As of |
| --- | --- | --- |
| Model Guru | 2026.09.0 | 2026-09-06 |

- Evaluation: `evaluation.synthetic-library.2026-09-07`
- Generated at: 2026-09-07T12:00:00Z
- Schema version: 1.0.0
- Status: complete
- Synthetic: yes
