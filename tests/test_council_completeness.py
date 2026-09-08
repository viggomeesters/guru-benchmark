import hashlib
import json
import socket
import unittest
from contextlib import redirect_stdout
from datetime import date
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from guru_benchmark.cli import main


ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "cases/founding-council"
BENCHMARK = ROOT / "benchmarks/guru-ai-engineer/2026.09.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class FoundingCouncilCompletenessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.benchmark = load(BENCHMARK)
        cls.evaluation = load(CASE / "evaluation.json")
        cls.audit = load(CASE / "gap-audit.json")
        cls.lenses = {
            item["expert"]["id"]: item
            for item in (load(path) for path in ROOT.glob("lenses/*/20*.json"))
        }

    def test_all_seven_resolve_one_to_one_without_gaps(self):
        gaps = {name: [] for name in self.audit["gaps"]}
        pins = {pin["lens_id"]: pin for pin in self.evaluation["inputs"]["lenses"]}
        outputs = [item["lens_id"] for item in self.evaluation["guru_contributions"]]
        for expert_id in self.benchmark["council"]:
            lens = self.lenses.get(expert_id)
            lens_id = f"expert.{expert_id}"
            if lens is None or lens["status"] != "active" or lens["expert"]["synthetic"]:
                gaps["lens"].append(expert_id)
                continue
            review_path = ROOT / f"sources/{expert_id}/{lens['version']}-review.json"
            if not lens["source_references"] or not review_path.exists():
                gaps["source"].append(expert_id)
            else:
                review = load(review_path)
                if review["lens_id"] != lens_id or set(review["checks"].values()) != {"passed"}:
                    gaps["source"].append(expert_id)
                if review["checks"]["copyright_boundary_review"] != "passed" or any(
                    "metadata" not in (source.get("notes") or "").lower()
                    for source in lens["source_references"]
                ):
                    gaps["copyright"].append(expert_id)
            if lens["confidence"] not in {"low", "medium", "high"}:
                gaps["confidence"].append(expert_id)
            if date.fromisoformat(lens["valid_until"]) < date.fromisoformat("2026-09-08"):
                gaps["validity"].append(expert_id)
            if pins.get(lens_id) != {"lens_id": lens_id, "version": lens["version"], "as_of": lens["as_of"]}:
                gaps["version_pin"].append(expert_id)
            if outputs.count(lens_id) != 1:
                gaps["output"].append(expert_id)
        self.assertEqual({name: [] for name in gaps}, gaps)
        self.assertEqual(0, self.audit["gap_count"])
        self.assertEqual(gaps, self.audit["gaps"])

    def test_offline_render_is_deterministic_and_matches_committed_output(self):
        lens_args = []
        for expert_id in self.benchmark["council"]:
            lens_args.extend(["--lens", str(ROOT / f"lenses/{expert_id}/2026.09.0.json")])
        args = ["render", "--evaluation", str(CASE / "evaluation.json"), "--benchmark", str(BENCHMARK), "--context", str(CASE / "context.json"), *lens_args]
        renders = []
        with patch.object(socket, "socket", side_effect=AssertionError("network disabled")):
            for _ in range(2):
                stream = StringIO()
                with redirect_stdout(stream):
                    self.assertEqual(0, main(args))
                renders.append(stream.getvalue())
        self.assertEqual(renders[0], renders[1])
        self.assertEqual((CASE / "verdict.md").read_text(encoding="utf-8"), renders[0])
        for contribution in self.evaluation["guru_contributions"]:
            self.assertEqual(
                1,
                renders[0].count(f"| {contribution['lens_id']} | {contribution['role']} |"),
            )
        self.assertEqual(64, len(hashlib.sha256(renders[0].encode()).hexdigest()))

    def test_self_benchmark_comparison_is_public_falsifiable_and_actionable(self):
        comparison = load(CASE / "comparison.json")
        self.assertEqual({"classification": "public", "private_data_included": False}, comparison["privacy"])
        values = comparison["guru_benchmark_review"]["distinct_falsifiable_value"]
        self.assertGreaterEqual(len(values), 3)
        self.assertTrue(all(item["claim"] and item["falsifier"] for item in values))
        repair_ids = {item["task_id"] for item in comparison["repair_tasks"]}
        self.assertEqual({"GB-106", "GB-119"}, repair_ids)
        self.assertTrue(comparison["normal_technical_review"]["limitations"])
        self.assertTrue(comparison["guru_benchmark_review"]["limitations"])


if __name__ == "__main__":
    unittest.main()
