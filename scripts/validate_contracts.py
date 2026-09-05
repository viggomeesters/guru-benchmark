#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]


def load(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def validate(instance_path: str, schema_path: str) -> None:
    instance = load(instance_path)
    schema = load(schema_path)
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(instance),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        formatted = "\n".join(f"- {instance_path}:{'/'.join(map(str, e.absolute_path))}: {e.message}" for e in errors)
        raise SystemExit(f"Contract validation failed:\n{formatted}")


validate("docs/vision.json", "schemas/repo-vision-contract.schema.json")
validate("benchmarks/guru-ai-engineer/2026.09.json", "schemas/guru-benchmark.schema.json")

benchmark = load("benchmarks/guru-ai-engineer/2026.09.json")
weight = sum(item["weight"] for item in benchmark["dimensions"])
if abs(weight - 1.0) > 1e-9:
    raise SystemExit(f"Dimension weights must total 1.0, got {weight}")
if len(set(benchmark["council"])) != 7:
    raise SystemExit("Founding council must contain exactly seven unique members")
print("contracts: valid")
