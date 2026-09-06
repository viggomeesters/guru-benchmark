---
name: guru-benchmark
description: Use when evaluating, redesigning, comparing, or adversarially reviewing a technical system against source-grounded expert lenses and the versioned Guru Benchmark constitution.
version: 0.1.0
author: Guru Benchmark contributors
license: MIT
user-invocable: true
triggers:
  - guru benchmark
  - north star critique
  - north star design
  - north star delta
  - north star devil
metadata:
  hermes:
    tags: [architecture, benchmark, design-review, decision-support, evidence]
    related_skills: []
---

# Guru Benchmark

## Overview

Guru Benchmark turns a concrete system, proposal, repository, or architecture into one source-grounded technical judgment. It uses a versioned benchmark constitution and dated expert lenses; it does **not** imitate people, invent quotations, or treat reputation as evidence.

The skill produces one synthesis rather than seven celebrity essays. Every expert remains visible, but relevance, source quality, confidence, context, disagreement, and abstention determine influence. Hard failures are handled before aggregate scoring and can never be averaged away.

## When to Use

Use this skill for:

- **North Star critique** — evaluate an existing system and identify the most consequential defects.
- **North Star design** — produce the strongest practical target design for a stated context.
- **North Star delta** — compare current state with the target and order the smallest useful moves.
- **North Star devil** — attack a proposed design, expose false certainty, and identify failure modes.
- architecture reviews, agent-system reviews, developer-tooling reviews, benchmarked design decisions, and evidence-backed improvement plans.

Do not use it for:

- impersonating or writing in the voice of a council member;
- predicting what a named person would privately think;
- producing endorsements, personality profiles, or entertainment role-play;
- reviewing a system without enough inspectable context when the missing facts would change the verdict;
- replacing domain-specific legal, medical, security, or financial review.

## Canonical Repository Contracts

The portable runtime bundle lives under `references/contracts/` beside this skill:

- benchmark definition: `references/contracts/2026.09.json`
- benchmark schema: `references/contracts/guru-benchmark.schema.json`
- expert-lens schema: `references/contracts/expert-lens.schema.json`
- source-reference schema: `references/contracts/source-reference.schema.json`
- integrity manifest: `references/contracts/manifest.json`

When this skill is used from a Guru Benchmark checkout, the repository source files under `benchmarks/` and `schemas/` remain canonical. `scripts/sync_skill_contracts.py` produces the portable copies, and `scripts/validate_skill.py` rejects hash drift between source and bundle. The repository also provides `docs/vision.json` and `docs/benchmark-model.md` as broader methodology context.

If the bundled contracts cannot be read or their hashes do not match the manifest, stop with a concrete missing-path or integrity error. Never silently substitute remembered benchmark rules.

## Invocation Contract

Accept natural-language requests or structured JSON matching `references/request.schema.json`.

Infer the mode only when obvious:

| User intent | Mode |
|---|---|
| assess or review what exists | `critique` |
| propose the strongest target architecture | `design` |
| compare current and target state | `delta` |
| stress-test a proposal | `devil` |

For material ambiguity that changes the benchmark, target, privacy boundary, or system scope, ask one bounded clarification. Otherwise proceed and list assumptions.

Always pin:

- `benchmark_id` and `benchmark_version`;
- benchmark `as_of` date;
- every lens version actually used;
- evaluation timestamp separately from evidence cutoff.

Read `references/invocation-contract.md` for the full input and context-normalization rules.

## Evidence Boundary

Classify every expert-linked claim as exactly one of:

1. `direct_source` — explicitly stated in a dated public primary source;
2. `built_pattern` — repeatedly demonstrated in authored work or maintained systems;
3. `labeled_inference` — a bounded interpretation with its basis stated;
4. unsupported stereotype — **forbidden** and excluded from scoring.

Rules:

- Prefer primary authored sources and official repositories over commentary.
- Cite source identifiers or URLs close to the supported claim.
- Keep any source excerpt short; paraphrase by default.
- Never invent a source, quotation, date, confidence level, or expert position.
- Never turn silence into agreement.
- Missing, stale, contradictory, or irrelevant evidence lowers confidence or causes abstention.
- Do not expose hidden chain-of-thought. Return concise decision rationale and inspectable evidence references.
- Do not copy private context, credentials, proprietary corpora, or generated runtime state into public benchmark artifacts.

When current evidence is requested, use available research tools and clearly separate newly retrieved evidence from repository-pinned evidence. Do not mutate benchmark or lens versions during an evaluation.

## Council Participation

