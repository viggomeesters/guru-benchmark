# Architecture

## System intent

Guru Benchmark is designed as a small, inspectable pipeline whose artifacts are durable JSON contracts rather than hidden prompt behavior.

```text
Decision context
      │
      ▼
Context classifier ──────── benchmark profile
      │                           │
      ▼                           ▼
Lens resolver ───────────── immutable expert lens snapshots
      │
      ▼
Hard-gate evaluator
      │
      ▼
Weighted synthesis ──────── abstentions + disagreement analysis
      │
      ▼
Guru Verdict contract
```

## Canonical artifacts

| Artifact | Responsibility |
|---|---|
| `benchmarks/<id>/<version>.json` | Dimensions, hard gates, council, aggregation, output contract |
| `lenses/<expert>/<version>.json` | Dated claims, evidence refs, confidence, domains, objections, abstention boundaries |
| `contexts/<id>/<version>.json` | User, scale, lifecycle, risk, and operating constraints |
| `evaluations/<id>.json` | Generated output that pins all exact inputs; ignored by default until publication is intentional |
| `schemas/*.schema.json` | Machine-enforced contracts |
| `.go/**` | Canonical execution, task, decision, architecture, and evidence state |

Only benchmark definitions and reviewed lens metadata are canonical product inputs. Downloaded pages and copied source content are not repository data.

## Trust boundaries

1. **Public-source boundary:** external material is untrusted input. Store stable references and bounded metadata, not copied corpora.
2. **Inference boundary:** direct evidence, repeated build pattern, labeled inference, and abstention are different evidence classes.
3. **Private-context boundary:** personal or proprietary context can influence a local run but must not enter public fixtures or Git history.
4. **Generated-output boundary:** evaluation results are derived, potentially sensitive runtime artifacts and remain ignored by default.
5. **Endorsement boundary:** synthesized results are independent analysis, never attributed approval.

## Aggregation

The default score method is a weighted median. Lens influence is based on domain relevance, source confidence, recency, context fit, and counterweight value. A lens can abstain without disappearing from the council record.

Hard gates run before aggregate scores. A failed correctness, security, privacy, recoverability, or evidence gate can block or cap the verdict regardless of the numerical result.

Material divergence produces a `clarification` section. Low-impact differences remain available in provenance but do not force seven separate narratives into the default output.

## Versioning

Benchmark and lens snapshots are immutable. New evidence creates a new dated version. Historical evaluations pin exact versions and source cutoffs; a moving `latest` alias must never rewrite a past verdict.

## Initial implementation boundary

Repository foundation ships contracts, schemas, validation, workflow, and public documentation. The evaluator, lens corpus, CLI, and agent adapters remain ordered backlog work. This avoids presenting intended behavior as implemented behavior.
