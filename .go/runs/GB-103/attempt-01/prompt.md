# Attempt 1 — GB-103

Strategy: `direct_fix`

## Project contract

North star: Make world-class technical judgment reusable, source-grounded, updateable, and executable without reducing experts to role-play.

Success metrics:
- A fresh clone can validate all contracts and identify the next claimable implementation task with one documented command.
- Every Guru Verdict can identify benchmark version, source cutoff, contributing lenses, confidence, hard-gate state, and disagreement status.

Architecture principles:
- `evidence-before-persona`: Expert positions require dated source evidence or an explicit inference/abstention label.
- `weighted-consensus`: Council synthesis uses domain relevance and confidence rather than equal voting.
- `fail-closed`: Missing evidence or a failed hard gate stays visible and caps the verdict.
- `temporal-reproducibility`: Benchmark and lens snapshots are immutable and dated.

Hierarchy epics: foundation, engine, evidence, interfaces, workflow

## Task

Summary: Implement deterministic weighting and weighted median

Implement transparent weight normalization, abstention handling, and deterministic weighted-median scoring.

## Acceptance

- Weights normalize deterministically; abstentions contribute no score; ties are documented and fixture-proven.

## Verification

- `python3 -m unittest tests.test_aggregation -v && make check`
