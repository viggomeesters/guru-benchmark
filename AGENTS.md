# Agent Instructions

This repository uses a repo-local Go workflow. Repository files are the source of truth; chat memory is not.

## Startup

1. Read `.go/project.json`, `.go/vision.json`, `.go/hierarchy.json`, and the applicable task file.
2. Run `./go doctor . --platform auto --agent auto`.
3. Run `./go validate .`.
4. Inspect the next work with `./go status . --json`.
5. Claim exactly one ready task before editing:
   `./go claim <TASK-ID> --repo . --agent <agent-name>`.
6. Stay inside the task's `scope.modify` paths.

## Product rules

- Never impersonate a council member or fabricate a quotation, belief, or endorsement.
- Direct claims need dated public-source provenance.
- Inferences must be labeled and confidence-scored.
- Insufficient evidence means abstention, not invention.
- Apply hard gates before aggregate scoring.
- Keep Current Score and North Star Score distinct.
- Pin immutable benchmark and lens versions in evaluations.
- Public fixtures must be synthetic and contain no private context.

## Verification

Run `make check` before finishing. For architecture-sensitive work, record the required decision, classification, conformance, and review evidence through `./go architecture` commands.

Finish only with attributed evidence:

```bash
./go finish <TASK-ID> --repo . --agent <agent-name> \
  --evidence 'changed_files=<paths>; verification=make check; result=passed; critic=<outcome or skip reason>; runtime=<agent>'
```

Commit one completed task at a time. Do not commit generated evaluations, downloaded sources, caches, virtual environments, or secrets.
