# Attempt 1 — GB-104

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

Summary: Implement hard-gate and score-cap semantics

Apply hold, conditional-go, and score-cap effects before aggregate scoring.

## Acceptance

- Gate effects run before aggregation and cannot be erased by high dimension scores.

## Verification

- `python3 -m unittest tests.test_hard_gates -v && make check`
