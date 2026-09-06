"""Deterministic council-weight aggregation."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from fractions import Fraction
from typing import Iterable, Mapping, Union

Number = Union[int, float, str, Decimal]


class AggregationError(ValueError):
    """Raised when weights or scores cannot produce an honest aggregate."""


def _decimal(value: Number, *, label: str) -> Decimal:
    if isinstance(value, bool):
        raise AggregationError(f"{label} must be a finite number")
    try:
        converted = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise AggregationError(f"{label} must be a finite number") from None
    if not converted.is_finite():
        raise AggregationError(f"{label} must be a finite number")
    return converted


def _identifiers(
    weights: Mapping[str, Number], abstentions: Iterable[str]
) -> tuple[set[str], set[str]]:
    weight_ids = set(weights)
    if any(not isinstance(identifier, str) or not identifier for identifier in weight_ids):
        raise AggregationError("lens identifiers must be non-empty strings")
    abstaining = set(abstentions)
    if any(
        not isinstance(identifier, str) or not identifier for identifier in abstaining
    ):
        raise AggregationError("abstention identifiers must be non-empty strings")
    unknown_abstentions = abstaining - weight_ids
    if unknown_abstentions:
        unknown = ", ".join(sorted(unknown_abstentions))
        raise AggregationError(f"abstention has no matching weight: {unknown}")
    return weight_ids, abstaining


def _scaled_decimal(units: int, places: int) -> Decimal:
    """Build a decimal without consulting the process-wide decimal context."""
    digits = tuple(int(digit) for digit in str(units)) if units else (0,)
    return Decimal((0, digits, -places))


def _fraction_to_decimal(value: Fraction) -> Decimal:
    """Convert a terminating fraction to an exact, context-independent decimal."""
    numerator = value.numerator
    denominator = value.denominator
    twos = fives = 0
    while denominator % 2 == 0:
        denominator //= 2
        twos += 1
    while denominator % 5 == 0:
        denominator //= 5
        fives += 1
    if denominator != 1:  # Defensive: decimal inputs can only yield 2/5 factors.
        raise AggregationError("aggregate cannot be represented as a finite decimal")
    places = max(twos, fives)
    units = numerator * (2 ** (places - twos)) * (5 ** (places - fives))
    sign = 1 if units < 0 else 0
    digits = tuple(int(digit) for digit in str(abs(units))) if units else (0,)
    return Decimal((sign, digits, -places))


def normalize_weights(
    weights: Mapping[str, Number],
    *,
    abstentions: Iterable[str] = (),
    places: int = 12,
) -> dict[str, Decimal]:
    """Normalize participating weights to an exact decimal unit total.

    Results have ``places`` decimal places. Any leftover units after rounding
    down go to the largest fractional remainders, with the stable identifier as
    the final tie-breaker. Abstaining identifiers remain visible at zero but do
    not enter the denominator.
    """
    if not isinstance(places, int) or isinstance(places, bool) or places < 0:
        raise AggregationError("places must be a non-negative integer")
    _, abstaining = _identifiers(weights, abstentions)
    converted = {
        key: _decimal(value, label=f"weight for {key!r}")
        for key, value in weights.items()
    }
    if any(value < 0 for value in converted.values()):
        raise AggregationError("weights must be non-negative")
    active = {
        key: Fraction(value)
        for key, value in converted.items()
        if key not in abstaining
    }
    total = sum(active.values())
    if total <= 0:
        raise AggregationError("aggregation requires positive participating weight")
    scale = 10**places
    exact_units = {key: value * scale / total for key, value in active.items()}
    floor_units = {
        key: value.numerator // value.denominator
        for key, value in exact_units.items()
    }
    units_left = scale - sum(floor_units.values())
    remainders = sorted(
        active,
        key=lambda key: (-(exact_units[key] - floor_units[key]), key),
    )
    for key in remainders[:units_left]:
        floor_units[key] += 1
    normalized = {
        key: Decimal(0)
        if key in abstaining
        else _scaled_decimal(floor_units[key], places)
        for key in converted
    }
    return dict(sorted(normalized.items()))


def weighted_median(
    scores: Mapping[str, Number],
    weights: Mapping[str, Number],
    *,
    abstentions: Iterable[str] = (),
) -> Decimal:
    """Return the weighted median of non-abstaining lens scores.

    When cumulative weight lands exactly on one half between two distinct
    scores, the result is their midpoint. This is the weighted analogue of the
    conventional median for an even, equally weighted sample.
    """
    # Use the original weights here rather than the display-normalized values.
    # Quantization is deterministic, but its remainder allocation can move an
    # exact half boundary and therefore must not change the aggregate score.
    _, abstaining = _identifiers(weights, abstentions)
    converted = {
        key: _decimal(value, label=f"weight for {key!r}")
        for key, value in weights.items()
    }
    if any(value < 0 for value in converted.values()):
        raise AggregationError("weights must be non-negative")
    active = {
        key: Fraction(value)
        for key, value in converted.items()
        if key not in abstaining and value > 0
    }
    total = sum(active.values())
    if total <= 0:
        raise AggregationError("aggregation requires positive participating weight")

    weight_by_score: dict[Decimal, Fraction] = {}
    for key, weight in active.items():
        if key not in scores:
            raise AggregationError(f"contributing lens has no score: {key}")
        score = _decimal(scores[key], label=f"score for {key!r}")
        weight_by_score[score] = weight_by_score.get(score, Fraction(0)) + weight
    ordered = sorted(weight_by_score.items())
    cumulative = Fraction(0)
    half = total / 2
    for index, (score, weight) in enumerate(ordered):
        cumulative += weight
        if cumulative == half and index + 1 < len(ordered):
            midpoint = (Fraction(score) + Fraction(ordered[index + 1][0])) / 2
            return _fraction_to_decimal(midpoint)
        if cumulative > half:
            return score
    raise AggregationError("weighted median requires at least one contributing score")
