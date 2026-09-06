from __future__ import annotations

from decimal import Decimal, localcontext
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from guru_benchmark.disagreement import DisagreementPolicy, analyze_disagreement


class ScoreDispersionTests(unittest.TestCase):
    def test_material_score_range_requires_clarification(self) -> None:
        result = analyze_disagreement(
            scores={"lens.low": 4, "lens.high": 8},
            weights={"lens.low": 1, "lens.high": 1},
            recommendations={"lens.low": "revise", "lens.high": "revise"},
            policy=DisagreementPolicy(
                dispersion_threshold=3,
                recommendation_weight_threshold="0.2",
            ),
        )

        self.assertEqual(result.score_dispersion, Decimal("4"))
        self.assertTrue(result.clarification_required)
        self.assertEqual(result.reasons, ("score_dispersion",))
        self.assertEqual(
            result.summary,
            "Material score dispersion: range 4 exceeds threshold 3.",
        )

    def test_full_scale_dispersion_is_rendered_exactly(self) -> None:
        result = analyze_disagreement(
            scores={"lens.low": 0, "lens.high": 10},
            weights={"lens.low": 1, "lens.high": 1},
            recommendations={},
            policy=DisagreementPolicy(
                dispersion_threshold=9,
                recommendation_weight_threshold="0.2",
            ),
        )

        self.assertEqual(
            result.summary,
            "Material score dispersion: range 10 exceeds threshold 9.",
        )

    def test_dispersion_is_independent_of_ambient_decimal_precision(self) -> None:
        with localcontext() as context:
            context.prec = 2
            result = analyze_disagreement(
                scores={"lens.low": "1.111", "lens.high": "2.345"},
                weights={"lens.low": 1, "lens.high": 1},
                recommendations={},
                policy=DisagreementPolicy(
                    dispersion_threshold="1.23",
                    recommendation_weight_threshold="0.2",
                ),
            )

        self.assertEqual(result.score_dispersion, Decimal("1.234"))
        self.assertTrue(result.clarification_required)
        self.assertEqual(
            result.summary,
            "Material score dispersion: range 1.234 exceeds threshold 1.23.",
        )


class RecommendationConflictTests(unittest.TestCase):
    def test_sufficiently_weighted_incompatible_actions_require_clarification(self) -> None:
        result = analyze_disagreement(
            scores={"lens.ship": 7, "lens.hold": 7},
            weights={"lens.ship": 3, "lens.hold": 2},
            recommendations={"lens.ship": "ship", "lens.hold": "hold"},
            incompatible_actions=[("hold", "ship")],
            policy=DisagreementPolicy(
                dispersion_threshold=3,
                recommendation_weight_threshold="0.35",
            ),
        )

        self.assertTrue(result.clarification_required)
        self.assertEqual(result.reasons, ("incompatible_recommendations",))
        self.assertEqual(result.conflicting_actions, (("hold", "ship"),))
        self.assertEqual(
            result.summary,
            "Material recommendation conflict: hold versus ship.",
        )

    def test_display_rounding_cannot_promote_a_subthreshold_lens(self) -> None:
        result = analyze_disagreement(
            scores={"lens.ship": 7, "lens.hold": 7},
            weights={"lens.ship": "0.3499999999999", "lens.hold": "0.6500000000001"},
            recommendations={"lens.ship": "ship", "lens.hold": "hold"},
            incompatible_actions=[("hold", "ship")],
            policy=DisagreementPolicy(
                dispersion_threshold=3,
                recommendation_weight_threshold="0.35",
            ),
        )

        self.assertFalse(result.clarification_required)
        self.assertEqual(result.summary, "None material.")


class PublicApiTests(unittest.TestCase):
    def test_disagreement_engine_is_available_from_the_package(self) -> None:
        from guru_benchmark import (
            DisagreementError,
            DisagreementPolicy,
            DisagreementResult,
            analyze_disagreement,
        )

        self.assertTrue(issubclass(DisagreementError, ValueError))
        self.assertTrue(callable(DisagreementPolicy))
        self.assertTrue(callable(DisagreementResult))
        self.assertTrue(callable(analyze_disagreement))


class SyntheticFixtureTests(unittest.TestCase):
    def test_material_and_harmless_cases_follow_the_same_versioned_policy(self) -> None:
        fixture = json.loads(
            (
                Path(__file__).parent
                / "fixtures"
                / "disagreement"
                / "material-and-harmless.json"
            ).read_text(encoding="utf-8")
        )
        self.assertTrue(fixture["synthetic"])
        policy = DisagreementPolicy(**fixture["policy"])

        for case in fixture["cases"]:
            with self.subTest(case=case["id"]):
                result = analyze_disagreement(
                    scores=case["scores"],
                    weights=case["weights"],
                    recommendations=case["recommendations"],
                    incompatible_actions=fixture["incompatible_actions"],
                    abstentions=case["abstentions"],
                    policy=policy,
                )

                self.assertEqual(
                    result.clarification_required, case["expected_required"]
                )
                self.assertEqual(
                    result.score_dispersion,
                    Decimal(str(case["expected_dispersion"])),
                )
                self.assertEqual(result.reasons, tuple(case["expected_reasons"]))
                if not case["expected_required"]:
                    self.assertEqual(result.summary, "None material.")


if __name__ == "__main__":
    unittest.main()
