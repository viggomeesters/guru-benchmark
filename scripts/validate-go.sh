#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$ROOT/go" validate "$ROOT"
"$ROOT/go" architecture validate "$ROOT"
"$ROOT/go" status "$ROOT" --json >/dev/null
printf 'workflow: valid\n'
