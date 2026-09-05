# Contributing

Contributions are welcome when they improve evidence quality, reproducibility, public safety, or the usefulness of the synthesized verdict.

## Before editing

1. Read `AGENTS.md` and `docs/getting-started.md`.
2. Run `make check` on a clean clone.
3. Inspect `./go status . --json`.
4. Claim one ready task before changing files.

If no task covers the proposed change, open an issue describing the decision context, expected outcome, public evidence boundary, and acceptance test before adding implementation.

## Development rules

- Keep changes inside the claimed task scope.
- Prefer small, dependency-ordered commits.
- Add or update tests for behavior and contract changes.
- Use synthetic fixtures only.
- Do not commit downloaded pages, transcripts, private context, evaluation outputs, credentials, caches, or virtual environments.
- Never invent a council member's opinion, quotation, or endorsement.
- Distinguish direct evidence, public built patterns, labeled inference, and abstention.
- Create a new immutable version when scoring semantics or lens evidence changes.

## Validate

```bash
make check
```

A pull request must explain:

- what decision or user outcome improves;
- which contracts or versions change;
- how the result was verified;
- whether public attribution, security, privacy, or historical reproducibility are affected.

## Commit style

Use concise imperative Conventional Commit subjects, for example:

```text
feat: add deterministic weighted median
fix: reject unsupported lens claims
docs: clarify historical snapshot policy
```

## Review expectations

Material benchmark, attribution, privacy, schema, or architecture changes require explicit human review. Maintainers may reject technically valid changes that introduce false precision, celebrity fanfiction, source-copying, or complexity without proven user leverage.
