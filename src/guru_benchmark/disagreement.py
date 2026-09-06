"""Deterministic, policy-driven disagreement analysis."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from typing import Iterable, Mapping

from .aggregation import AggregationError, Number, normalize_weights


class DisagreementError(ValueError):
    """Raised when disagreement inputs are incomplete or contradictory."""


def _decimal(value: Number, *, label: str) -> Decimal:
    if isinstance(value, bool):
        raise DisagreementError(f"{label} must be a finite number")
    try:
        converted = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise DisagreementError(f"{label} must be a finite number") from None
    if not converted.is_finite():
        raise DisagreementError(f"{label} must be a finite number")
    return converted


def _display(value: Decimal) -> str:
    rendered = format(value, "f")
    return rendered.rstrip("0").rstrip(".") if "." in rendered else rendered


def _fraction_to_decimal(value: Fraction) -> Decimal:
    """Return an exact decimal without consulting the ambient context."""
    numerator = value.numerator
    denominator = value.denominator
    twos = fives = 0
    while denominator % 2 == 0:
        denominator //= 2
        twos += 1
    while denominator % 5 == 0:
        denominator //= 5
        fives += 1
    if denominator != 1:  # Decimal inputs always produce a terminating result.
        raise DisagreementError("score dispersion is not a finite decimal")
    places = max(twos, fives)
    units = numerator * (2 ** (places - twos)) * (5 ** (places - fives))
    sign = 1 if units < 0 else 0
    digits = tuple(int(digit) for digit in str(abs(units))) if units else (0,)
    return Decimal((sign, digits, -places))


@dataclass(frozen=True)
class DisagreementPolicy:
    """Version-pinned materiality thresholds supplied by the caller."""

    dispersion_threshold: Number
    recommendation_weight_threshold: Number


@dataclass(frozen=True)
class DisagreementResult:
    """Compact clarification decision and its inspectable causes."""

    score_dispersion: Decimal
    clarification_required: bool
    reasons: tuple[str, ...]
    conflicting_actions: tuple[tuple[str, str], ...]
    summary: str


def analyze_disagreement(
    *,
    scores: Mapping[str, Number],
    weights: Mapping[str, Number],
    recommendations: Mapping[str, str],
    policy: DisagreementPolicy,
    incompatible_actions: Iterable[tuple[str, str]] = (),
    abstentions: Iterable[str] = (),
) -> DisagreementResult:
    """Detect material score range and explicitly modeled action conflicts."""
    abstaining = set(abstentions)
    try:
        normalize_weights(weights, abstentions=abstaining)
    except AggregationError as error:
        raise DisagreementError(str(error)) from None
    converted_weights = {
        lens_id: _decimal(value, label=f"weight for {lens_id!r}")
        for lens_id, value in weights.items()
    }
    active = {
        lens_id: weight
        for lens_id, weight in converted_weights.items()
        if weight > 0 and lens_id not in abstaining
    }
    total_weight = sum(Fraction(weight) for weight in active.values())
    exact_weights = {
        lens_id: Fraction(weight) / total_weight
        for lens_id, weight in active.items()
    }
    missing_scores = active.keys() - scores.keys()
    if missing_scores:
        raise DisagreementError(
            f"contributing lens has no score: {sorted(missing_scores)[0]}"
        )
    converted = []
    for lens_id in active:
        score = _decimal(scores[lens_id], label=f"score for {lens_id!r}")
        if not Decimal(0) <= score <= Decimal(10):
            raise DisagreementError(f"score for {lens_id!r} must be from 0 to 10")
        converted.append(score)
    dispersion = _fraction_to_decimal(
        Fraction(max(converted)) - Fraction(min(converted))
    )
    threshold = _decimal(
        policy.dispersion_threshold, label="dispersion_threshold"
    )
    if not Decimal(0) <= threshold <= Decimal(10):
        raise DisagreementError("dispersion_threshold must be from 0 to 10")
    weight_threshold = _decimal(
        policy.recommendation_weight_threshold,
        label="recommendation_weight_threshold",
    )
    if not Decimal(0) < weight_threshold <= Decimal(1):
        raise DisagreementError(
            "recommendation_weight_threshold must be greater than 0 and at most 1"
        )

    action_lenses: dict[str, list[str]] = {}
    for lens_id, action in recommendations.items():
        if lens_id not in active:
            continue
        if not isinstance(action, str) or not action.strip():
            raise DisagreementError(
                f"recommendation for {lens_id!r} must be a non-empty action"
            )
        if exact_weights[lens_id] >= Fraction(weight_threshold):
            action_lenses.setdefault(action, []).append(lens_id)

    conflicts: set[tuple[str, str]] = set()
    for pair in incompatible_actions:
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise DisagreementError("incompatible action pairs must contain two actions")
        left, right = pair
        if (
            not isinstance(left, str)
            or not left
            or not isinstance(right, str)
            or not right
            or left == right
        ):
            raise DisagreementError(
                "incompatible action pairs require two distinct non-empty actions"
            )
        if left in action_lenses and right in action_lenses:
            conflicts.add(tuple(sorted((left, right))))

    reasons = []
    summaries = []
    if dispersion > threshold:
        reasons.append("score_dispersion")
        summaries.append(
            f"Material score dispersion: range {_display(dispersion)} exceeds "
            f"threshold {_display(threshold)}."
        )
    ordered_conflicts = tuple(sorted(conflicts))
    if ordered_conflicts:
        reasons.append("incompatible_recommendations")
        rendered = "; ".join(
            f"{left} versus {right}" for left, right in ordered_conflicts
        )
        summaries.append(f"Material recommendation conflict: {rendered}.")

    return DisagreementResult(
        score_dispersion=dispersion,
        clarification_required=bool(reasons),
        reasons=tuple(reasons),
        conflicting_actions=ordered_conflicts,
        summary=" ".join(summaries) if summaries else "None material.",
    )
