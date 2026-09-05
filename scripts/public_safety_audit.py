#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRACKED = subprocess.check_output(["git", "-C", str(ROOT), "ls-files"], text=True).splitlines()

forbidden_paths = re.compile(r"(^|/)(\.env($|\.)|id_rsa|id_ed25519|.*\.(pem|key|p12|pfx|sqlite|sqlite3|db)|node_modules|\.venv|dist|build|coverage|cache)(/|$)", re.I)
secret_patterns = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\s*[:=]\s*['\"][^'\"]{8,}['\"]", re.I),
]
allow_suffixes = {".md", ".json", ".jsonl", ".py", ".sh", ".yml", ".yaml", ".txt", ".svg", ""}
errors = []
for relative in TRACKED:
    if forbidden_paths.search(relative):
        errors.append(f"forbidden tracked path: {relative}")
        continue
    path = ROOT / relative
    if not path.is_file() or path.suffix.lower() not in allow_suffixes:
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    for pattern in secret_patterns:
        if pattern.search(text):
            errors.append(f"secret-like content in: {relative}")
            break

if errors:
    raise SystemExit("Public safety audit failed:\n" + "\n".join(f"- {e}" for e in errors))
print(f"public safety: valid ({len(TRACKED)} tracked paths)")
