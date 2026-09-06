# Critic — GB-103 attempt 2

Status: `blocking_findings`

## Blocking findings
- build adapter failed

## Repair hint
    unknown = ", ".join(sorted(unknown_abstentions))
-        raise AggregationError(f"abstention has no matching weight: {unknown}")
     active = {
-        key: value
+        key: Fraction(value)
         for key, value in converted.items()
         if key not in abstaining and value > 0
     }
@@ -110,19 +152,20 @@
     if total <= 0:
         raise AggregationError("aggregation requires positive participating weight")
 
-    weight_by_score: dict[Decimal, Decimal] = {}
+    weight_by_score: dict[Decimal, Fraction] = {}
     for key, weight in active.items():
         if key not in scores:
             raise AggregationError(f"contributing lens has no score: {key}")
         score = _decimal(scores[key], label=f"score for {key!r}")
-        weight_by_score[score] = weight_by_score.get(score, Decimal(0)) + weight
+        weight_by_score[score] = weight_by_score.get(score, Fraction(0)) + weight
     ordered = sorted(weight_by_score.items())
-    cumulative = Decimal(0)
+    cumulative = Fraction(0)
     half = total / 2
     for index, (score, weight) in enumerate(ordered):
         cumulative += weight
         if cumulative == half and index + 1 < len(ordered):
-            return (score + ordered[index + 1][0]) / 2
+            midpoint = (Fraction(score) + Fraction(ordered[index + 1][0])) / 2
+            return _fraction_to_decimal(midpoint)
         if cumulative > half:
             return score
     raise AggregationError("weighted median requires at least one contributing score")
diff --git a/tests/test_aggregation.py b/tests/test_aggregation.py
index 11600f6567330cc8e4ad924a232cc43e7f4fc657..d146a12d0ca79ffe88ca829e8a7fa4c494c52933
--- a/tests/test_aggregation.py
+++ b/tests/test_aggregation.py
@@ -1,7 +1,7 @@
 from __future__ import annotations
 
 import unittest
-from decimal import Decimal
+from decimal import Decimal, localcontext
 import json
 from pathlib import Path
 import sys
@@ -36,6 +36,23 @@
             {"lens.abstaining": Decimal("0"), "lens.active": Decimal("1")},
         )
 
+    def test_normalization_is_independent_of_decimal_context(self) -> None:
+        with localcontext() as context:
+            context.prec = 3
+            normalized = normalize_weights(
+                {"lens.c": "1e100", "lens.a": "1e100", "lens.b": "1e100"}
+            )
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
     def test_rejects_an_input_without_positive_participating_weight(self) -> None:
         with self.assertRaisesRegex(AggregationError, "positive participating weight"):
             normalize_weights(
@@ -90,6 +107,35 @@
 
         self.assertEqual(score, Decimal("2.5"))
 
+    def test_abstaining_and_zero_weight_scores_do_not_contribute(self) -> None:
+        score = weighted_median(
+            {
+                "lens.low": 2,
+                "lens.high": 8,
+                "lens.zero": "not-a-score",
+                "lens.abstaining": "not-a-score",
+            },
+            {
+                "lens.low": 1,
+                "lens.high": 3,
+                "lens.zero": 0,
+                "lens.abstaining": 100,
+            },
+            abstentions={"lens.abstaining"},
+        )
+
+        self.assertEqual(score, Decimal("8"))
+
+    def test_exact_half_midpoint_is_independent_of_decimal_context(self) -> None:
+        with localcontext() as context:
+            context.prec = 2
+            score = weighted_median(
+                {"lens.lower": "123456789.123", "lens.upper": "123456789.129"},
+                {"lens.lower": "1e100", "lens.upper": "1e100"},
+            )
+
+        self.assertEqual(score, Decimal("123456789.126"))
+
 
 if __name__ == "__main__":
     unittest.main()

tokens used
68.325

scope violations after build adapter: src/
