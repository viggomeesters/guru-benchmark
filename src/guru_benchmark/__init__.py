"""Deterministic evaluation primitives for Guru Benchmark."""

from .aggregation import AggregationError, normalize_weights, weighted_median
from .disagreement import (
    DisagreementError,
    DisagreementPolicy,
    DisagreementResult,
    analyze_disagreement,
)
from .hard_gates import (
    HardGateError,
    HardGateResult,
    aggregate_with_hard_gates,
    apply_hard_gates,
)
from .renderer import RendererError, render, render_evaluation, render_guru_verdict

__all__ = [
    "AggregationError",
    "DisagreementError",
    "DisagreementPolicy",
    "DisagreementResult",
    "HardGateError",
    "HardGateResult",
    "RendererError",
    "aggregate_with_hard_gates",
    "analyze_disagreement",
    "apply_hard_gates",
    "normalize_weights",
    "render",
    "render_evaluation",
    "render_guru_verdict",
    "weighted_median",
]
