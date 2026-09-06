import json
import unittest
from datetime import date
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def registry():
    result = Registry()
    for path in SCHEMAS.glob("*.schema.json"):
        schema = load(path)
        if "$id" in schema:
            result = result.with_resource(schema["$id"], Resource.from_contents(schema))
    return result


def validator():
    schema = load(SCHEMAS / "expert-lens.schema.json")
    return Draft202012Validator(schema, registry=registry(), format_checker=FormatChecker())


class ExpertLensContractTests(unittest.TestCase):
    def test_valid_synthetic_lens_passes(self):
        lens = load(ROOT / "lenses/fixtures/valid/synthetic-systems-builder.json")
        errors = list(validator().iter_errors(lens))
        self.assertEqual([], errors)
        self.assertTrue(lens["expert"]["synthetic"])

    def test_internet_stereotype_is_rejected(self):
        lens = load(ROOT / "lenses/fixtures/invalid/internet-stereotype.json")
        messages = " ".join(error.message for error in validator().iter_errors(lens))
        self.assertIn("internet_stereotype", messages)
        self.assertIn("non-empty", messages)

    def test_inference_without_basis_is_rejected(self):
        lens = load(ROOT / "lenses/fixtures/invalid/unlabeled-inference.json")
        messages = " ".join(error.message for error in validator().iter_errors(lens))
        self.assertIn("inference_basis", messages)

    def test_source_refs_resolve_and_dates_are_ordered(self):
        lens = load(ROOT / "lenses/fixtures/valid/synthetic-systems-builder.json")
        source_ids = [source["id"] for source in lens["source_references"]]
        self.assertEqual(len(source_ids), len(set(source_ids)))
        for group in ["principles", "signature_moves", "likely_objections", "anti_patterns"]:
            for claim in lens[group]:
                self.assertLessEqual(set(claim["source_refs"]), set(source_ids))
        self.assertLessEqual(date.fromisoformat(lens["as_of"]), date.fromisoformat(lens["valid_until"]))

    def test_short_excerpt_requires_direct_source(self):
        lens = load(ROOT / "lenses/fixtures/valid/synthetic-systems-builder.json")
        claim = dict(lens["principles"][0])
        claim["evidence_class"] = "built_pattern"
        claim["short_excerpt"] = "Synthetic excerpt."
        lens["principles"] = [claim]
        messages = " ".join(error.message for error in validator().iter_errors(lens))
        self.assertIn("direct_source", messages)


if __name__ == "__main__":
    unittest.main()
