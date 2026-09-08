import json
import unittest
from datetime import date, timedelta
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
CLAIM_GROUPS = ("principles", "signature_moves", "likely_objections", "anti_patterns")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def validator():
    registry = Registry()
    for path in SCHEMAS.glob("*.schema.json"):
        schema = load(path)
        if "$id" in schema:
            registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    return Draft202012Validator(load(SCHEMAS / "expert-lens.schema.json"), registry=registry, format_checker=FormatChecker())


class ReviewedLensTests(unittest.TestCase):
    def test_every_published_lens_has_reviewed_provenance_and_bounded_validity(self):
        for path in sorted((ROOT / "lenses").glob("*/20*.json")):
            with self.subTest(lens=path.parent.name):
                lens = load(path)
                self.assertEqual([], list(validator().iter_errors(lens)))
                self.assertEqual(f"expert.{lens['expert']['id']}", lens["lens_id"])
                self.assertFalse(lens["expert"]["synthetic"])
                self.assertEqual("active", lens["status"])
                as_of, valid_until = date.fromisoformat(lens["as_of"]), date.fromisoformat(lens["valid_until"])
                self.assertLessEqual(valid_until - as_of, timedelta(days=120))
                sources = {item["id"]: item for item in lens["source_references"]}
                for source in sources.values():
                    self.assertTrue(source["primary"])
                    self.assertFalse(source["synthetic"])
                    self.assertIn("metadata", (source.get("notes") or "").lower())
                for group in CLAIM_GROUPS:
                    for claim in lens[group]:
                        self.assertTrue(set(claim["source_refs"]) <= set(sources))
                        self.assertNotIn("short_excerpt", claim)
                        if claim["evidence_class"] == "labeled_inference":
                            self.assertTrue(claim.get("inference_basis"))
                review = load(ROOT / "sources" / path.parent.name / f"{lens['version']}-review.json")
                self.assertEqual((lens["lens_id"], lens["version"]), (review["lens_id"], review["lens_version"]))
                self.assertEqual({"passed"}, set(review["checks"].values()))


if __name__ == "__main__":
    unittest.main()
