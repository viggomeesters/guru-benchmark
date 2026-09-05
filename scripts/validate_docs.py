#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
required = [
    "README.md", "LICENSE", "SECURITY.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md",
    "CHANGELOG.md", "AGENTS.md", "CITATION.cff", "docs/product-vision.md",
    "docs/vision.json", "docs/architecture.md", "docs/getting-started.md",
    "docs/benchmark-model.md", "docs/governance.md", "docs/implementation-plan.md",
]
errors = [f"missing required document: {item}" for item in required if not (ROOT / item).is_file()]

placeholder = re.compile(r"\b(?:TBD|TBC|FIXME|XXX|YOUR[_ -]?NAME|PROJECT[_ -]?NAME|LOREM IPSUM)\b|\{NTB\}", re.I)
for relative in required:
    path = ROOT / relative
    if path.is_file():
        match = placeholder.search(path.read_text(encoding="utf-8"))
        if match:
            errors.append(f"placeholder token {match.group(0)!r} in {relative}")

readme = (ROOT / "README.md").read_text(encoding="utf-8") if (ROOT / "README.md").is_file() else ""
for target in ["assets/social-preview.png", "docs/product-vision.md", "docs/vision.json", "docs/implementation-plan.md", "CONTRIBUTING.md", "SECURITY.md", "LICENSE"]:
    if target not in readme:
        errors.append(f"README does not link {target}")

if errors:
    raise SystemExit("Documentation validation failed:\n" + "\n".join(f"- {e}" for e in errors))
print(f"docs: valid ({len(required)} required artifacts)")
