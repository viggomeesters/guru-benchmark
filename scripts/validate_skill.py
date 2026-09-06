#!/usr/bin/env python3
from __future__ import annotations

import json
import hashlib
import re
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills/guru-benchmark"
SKILL = SKILL_DIR / "SKILL.md"


def fail(message: str) -> None:
    raise SystemExit(f"skill contract: invalid: {message}")


def load_json(relative: str):
    return json.loads((SKILL_DIR / relative).read_text(encoding="utf-8"))


text = SKILL.read_text(encoding="utf-8")
if not text.startswith("---\n"):
    fail("frontmatter must start at byte zero")
match = re.match(r"^---\n(.*?)\n---\n(.+)$", text, re.DOTALL)
if not match:
    fail("frontmatter or body is malformed")
frontmatter, body = match.groups()

required_frontmatter = {
    "name": "guru-benchmark",
    "version": "0.1.0",
    "author": "Guru Benchmark contributors",
    "license": "MIT",
    "user-invocable": "true",
}
for key, value in required_frontmatter.items():
    if not re.search(rf"(?m)^{re.escape(key)}:\s*{re.escape(value)}\s*$", frontmatter):
        fail(f"missing or incorrect frontmatter: {key}")
description = re.search(r"(?m)^description:\s*(.+)$", frontmatter)
if not description or not description.group(1).startswith("Use when "):
    fail("description must start with 'Use when '")
if len(description.group(1)) > 1024:
    fail("description exceeds 1024 characters")
if len(text) > 100_000:
    fail("SKILL.md exceeds 100000 characters")

required_snippets = [
    "North Star critique",
    "North Star design",
    "North Star delta",
    "North Star devil",
    "direct_source",
    "built_pattern",
    "labeled_inference",
    "unsupported stereotype",
    "Current Score",
    "North Star Score",
    "Guru Verdict",
    "Ultimate Design",
    "Opheldering",
    "Guru Contributions",
    "Next Moves",
    "abstain",
    "Do not expose hidden chain-of-thought",
]
for snippet in required_snippets:
    if snippet not in body:
        fail(f"required behavior snippet missing: {snippet}")

for forbidden in ["TODO", "TBD", "PLACEHOLDER", "act as Karpathy", "pretend to be"]:
    if forbidden.lower() in text.lower():
        fail(f"forbidden unfinished or persona phrase: {forbidden}")

for relative in [
    "references/invocation-contract.md",
    "references/eval-prompts.md",
    "references/request.schema.json",
    "references/response.schema.json",
    "examples/request.json",
    "examples/response.json",
    "references/contracts/manifest.json",
]:
    if not (SKILL_DIR / relative).is_file():
        fail(f"missing linked artifact: {relative}")

manifest = load_json("references/contracts/manifest.json")
if manifest.get("schema") != "guru-benchmark.portable-contract-bundle.v1":
    fail("portable contract manifest has the wrong schema")
for artifact in manifest.get("artifacts", []):
    source = ROOT / artifact["source"]
    bundled = SKILL_DIR / artifact["bundled"]
    if not source.is_file() or not bundled.is_file():
        fail(f"portable contract artifact is missing: {artifact}")
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    bundled_hash = hashlib.sha256(bundled.read_bytes()).hexdigest()
    if source_hash != artifact["sha256"] or bundled_hash != artifact["sha256"]:
        fail(f"portable contract drift: {artifact['source']}")

prompts = (SKILL_DIR / "references/eval-prompts.md").read_text(encoding="utf-8")
if len(re.findall(r"(?m)^## [1-4]\. ", prompts)) != 4:
    fail("eval-prompts.md must define exactly four numbered canonical cases")
for marker in ["**Prompt**", "**Expected**", "**Must prevent**"]:
    if prompts.count(marker) != 4:
        fail(f"each eval case must contain {marker}")

for schema_name in ["references/request.schema.json", "references/response.schema.json"]:
    Draft202012Validator.check_schema(load_json(schema_name))

format_checker = FormatChecker()
request_validator = Draft202012Validator(load_json("references/request.schema.json"), format_checker=format_checker)
response_validator = Draft202012Validator(load_json("references/response.schema.json"), format_checker=format_checker)
request_errors = list(request_validator.iter_errors(load_json("examples/request.json")))
response_errors = list(response_validator.iter_errors(load_json("examples/response.json")))
if request_errors:
    fail(f"example request does not validate: {request_errors[0].message}")
if response_errors:
    fail(f"example response does not validate: {response_errors[0].message}")

print("skill contract: valid")
