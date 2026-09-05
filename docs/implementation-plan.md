# Implementation Plan

Repository foundation is complete when all `GB-F00x` tasks are done. Product implementation remains deliberately unbuilt and is decomposed below into dependency-ordered, individually claimable Go tasks.

## Delivery sequence

### GB-101 — Define expert lens and evidence schemas

**Depends on:** foundation

**Scope:** `schemas/`, `lenses/fixtures/`, `tests/`

**Acceptance:** Direct evidence, built patterns, labeled inference, confidence, validity, source references, objections, and abstention boundaries validate; unsupported claims fail.

**Verification:** `python3 -m unittest tests.test_lens_contract -v && make check`

### GB-102 — Define context and evaluation schemas

**Depends on:** GB-101

**Scope:** `schemas/`, `contexts/fixtures/`, `evaluations/fixtures/`, `tests/`

**Acceptance:** Evaluations pin exact benchmark, lens, context, and source-cutoff versions; Current and North Star evidence are structurally distinct.

**Verification:** `python3 -m unittest tests.test_evaluation_contract -v && make check`

### GB-103 — Implement deterministic weighting and weighted median

**Depends on:** GB-102

**Scope:** `src/guru_benchmark/`, `tests/fixtures/`, `tests/`

**Acceptance:** Weights normalize deterministically; abstentions contribute no fabricated score; tie behavior is documented and fixture-proven.

**Verification:** `python3 -m unittest tests.test_aggregation -v && make check`

### GB-104 — Implement hard-gate and score-cap semantics

**Depends on:** GB-103

**Scope:** `src/guru_benchmark/`, `tests/fixtures/`, `tests/`

**Acceptance:** Gate effects run before aggregation and cannot be erased by high dimension scores.

**Verification:** `python3 -m unittest tests.test_hard_gates -v && make check`

### GB-105 — Implement disagreement and clarification engine

**Depends on:** GB-103

**Scope:** `src/guru_benchmark/`, `tests/fixtures/`, `tests/`

**Acceptance:** Dispersion and incompatible actions deterministically trigger clarification; harmless variation does not create noisy output.

**Verification:** `python3 -m unittest tests.test_disagreement -v && make check`

### GB-106 — Build Guru Verdict renderer

**Depends on:** GB-104, GB-105

**Scope:** `src/guru_benchmark/`, `tests/golden/`, `tests/`

**Acceptance:** A synthetic evaluation renders every required output section with exact provenance and no persona-style claims.

**Verification:** `python3 -m unittest tests.test_renderer -v && make check`

### GB-107 — Research and publish one source-grounded pilot lens

**Depends on:** GB-101

**Scope:** `lenses/`, `sources/`, `tests/`

**Acceptance:** One council lens passes source review, confidence review, copyright boundary checks, and validity-window checks.

**Verification:** `python3 scripts/validate_contracts.py && make check`

### GB-108 — Add the Guru Benchmark CLI

**Depends on:** GB-106, GB-107

**Scope:** `src/`, `tests/`, `docs/`

**Acceptance:** A user can validate inputs and generate a deterministic verdict from version-pinned local JSON without network access.

**Verification:** `python3 -m unittest tests.test_cli -v && make check`

### GB-109 — Run one real-case pilot and compare against a normal review

**Depends on:** GB-108

**Scope:** `cases/`, `docs/`, `tests/`

**Acceptance:** A public-safe case measures whether the benchmark adds distinct, falsifiable value; weaknesses become ordered repair tasks.

**Verification:** `make check`

## Deliberately deferred

Hosted APIs, autonomous source ingestion, a web UI, a large council, private-context persistence, and integrations remain out of scope until the local pilot proves useful.
