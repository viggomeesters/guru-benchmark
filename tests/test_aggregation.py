from __future__ import annotations

import unittest
from decimal import Decimal, localcontext
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from guru_benchmark.aggregation import AggregationError, normalize_weights, weighted_median


class NormalizeWeightsTests(unittest.TestCase):
    def test_normalizes_by_stable_identifier_with_exact_total(self) -> None:
        normalized = normalize_weights({"lens.c": 1, "lens.a": 1, "lens.b": 1})

        self.assertEqual(
            normalized,
            {
                "lens.a": Decimal("0.333333333334"),
                "lens.b": Decimal("0.333333333333"),
                "lens.c": Decimal("0.333333333333"),
            },
        )
        self.assertEqual(sum(normalized.values()), Decimal("1"))

    def test_abstentions_are_retained_at_zero_and_excluded_from_total(self) -> None:
        normalized = normalize_weights(
            {"lens.active": 2, "lens.abstaining": 100},
            abstentions={"lens.abstaining"},
        )

        self.assertEqual(
            normalized,
            {"lens.abstaining": Decimal("0"), "lens.active": Decimal("1")},
        )

    def test_normalization_is_independent_of_decimal_context(self) -> None:
        with localcontext() as context:
            context.prec = 3
            normalized = normalize_weights(
                {"lens.c": "1e100", "lens.a": "1e100", "lens.b": "1e100"}
            )

        self.assertEqual(
            normalized,
            {
                "lens.a": Decimal("0.333333333334"),
                "lens.b": Decimal("0.333333333333"),
                "lens.c": Decimal("0.333333333333"),
            },
        )
        self.assertEqual(sum(normalized.values()), Decimal("1"))

    def test_rejects_an_input_without_positive_participating_weight(self) -> None:
        with self.assertRaisesRegex(AggregationError, "positive participating weight"):
            normalize_weights(
                {"lens.zero": 0, "lens.abstaining": 1},
                abstentions={"lens.abstaining"},
            )


class WeightedMedianTests(unittest.TestCase):
    def test_returns_score_that_crosses_half_of_active_weight(self) -> None:
        score = weighted_median(
            {"lens.low": 2, "lens.middle": 7, "lens.high": 10},
            {"lens.low": 1, "lens.middle": 3, "lens.high": 1},
        )

        self.assertEqual(score, Decimal("7"))

    def test_exact_half_tie_uses_midpoint_of_adjacent_distinct_scores(self) -> None:
        fixture_path = (
            Path(__file__).parent
            / "fixtures"
            / "aggregation"
            / "exact-half-tie.json"
        )
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

        score = weighted_median(
            fixture["scores"],
            fixture["weights"],
            abstentions=fixture["abstentions"],
        )

        self.assertEqual(score, Decimal(fixture["expected"]))

    def test_normalization_rounding_does_not_move_an_exact_half_boundary(self) -> None:
        score = weighted_median(
            {
                "lens.a": 0,
                "lens.b": 1,
                "lens.c": 2,
                "lens.d": 3,
                "lens.e": 4,
            },
            {
                "lens.a": 1,
                "lens.b": 1,
                "lens.c": 1,
                "lens.d": 1,
                "lens.e": 2,
            },
        )

        self.assertEqual(score, Decimal("2.5"))

    def test_abstaining_and_zero_weight_scores_do_not_contribute(self) -> None:
        score = weighted_median(
            {
                "lens.low": 2,
                "lens.high": 8,
                "lens.zero": "not-a-score",
                "lens.abstaining": "not-a-score",
            },
            {
                "lens.low": 1,
                "lens.high": 3,
                "lens.zero": 0,
                "lens.abstaining": 100,
            },
            abstentions={"lens.abstaining"},
        )

        self.assertEqual(score, Decimal("8"))

    def test_exact_half_midpoint_is_independent_of_decimal_context(self) -> None:
        with localcontext() as context:
            context.prec = 2
            score = weighted_median(
                {"lens.lower": "123456789.123", "lens.upper": "123456789.129"},
                {"lens.lower": "1e100", "lens.upper": "1e100"},
            )

        self.assertEqual(score, Decimal("123456789.126"))


if __name__ == "__main__":
    unittest.main()
