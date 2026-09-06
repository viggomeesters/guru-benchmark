import json
import subprocess
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/guru-benchmark"


class GuruBenchmarkSkillContractTests(unittest.TestCase):
    def test_skill_validator_passes(self):
        completed = subprocess.run(
            ["python3", "scripts/validate_skill.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        self.assertIn("skill contract: valid", completed.stdout)

    def test_request_and_response_examples_validate(self):
        for stem in ["request", "response"]:
            schema = json.loads((SKILL / f"references/{stem}.schema.json").read_text(encoding="utf-8"))
            instance = json.loads((SKILL / f"examples/{stem}.json").read_text(encoding="utf-8"))
            errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(instance))
            self.assertEqual([], errors)

    def test_skill_names_all_four_modes_and_output_sections(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for mode in ["critique", "design", "delta", "devil"]:
            self.assertIn(f"North Star {mode}", text)
        positions = [text.index(label) for label in ["Guru Verdict", "Guru Score", "Ultimate Design", "Opheldering", "Guru Contributions", "Next Moves", "Pins & Evidence"]]
        self.assertEqual(positions, sorted(positions))

    def test_response_contract_keeps_current_and_north_star_separate(self):
        schema = json.loads((SKILL / "references/response.schema.json").read_text(encoding="utf-8"))
        score_required = schema["properties"]["guru_score"]["required"]
        self.assertIn("current", score_required)
        self.assertIn("north_star", score_required)
        self.assertNotEqual("current", "north_star")

    def test_example_keeps_every_council_member_visible(self):
        benchmark = json.loads((ROOT / "benchmarks/guru-ai-engineer/2026.09.json").read_text(encoding="utf-8"))
        response = json.loads((SKILL / "examples/response.json").read_text(encoding="utf-8"))
        members = [item["member"] for item in response["guru_contributions"]]
        self.assertEqual(benchmark["council"], members)
        self.assertTrue(all(item["role"] == "abstain" for item in response["guru_contributions"]))


if __name__ == "__main__":
    unittest.main()
