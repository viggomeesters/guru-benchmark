"""Fail-closed hard-gate policy for aggregate scores."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Callable, Iterable, Mapping, Optional

from .aggregation import Number, weighted_median


class HardGateError(ValueError):
    """Raised when gate inputs cannot produce a fail-closed result."""


@dataclass(frozen=True)
class HardGateResult:
    """The decision and score remaining after hard-gate effects."""

    decision: str
    score: Optional[Decimal]


def _validate_gates(gates: Iterable[Mapping[str, object]]) -> list[Mapping[str, object]]:
    gate_list = list(gates)
    if not gate_list:
        raise HardGateError("at least one hard gate is required")
    seen: set[str] = set()
    for gate in gate_list:
        gate_id = gate.get("gate_id")
        status = gate.get("status")
        effect = gate.get("effect")
        if not isinstance(gate_id, str) or not gate_id:
            raise HardGateError("gate_id must be a non-empty string")
        if gate_id in seen:
            raise HardGateError(f"duplicate hard gate: {gate_id}")
        seen.add(gate_id)
        if status not in {"pass", "fail", "unknown"}:
            raise HardGateError(f"unsupported status for hard gate {gate_id}: {status!r}")
        if effect not in {"none", "hold", "score_cap", "conditional_go"}:
            raise HardGateError(f"unsupported effect for hard gate {gate_id}: {effect!r}")
        if (status == "pass") != (effect == "none"):
            raise HardGateError(
                f"contradictory status/effect for hard gate {gate_id}: {status}/{effect}"
            )
    return gate_list


def _bounded_score(value: Number, *, label: str) -> Decimal:
    if isinstance(value, bool):
        raise HardGateError(f"{label} must be a finite score from 0 to 10")
    try:
        score = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise HardGateError(f"{label} must be a finite score from 0 to 10") from None
    if not score.is_finite() or not Decimal(0) <= score <= Decimal(10):
        raise HardGateError(f"{label} must be a finite score from 0 to 10")
    return score


def apply_hard_gates(
    gates: Iterable[Mapping[str, object]],
    aggregate_score: Callable[[], Number],
    *,
    score_cap: Optional[Number] = None,
) -> HardGateResult:
    """Apply blocking gate effects before invoking aggregate scoring."""
    gate_list = _validate_gates(gates)
    if any(
        gate.get("status") in {"fail", "unknown"}
        and gate.get("effect") == "hold"
        for gate in gate_list
    ):
        return HardGateResult(decision="hold", score=None)
    conditional = any(
        gate.get("status") in {"fail", "unknown"}
        and gate.get("effect") in {"conditional_go", "score_cap"}
        for gate in gate_list
    )
    decision = "conditional_go" if conditional else "go"
    has_cap = any(
        gate.get("status") in {"fail", "unknown"}
        and gate.get("effect") == "score_cap"
        for gate in gate_list
    )
    if has_cap and score_cap is None:
        raise HardGateError("score_cap effect requires an explicit score_cap")
    cap = _bounded_score(score_cap, label="score_cap") if has_cap else None
    score = _bounded_score(aggregate_score(), label="aggregate score")
    if has_cap:
        assert cap is not None
        score = min(score, cap)
    return HardGateResult(decision=decision, score=score)


def aggregate_with_hard_gates(
    scores: Mapping[str, Number],
    weights: Mapping[str, Number],
    gates: Iterable[Mapping[str, object]],
    *,
    score_cap: Optional[Number] = None,
    abstentions: Iterable[str] = (),
) -> HardGateResult:
    """Resolve gates, then aggregate eligible scores with the weighted median."""
    return apply_hard_gates(
        gates,
        lambda: weighted_median(scores, weights, abstentions=abstentions),
        score_cap=score_cap,
    )
