#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/install-skill.sh --target hermes|codex [--destination-root PATH] [--dry-run] [--force]

Installs the complete Guru Benchmark skill bundle. Existing installs are never
replaced unless --force is supplied; forced replacements are backed up beside
the destination.
EOF
}

target=""
destination_root=""
dry_run=false
force=false
while (($#)); do
  case "$1" in
    --target) target="${2:-}"; shift 2 ;;
    --destination-root) destination_root="${2:-}"; shift 2 ;;
    --dry-run) dry_run=true; shift ;;
    --force) force=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "error: unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

case "$target" in
  hermes)
    if [[ -z "$destination_root" ]]; then
      destination_root="${HERMES_HOME:-$HOME/.hermes}/skills"
    fi
    ;;
  codex)
    if [[ -z "$destination_root" ]]; then
      destination_root="${AGENTS_HOME:-$HOME/.agents}/skills"
    fi
    ;;
  *) echo "error: --target must be hermes or codex" >&2; exit 2 ;;
esac

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_dir="$repo_root/skills/guru-benchmark"
destination="$destination_root/guru-benchmark"

[[ -f "$source_dir/SKILL.md" ]] || { echo "error: canonical skill missing: $source_dir/SKILL.md" >&2; exit 1; }
[[ -f "$source_dir/references/contracts/manifest.json" ]] || { echo "error: contract bundle missing" >&2; exit 1; }

if [[ -e "$destination" && "$force" != true ]]; then
  echo "error: destination exists; use --force to replace safely: $destination" >&2
  exit 3
fi

if [[ "$dry_run" == true ]]; then
  printf 'target=%s\nsource=%s\ndestination=%s\naction=%s\n' \
    "$target" "$source_dir" "$destination" "$([[ -e "$destination" ]] && echo backup-and-replace || echo install)"
  exit 0
fi

mkdir -p "$destination_root"
staging="$(mktemp -d "$destination_root/.guru-benchmark.install.XXXXXX")"
cleanup() { [[ -d "$staging" ]] && rm -rf "$staging"; }
trap cleanup EXIT
cp -a "$source_dir/." "$staging/"

backup=""
if [[ -e "$destination" ]]; then
  backup="$destination.backup.$(date -u +%Y%m%dT%H%M%SZ)"
  mv "$destination" "$backup"
fi
if ! mv "$staging" "$destination"; then
  [[ -n "$backup" && -e "$backup" && ! -e "$destination" ]] && mv "$backup" "$destination"
  exit 1
fi
trap - EXIT

printf 'installed=%s\ntarget=%s\n' "$destination" "$target"
if [[ -n "$backup" ]]; then
  printf 'backup=%s\n' "$backup"
fi
