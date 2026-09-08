# Critic — GB-107 attempt 1

Status: `blocking_findings`

## Blocking findings
- build adapter failed

## Repair hint
port Draft202012Validator, FormatChecker
+from referencing import Registry, Resource
+
+
+ROOT = Path(__file__).resolve().parents[1]
+SCHEMAS = ROOT / "schemas"
+LENS_PATH = ROOT / "lenses/simon-willison/2026.09.0.json"
+REVIEW_PATH = ROOT / "sources/simon-willison/2026.09.0-review.json"
+CLAIM_GROUPS = ("principles", "signature_moves", "likely_objections", "anti_patterns")
+
+
+def load(path: Path):
+    return json.loads(path.read_text(encoding="utf-8"))
+
+
+def lens_validator():
+    registry = Registry()
+    for path in SCHEMAS.glob("*.schema.json"):
+        schema = load(path)
+        if "$id" in schema:
+            registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
+    return Draft202012Validator(
+        load(SCHEMAS / "expert-lens.schema.json"),
+        registry=registry,
+        format_checker=FormatChecker(),
+    )
+
+
+class PilotLensTests(unittest.TestCase):
+    @classmethod
+    def setUpClass(cls):
+        cls.lens = load(LENS_PATH)
+        cls.review = load(REVIEW_PATH)
+
+    def test_real_pilot_lens_is_schema_valid(self):
+        self.assertEqual([], list(lens_validator().iter_errors(self.lens)))
+        self.assertEqual("expert.simon-willison", self.lens["lens_id"])
+        self.assertFalse(self.lens["expert"]["synthetic"])
+
+    def test_every_claim_resolves_to_primary_authored_sources(self):
+        sources = {source["id"]: source for source in self.lens["source_references"]}
+        self.assertEqual(len(sources), len(self.lens["source_references"]))
+        for source in sources.values():
+            self.assertTrue(source["primary"])
+            self.assertFalse(source["synthetic"])
+            self.assertEqual("Simon Willison", source["author"])
+            self.assertIn(source["source_type"], {"authored_essay", "authored_post"})
+        for group in CLAIM_GROUPS:
+            for claim in self.lens[group]:
+                self.assertTrue(claim["source_refs"])
+                self.assertLessEqual(set(claim["source_refs"]), set(sources))
+
+    def test_confidence_is_bounded_and_inferences_explain_their_basis(self):
+        self.assertEqual("high", self.lens["confidence"])
+        for group in CLAIM_GROUPS:
+            for claim in self.lens[group]:
+                self.assertIn(claim["confidence"], {"medium", "high"})
+                if claim["evidence_class"] == "labeled_inference":
+                    self.assertTrue(claim.get("inference_basis"))
+
+    def test_copyright_boundary_stores_metadata_and_paraphrase_only(self):
+        for group in CLAIM_GROUPS:
+            for claim in self.lens[group]:
+                self.assertNotIn("short_excerpt", claim)
+        for source in self.lens["source_references"]:
+            self.assertIsNone(source["content_hash"])
+            self.assertIn("metadata", source["notes"].lower())
+
+    def test_validity_window_is_forward_looking_and_bounded(self):
+        as_of = date.fromisoformat(self.lens["as_of"])
+        valid_until = date.fromisoformat(self.lens["valid_until"])
+        self.assertLess(as_of, valid_until)
+        self.assertLessEqual(valid_until - as_of, timedelta(days=120))
+        for source in self.lens["source_references"]:
+            self.assertLessEqual(date.fromisoformat(source["published_at"]), as_of)
+            self.assertLessEqual(date.fromisoformat(source["retrieved_at"]), as_of)
+
+    def test_review_records_all_required_acceptance_checks(self):
+        self.assertEqual(self.lens["lens_id"], self.review["lens_id"])
+        self.assertEqual(self.lens["version"], self.review["lens_version"])
+        self.assertEqual(
+            {
+                "source_review": "passed",
+                "confidence_review": "passed",
+                "copyright_boundary_review": "passed",
+                "validity_window_review": "passed",
+            },
+            self.review["checks"],
+        )
+
+
+if __name__ == "__main__":
+    unittest.main()

tokens used
94.651

scope violations after build adapter: sources/
