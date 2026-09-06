from __future__ import annotations

import unittest
import json
from decimal import Decimal
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from guru_benchmark.hard_gates import (
    HardGateError,
    aggregate_with_hard_gates,
    apply_hard_gates,
)


class HardGateOrderingTests(unittest.TestCase):
    def test_hold_short_circuits_aggregate_scoring(self) -> None:
        aggregate_called = False

        def aggregate_score() -> int:
            nonlocal aggregate_called
            aggregate_called = True
            return 10

        result = apply_hard_gates(
            [{"gate_id": "correctness", "status": "fail", "effect": "hold"}],
            aggregate_score,
        )

        self.assertFalse(aggregate_called)
        self.assertEqual(result.decision, "hold")
        self.assertIsNone(result.score)

    def test_conditional_go_survives_a_perfect_aggregate_score(self) -> None:
        result = apply_hard_gates(
            [
                {
                    "gate_id": "recoverability",
                    "status": "fail",
                    "effect": "conditional_go",
                }
            ],
            lambda: 10,
        )

        self.assertEqual(result.decision, "conditional_go")
        self.assertEqual(result.score, 10)

    def test_score_cap_limits_a_perfect_aggregate_score(self) -> None:
        fixture = json.loads(
            (
                Path(__file__).parent
                / "fixtures"
                / "hard_gates"
                / "high-scores-capped.json"
            ).read_text(encoding="utf-8")
        )

        result = apply_hard_gates(
            fixture["hard_gates"],
            lambda: fixture["aggregate_score"],
            score_cap=fixture["score_cap"],
        )

        self.assertEqual(result.decision, fixture["expected_decision"])
        self.assertEqual(result.score, Decimal(str(fixture["expected_score"])))

    def test_score_cap_effect_fails_closed_without_a_configured_cap(self) -> None:
        aggregate_called = False

        def aggregate_score() -> int:
            nonlocal aggregate_called
            aggregate_called = True
            return 10

        with self.assertRaisesRegex(HardGateError, "requires an explicit score_cap"):
            apply_hard_gates(
                [{"gate_id": "evidence", "status": "fail", "effect": "score_cap"}],
                aggregate_score,
            )

        self.assertFalse(aggregate_called)

    def test_contradictory_gate_state_is_rejected_before_aggregation(self) -> None:
        contradictory_gates = [
            {"gate_id": "correctness", "status": "pass", "effect": "hold"},
            {"gate_id": "correctness", "status": "fail", "effect": "none"},
        ]
        for gate in contradictory_gates:
            with self.subTest(gate=gate):
                aggregate_called = False

                def aggregate_score() -> int:
                    nonlocal aggregate_called
                    aggregate_called = True
                    return 10

                with self.assertRaisesRegex(HardGateError, "contradictory"):
                    apply_hard_gates([gate], aggregate_score)
                self.assertFalse(aggregate_called)


class GateAwareAggregationTests(unittest.TestCase):
    def test_weighted_median_is_capped_after_gates_are_resolved(self) -> None:
        result = aggregate_with_hard_gates(
            scores={"lens.high": 9, "lens.perfect": 10},
            weights={"lens.high": 1, "lens.perfect": 3},
            gates=[{"gate_id": "evidence", "status": "fail", "effect": "score_cap"}],
            score_cap=5,
        )

        self.assertEqual(result.decision, "conditional_go")
        self.assertEqual(result.score, Decimal("5"))


if __name__ == "__main__":
    unittest.main()
