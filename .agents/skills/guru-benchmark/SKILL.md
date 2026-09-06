---
name: guru-benchmark
description: Use when invoking the repository-local Guru Benchmark from Codex or another Agent Skills client; delegates to the canonical skill without forking its behavior.
version: 0.1.0
author: Guru Benchmark contributors
license: MIT
metadata:
  hermes:
    tags: [architecture, benchmark, design-review, evidence]
    related_skills: []
---

# Guru Benchmark Repository Bridge

Load and follow `../../../skills/guru-benchmark/SKILL.md` as the complete canonical skill contract.

This file is only a discovery adapter. Do not reinterpret, summarize, duplicate, or override the canonical behavior. Resolve all relative references from the canonical skill directory. If the canonical file or its bundled contract manifest is unavailable, stop and report the missing path instead of improvising benchmark rules.
