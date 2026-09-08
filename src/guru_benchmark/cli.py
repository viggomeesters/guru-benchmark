"""Offline command-line interface for validating and rendering Guru Verdicts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

from .renderer import RendererError, render_guru_verdict


def _contract_module():
    """Load the repository's canonical cross-document validator."""
    scripts = Path(__file__).resolve().parents[2] / "scripts"
    if not scripts.is_dir():
        raise RuntimeError("the repository-local CLI requires the canonical scripts directory")
    sys.path.insert(0, str(scripts))
    try:
        import evaluation_contract  # type: ignore[import-not-found]
    finally:
        sys.path.pop(0)
    return evaluation_contract


def _load(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _inputs(args: argparse.Namespace):
    return (
        _load(args.evaluation),
        _load(args.benchmark),
        _load(args.context),
        [_load(path) for path in args.lens],
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="guru-benchmark",
        description="Validate exact local snapshots and render a Guru Verdict offline.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("validate", "validate a pinned evaluation and all supplied snapshots"),
        ("render", "validate, then render deterministic Markdown"),
    ):
        command = subparsers.add_parser(name, help=help_text)
        command.add_argument("--evaluation", type=Path, required=True)
        command.add_argument("--benchmark", type=Path, required=True)
        command.add_argument("--context", type=Path, required=True)
        command.add_argument("--lens", type=Path, action="append", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        evaluation, benchmark, context, lenses = _inputs(args)
        errors = _contract_module().validate_contract(evaluation, benchmark, context, lenses)
        if errors:
            print("Evaluation contract validation failed:", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1
        if args.command == "validate":
            print("evaluation contract: valid")
            return 0
        sys.stdout.write(render_guru_verdict(evaluation))
        return 0
    except (RendererError, RuntimeError, ValueError) as error:
        print(f"guru-benchmark: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
