import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class ContractTests(unittest.TestCase):
    def test_vision_contract_has_required_shape(self):
        schema = load("schemas/repo-vision-contract.schema.json")
        vision = load("docs/vision.json")
        self.assertLessEqual(set(schema["required"]), set(vision))
        self.assertEqual(vision["artifact_kind"], "repo_design_vision_contract")
        self.assertEqual(vision["repo"]["name"], "guru-benchmark")
        self.assertGreaterEqual(len(vision["principles"]), 8)
        self.assertGreaterEqual(len(vision["acceptance_scorecard"]), 8)

    def test_guru_schema_encodes_core_aggregation_rules(self):
        schema = load("schemas/guru-benchmark.schema.json")
        aggregation = schema["properties"]["aggregation"]["properties"]
        self.assertEqual(aggregation["score_method"]["const"], "weighted_median")
        self.assertIn("abstention_policy", aggregation)
        self.assertIn("disagreement_policy", aggregation)

    def test_public_safety_forbids_fanfiction_and_private_data(self):
        vision = load("docs/vision.json")
        forbidden = " ".join(vision["public_safety"]["forbidden"]).lower()
        bad = " ".join(item for p in vision["principles"] for item in p["bad"]).lower()
        self.assertIn("private", forbidden)
        self.assertIn("secret", forbidden)
        self.assertIn("invented quotation", bad)

    def test_founding_council_is_documented(self):
        text = (ROOT / "docs/product-vision.md").read_text(encoding="utf-8")
        for name in ["Karpathy", "Pocock", "Steinberger", "Hickey", "Hansson", "Willison", "Hashimoto"]:
            self.assertIn(name, text)


if __name__ == "__main__":
    unittest.main()
