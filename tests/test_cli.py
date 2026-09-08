from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from guru_benchmark.cli import main  # noqa: E402


EVALUATION = ROOT / "tests/fixtures/evaluation/valid/synthetic-library-evaluation.json"
BENCHMARK = ROOT / "tests/fixtures/benchmark/synthetic-evaluation-contract.json"
CONTEXT = ROOT / "tests/fixtures/context/valid/synthetic-library-context.json"
LENS = ROOT / "lenses/fixtures/valid/synthetic-systems-builder.json"


def arguments(command: str, evaluation: Path = EVALUATION) -> list[str]:
    return [command, "--evaluation", str(evaluation), "--benchmark", str(BENCHMARK),
            "--context", str(CONTEXT), "--lens", str(LENS)]


def invoke(argv: list[str]) -> tuple[int, str, str]:
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        result = main(argv)
    return result, stdout.getvalue(), stderr.getvalue()


class OfflineCliTests(unittest.TestCase):
    def test_validate_accepts_exact_local_snapshot_pins_without_network(self) -> None:
        with patch.object(socket, "socket", side_effect=AssertionError("network access")):
            result, stdout, stderr = invoke(arguments("validate"))
        self.assertEqual((0, "evaluation contract: valid\n", ""), (result, stdout, stderr))

    def test_render_is_byte_deterministic_and_matches_the_golden_verdict(self) -> None:
        with patch.object(socket, "socket", side_effect=AssertionError("network access")):
            first, second = invoke(arguments("render")), invoke(arguments("render"))
        self.assertEqual((0, ""), (first[0], first[2]))
        self.assertEqual(first, second)
        expected = (ROOT / "tests/golden/synthetic-library-verdict.md").read_text(encoding="utf-8")
        self.assertEqual(expected, first[1])
        self.assertEqual(hashlib.sha256(expected.encode()).hexdigest(), hashlib.sha256(first[1].encode()).hexdigest())

    def test_mismatched_version_pin_fails_closed_without_rendering(self) -> None:
        invalid = copy.deepcopy(json.loads(EVALUATION.read_text(encoding="utf-8")))
        invalid["inputs"]["benchmark"]["version"] = "2026.10"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evaluation.json"
            path.write_text(json.dumps(invalid), encoding="utf-8")
            result, stdout, stderr = invoke(arguments("render", path))
        self.assertEqual((1, ""), (result, stdout))
        self.assertIn("benchmark pin does not exactly match", stderr)

    def test_missing_or_invalid_json_has_a_stable_nonzero_exit(self) -> None:
        result, stdout, stderr = invoke(arguments("validate", ROOT / "missing.json"))
        self.assertEqual((2, ""), (result, stdout))
        self.assertIn("guru-benchmark: cannot read", stderr)


if __name__ == "__main__":
    unittest.main()
