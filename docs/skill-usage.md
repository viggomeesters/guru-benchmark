# Use Guru Benchmark as an Agent Skill

Guru Benchmark ships one canonical behavior contract at [`skills/guru-benchmark/SKILL.md`](../skills/guru-benchmark/SKILL.md). Runtime adapters discover or install that same bundle; they do not maintain separate Hermes and Codex prompts.

## Invocation modes

```text
Guru Benchmark <request>
North Star critique <subject>
North Star design <subject>
North Star delta <subject>
North Star devil <subject>
```

Hermes can preload the installed skill by name. Codex can invoke a discovered skill explicitly as `$guru-benchmark` or select it implicitly from the request description.

## Hermes

### Safe local installation

From a clone of this repository:

```bash
./scripts/install-skill.sh --target hermes --dry-run
./scripts/install-skill.sh --target hermes
```

The default destination is `${HERMES_HOME:-$HOME/.hermes}/skills/guru-benchmark`. The installer copies the complete portable bundle, refuses to overwrite an existing install, and creates a timestamped backup when `--force` is explicitly used.

Start a new session or run `/reload-skills`, then invoke it explicitly:

```bash
hermes --skills guru-benchmark chat -q \
  'North Star devil this synthetic proposal: deploy when seven scores average 8.0.'
```

Inside an interactive or gateway session:

```text
/skill guru-benchmark
North Star critique <subject>
```

### Repository tap

Hermes also supports GitHub repositories as skill sources:

```bash
hermes skills tap add viggomeesters/guru-benchmark
hermes skills search 'guru benchmark'
```

Use the identifier returned by the search command for native installation. The repository keeps the install helper as the deterministic fallback because a direct URL to only `SKILL.md` would omit the bundled references and contracts.

## Codex

### Repository-local discovery

Open Codex from the repository root. Codex scans `.agents/skills` from the working directory through the repository root, so the committed bridge at `.agents/skills/guru-benchmark/SKILL.md` is discovered without a global install.

```text
$guru-benchmark North Star delta <current state and target>
```

The bridge delegates to `skills/guru-benchmark/SKILL.md`; it contains no independent methodology.

### User-level installation

```bash
./scripts/install-skill.sh --target codex --dry-run
./scripts/install-skill.sh --target codex
```

The default destination is `${AGENTS_HOME:-$HOME/.agents}/skills/guru-benchmark`, the current user-level Agent Skills location used by Codex. Restart Codex after installation so it rescans skills.

## Other Agent Skills clients

Clients implementing the Agent Skills `SKILL.md` convention can install or reference the complete `skills/guru-benchmark/` directory. Clients without automatic discovery can be instructed to read `skills/guru-benchmark/SKILL.md` directly and preserve its relative references.

## Integrity and updates

The installed bundle contains a hash manifest for its benchmark and schema snapshots. Repository maintainers update it with:

```bash
python3 scripts/sync_skill_contracts.py
python3 scripts/validate_skill.py
```

After pulling a newer repository version, rerun the installer with `--force` only when replacing an existing install is intended. The old installation is retained as a timestamped backup.

## Smoke checks

```bash
python3 scripts/validate_skill.py
python3 -m unittest tests.test_skill_install -v
make check
```

Runtime dogfood evidence and known limitations are recorded in the final section of this document once `GB-112` has executed.
