# Critic — GB-103 attempt 1

Status: `blocking_findings`

## Blocking findings
- build adapter failed

## Repair hint
core[score] = weight_by_score.get(score, Decimal(0)) + weight
+    ordered = sorted(weight_by_score.items())
+    cumulative = Decimal(0)
+    for index, (score, weight) in enumerate(ordered):
+        cumulative += weight
+        if cumulative == Decimal("0.5") and index + 1 < len(ordered):
+            return (score + ordered[index + 1][0]) / 2
+        if cumulative > Decimal("0.5"):
+            return score
+    raise AggregationError("weighted median requires at least one contributing score")
diff --git a/tests/fixtures/aggregation/exact-half-tie.json b/tests/fixtures/aggregation/exact-half-tie.json
new file mode 100644
index 0000000000000000000000000000000000000000..dfd0561468e01a8e3fea36e9016c1b0fecdcfae8
--- /dev/null
+++ b/tests/fixtures/aggregation/exact-half-tie.json
@@ -0,0 +1,15 @@
+{
+  "synthetic": true,
+  "description": "At an exact 50 percent boundary, use the midpoint between the adjacent distinct scores.",
+  "scores": {
+    "expert.synthetic-lower": 4,
+    "expert.synthetic-upper": 8
+  },
+  "weights": {
+    "expert.synthetic-lower": 1,
+    "expert.synthetic-upper": 1,
+    "expert.synthetic-abstaining": 100
+  },
+  "abstentions": ["expert.synthetic-abstaining"],
+  "expected": "6"
+}
diff --git a/tests/test_aggregation.py b/tests/test_aggregation.py
new file mode 100644
index 0000000000000000000000000000000000000000..c9742913cbb6d43a04d70d3014aa35dbca2120fc
--- /dev/null
+++ b/tests/test_aggregation.py
@@ -0,0 +1,75 @@
+from __future__ import annotations
+
+import unittest
+from decimal import Decimal
+import json
+from pathlib import Path
+import sys
+
+sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
+
+from guru_benchmark.aggregation import AggregationError, normalize_weights, weighted_median
+
+
+class NormalizeWeightsTests(unittest.TestCase):
+    def test_normalizes_by_stable_identifier_with_exact_total(self) -> None:
+        normalized = normalize_weights({"lens.c": 1, "lens.a": 1, "lens.b": 1})
+
+        self.assertEqual(
+            normalized,
+            {
+                "lens.a": Decimal("0.333333333334"),
+                "lens.b": Decimal("0.333333333333"),
+                "lens.c": Decimal("0.333333333333"),
+            },
+        )
+        self.assertEqual(sum(normalized.values()), Decimal("1"))
+
+    def test_abstentions_are_retained_at_zero_and_excluded_from_total(self) -> None:
+        normalized = normalize_weights(
+            {"lens.active": 2, "lens.abstaining": 100},
+            abstentions={"lens.abstaining"},
+        )
+
+        self.assertEqual(
+            normalized,
+            {"lens.abstaining": Decimal("0"), "lens.active": Decimal("1")},
+        )
+
+    def test_rejects_an_input_without_positive_participating_weight(self) -> None:
+        with self.assertRaisesRegex(AggregationError, "positive participating weight"):
+            normalize_weights(
+                {"lens.zero": 0, "lens.abstaining": 1},
+                abstentions={"lens.abstaining"},
+            )
+
+
+class WeightedMedianTests(unittest.TestCase):
+    def test_returns_score_that_crosses_half_of_active_weight(self) -> None:
+        score = weighted_median(
+            {"lens.low": 2, "lens.middle": 7, "lens.high": 10},
+            {"lens.low": 1, "lens.middle": 3, "lens.high": 1},
+        )
+
+        self.assertEqual(score, Decimal("7"))
+
+    def test_exact_half_tie_uses_midpoint_of_adjacent_distinct_scores(self) -> None:
+        fixture_path = (
+            Path(__file__).parent
+            / "fixtures"
+            / "aggregation"
+            / "exact-half-tie.json"
+        )
+        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
+
+        score = weighted_median(
+            fixture["scores"],
+            fixture["weights"],
+            abstentions=fixture["abstentions"],
+        )
+
+        self.assertEqual(score, Decimal(fixture["expected"]))
+
+
+if __name__ == "__main__":
+    unittest.main()

tokens used
67.457

scope violations after build adapter: src/
