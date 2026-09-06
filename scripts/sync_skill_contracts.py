#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "skills/guru-benchmark/references/contracts"
SOURCES = [
    "benchmarks/guru-ai-engineer/2026.09.json",
    "schemas/guru-benchmark.schema.json",
    "schemas/expert-lens.schema.json",
    "schemas/source-reference.schema.json",
]

TARGET.mkdir(parents=True, exist_ok=True)
artifacts = []
for relative in SOURCES:
    source = ROOT / relative
    destination = TARGET / source.name
    shutil.copyfile(source, destination)
    payload = destination.read_bytes()
    artifacts.append(
        {
            "source": relative,
            "bundled": f"references/contracts/{destination.name}",
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    )
manifest = {
    "schema": "guru-benchmark.portable-contract-bundle.v1",
    "generated_from": "repository canonical contracts",
    "artifacts": artifacts,
}
(TARGET / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(f"skill contracts: synced ({len(artifacts)} artifacts)")
