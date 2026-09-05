# Benchmark Model

## Council participation

The founding council is fixed for the initial benchmark generation. Every member is represented in an evaluation as one of:

- `primary` — direct domain relevance and strong evidence;
- `supporting` — relevant principles with moderate influence;
- `counterweight` — a useful competing philosophy;
- `abstain` — insufficient evidence or relevance for a responsible claim.

Abstention is a valid result. It prevents made-up specificity while preserving transparency about who was considered.

## Evidence classes

| Class | Meaning | Allowed use |
|---|---|---|
| `direct` | Explicit dated statement in a stable public source | Claim with attribution |
| `built-pattern` | Repeated, inspectable choices in public work | Pattern claim with examples |
| `inference` | Reasonable synthesis from direct evidence or built patterns | Must be labeled and confidence-scored |
| `unsupported` | Reputation, stereotype, or unverifiable attribution | Rejected |

Direct quotations require exact source support and must remain brief. The project stores references and metadata, not a shadow source archive.

## Weighting

Each participating lens receives a normalized influence based on:

1. domain relevance;
2. evidence confidence;
3. evidence recency;
4. fit with the supplied context;
5. value as a counterweight.

The aggregate score uses a weighted median to resist false precision and outliers. The output still records all contributions and dispersion.

## Hard gates

Hard gates are evaluated before dimensions. A gate can produce `hold`, `conditional_go`, or a score cap. A strong interface or elegant abstraction cannot cancel a correctness, security, privacy, evidence, or recovery failure.

## Disagreement

Clarification is required when either:

- score dispersion exceeds the versioned threshold;
- two sufficiently weighted lenses recommend incompatible actions;
- the disputed trade-off can change the verdict or first next move.

Otherwise the default output remains one synthesis.

## Score honesty

- **Current Score:** accepts only evidence about behavior that exists and was observed.
- **North Star Score:** rates the proposed design conditionally and must state unmet assumptions.

The gap between them becomes the improvement queue. Intended architecture is never counted as shipped implementation.

## Output contract

Every complete evaluation exposes:

1. Guru Verdict
2. Guru Score and confidence
3. hard-gate results
4. Current Score
5. North Star Score
6. Ultimate Design
7. Clarification
8. compact guru contributions
9. ordered next moves and explicit non-actions
10. exact benchmark, lens, context, and source-cutoff references