Consider every member listed in the pinned benchmark, then assign one role per relevant dimension:

- `primary` — strong domain relevance and adequate evidence;
- `supporting` — relevant corroboration with lower decision weight;
- `counterweight` — relevant objection or competing trade-off;
- `abstain` — insufficient relevance or evidence.

Weights are contextual, never celebrity popularity and never a permanent global percentage. Explain only weights that materially affect the verdict. An abstention is valid output, not a failure to fill space.

Do not calculate a simple arithmetic mean. Follow the benchmark's aggregation method and preserve score dispersion. Apply hard gates before synthesis; a failed hard gate must produce `hold`, `conditional_go`, or the configured score cap.

## Evaluation Workflow

1. **Resolve the request.** Capture mode, subject, product stage, dominant risk, constraints, decision horizon, audience, and desired depth.
2. **Load exact contracts.** Validate the benchmark definition and any lens files before using them.
3. **Inventory evidence.** Separate observed system facts, user claims, repository evidence, public sources, assumptions, and unknowns.
4. **Run hard gates.** Check correctness, safety/privacy, provenance, reversibility, and any benchmark-specific gates before scoring.
5. **Select participation.** Give every council member a role or explicit abstention for each material dimension.
6. **Score current state.** Record the observed score and confidence without rewarding imagined future work.
7. **Design the North Star.** Describe the smallest coherent target design that resolves the dominant constraints.
8. **Score the target separately.** Do not collapse Current Score and North Star Score.
9. **Map disagreement.** Surface only differences that change the decision; distinguish principled conflict from missing evidence.
10. **Synthesize.** Produce one verdict, ordered design, and executable next moves.
11. **Self-audit.** Reject unsupported guru claims, fake precision, hidden assumptions, and recommendations that violate hard gates.

## Required Output

Return the following headings in this order:

1. **Guru Verdict** — one compact decision: `go`, `conditional_go`, `hold`, or `reject`, plus why.
2. **Guru Score** — Current Score, North Star Score, confidence, score dispersion, and hard-gate status.
3. **Ultimate Design** — the target architecture or decision, including boundaries and explicit non-goals.
4. **Opheldering** — only decision-relevant disagreement, uncertainty, assumptions, and abstentions. Write `None material` when there is none.
5. **Guru Contributions** — compact table of council member, role, contribution, confidence, and evidence refs; never first-person imitation.
6. **Next Moves** — ordered, individually testable actions with expected evidence.
7. **Pins & Evidence** — benchmark/lens versions, cutoff date, source references, and unresolved evidence gaps.

Structured consumers may request JSON matching `references/response.schema.json`. Human-readable output must remain equivalent to that schema.

## Failure and Abstention Rules

Return `hold` rather than bluff when:

- the evaluated artifact is inaccessible;
- a critical security, privacy, correctness, or provenance question is unanswered;
- the available benchmark/lens version does not cover the requested domain;
- current facts are required but cannot be verified;
- evidence conflicts strongly enough that synthesis would create fake certainty.

Name the smallest missing input or verification that would unblock the decision.

## Common Pitfalls

1. **Seven mini-essays.** Wrong: one section per famous person. Right: one synthesis plus a compact contribution table.
2. **Permanent weights.** Weight by current context, stage, risk, relevance, and evidence quality.
3. **Averaging a blocker.** Hard-gate failures happen before aggregate scoring.
4. **Confusing target with reality.** Current Score measures observed state; North Star Score measures the proposed target.
5. **Inference laundering.** Label inference and state its source-backed basis.
6. **Forced participation.** Use `abstain` when a member is irrelevant or weakly evidenced.
7. **Prompt-as-truth.** User-provided descriptions are claims until inspected or explicitly accepted as assumptions.
8. **Unbounded redesign.** Prefer the smallest coherent design that materially improves the decision.

## Evaluation Prompts

Before changing this skill, run the four canonical trigger cases in `references/eval-prompts.md`. Each case defines expected routing, guardrails, output shape, and the failure it must prevent.

## Verification Checklist

- [ ] Exact benchmark and lens versions are pinned.
- [ ] Every expert-linked claim has a valid evidence class and source reference.
- [ ] Every council member has a role or explicit abstention.
- [ ] Hard gates run before scoring.
- [ ] Current Score and North Star Score remain separate.
- [ ] Material disagreement and uncertainty remain visible.
- [ ] Output follows the required heading or JSON contract.
- [ ] No persona imitation, fabricated quotation, hidden chain-of-thought, private data, or unsupported endorsement appears.
- [ ] Next Moves are ordered and testable.
