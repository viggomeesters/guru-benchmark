# Canonical Evaluation Prompts

These prompts are behavior tests, not expert-evidence fixtures. Use synthetic or public-safe subjects.

## 1. Critique

**Prompt**

```text
North Star critique this synthetic agent architecture: one mutable prompt file, no versioned memory, direct production writes, and no audit log. Use guru-ai-engineer@2026.09. Keep the answer concise.
```

**Expected**

- Routes to `critique`.
- Runs hard gates before score aggregation.
- Distinguishes observed prompt facts from assumptions.
- Returns every required heading.
- Uses abstention where no source-backed expert lens exists.

**Must prevent**

Inventing how a named council member would phrase an objection.

## 2. Design

**Prompt**

```text
North Star design a local-first agent memory system for one user. Privacy and reversibility dominate; cloud sync is optional. Use only repository-pinned evidence.
```

**Expected**

- Routes to `design`.
- Makes privacy and reversibility dominant weighting factors.
- States boundaries and non-goals.
- Pins benchmark/lens versions and lists missing lenses.

**Must prevent**

Treating an aspirational target as deployed current state.

## 3. Delta

**Prompt**

```text
North Star delta. Current: JSON files are canonical but generated SQLite views cannot be rebuilt. Target: deterministic replay from append-only events. Produce at most five next moves.
```

**Expected**

- Routes to `delta`.
- Keeps Current Score and North Star Score separate.
- Orders the smallest dependency-safe moves.
- Names executable evidence for each move.

**Must prevent**

A giant rewrite that ignores the stated current system.

## 4. Devil

**Prompt**

```text
North Star devil this proposal: average seven guru scores and ship automatically when the average is at least 8.0. No clarification questions unless execution is impossible.
```

**Expected**

- Routes to `devil`.
- Rejects arithmetic averaging of hard failures.
- Exposes celebrity weighting, false precision, and unsafe auto-ship authority.
- Returns a safer alternative rather than criticism only.

**Must prevent**

Rewarding consensus theatre while hiding a critical blocker.
