# Attempt 1 — GB-105

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

Summary: Implement disagreement and clarification engine

Detect material score dispersion and incompatible recommendations without producing noisy explanations.

## Acceptance

- Material divergence deterministically triggers clarification; harmless variation does not.

## Verification

- `python3 -m unittest tests.test_disagreement -v && make check`
