# Getting Started

## Prerequisites

- Git
- Bash
- Make
- Python 3.11 or newer
- Network access for the first repo-local Go runtime bootstrap
- The Python `jsonschema` package

No Node.js toolchain, service account, API key, or hosted runtime is required for foundation validation.

## Fresh clone

```bash
git clone https://github.com/viggomeesters/guru-benchmark.git
cd guru-benchmark
./go doctor . --platform auto --agent auto
make check
```

The `go` launcher reads the exact runtime pin from `.go/project.json` and bootstraps the matching workflow runtime outside the repository.

## Repository map

```text
.go/                 Canonical workflow, goals, tasks, decisions, evidence
assets/              README hero and social-preview source
benchmarks/          Immutable benchmark definitions
schemas/             JSON Schema contracts
docs/                Vision, architecture, governance, and plan
scripts/             Deterministic local validation
src/                 Reserved for task-driven product implementation
tests/               Contract and later behavioral tests
```

## Understand the product

Read in this order:

1. `README.md`
2. `docs/product-vision.md`
3. `docs/vision.json`
4. `docs/architecture.md`
5. `docs/benchmark-model.md`
6. `docs/implementation-plan.md`

## Pick up work

```bash
./go status . --json
./go validate .
./go claim <TASK-ID> --repo . --agent <agent-name>
```

Read the claimed task in `.go/tasks/active/` and do not modify paths outside its scope. Finish with `make check`, task-specific verification, and attributed finish evidence.

## Common commands

```bash
make check                 # complete local quality gate
make contracts             # schemas and contract tests
make workflow              # repo-local Go and architecture validation
make docs                  # public documentation checks
make privacy               # tracked-file public-safety audit
./go status . --json       # workflow and next-task readback
```

## Adding product behavior

Do not add an evaluator, lens, or adapter opportunistically. Claim the matching Go task, write the failing behavioral test first where practical, preserve immutable version boundaries, and use only synthetic fixtures.
