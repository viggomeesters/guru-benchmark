#!/usr/bin/env python3
"""Validate Guru Benchmark context and evaluation contracts fail-closed."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def schema_validator(schema_name: str) -> Draft202012Validator:
    registry = Registry()
    for path in SCHEMAS.glob("*.schema.json"):
        schema = load(path)
        if "$id" in schema:
            registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    return Draft202012Validator(
        load(SCHEMAS / schema_name),
        registry=registry,
        format_checker=FormatChecker(),
    )


def schema_errors(instance: dict[str, Any], schema_name: str) -> list[str]:
    errors = sorted(
        schema_validator(schema_name).iter_errors(instance),
        key=lambda error: list(error.absolute_path),
    )
    return [
        f"{'/'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
        for error in errors
    ]


def _exact_pin(document: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    return {field: document[field] for field in fields}


def _datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def semantic_errors(
    evaluation: dict[str, Any],
    benchmark: dict[str, Any],
    context: dict[str, Any],
    lenses: list[dict[str, Any]],
) -> list[str]:
    """Check cross-document invariants JSON Schema cannot express."""
    errors: list[str] = []
    inputs = evaluation["inputs"]

    expected_benchmark_pin = _exact_pin(benchmark, ("benchmark_id", "version", "as_of"))
    if inputs["benchmark"] != expected_benchmark_pin:
        errors.append("benchmark pin does not exactly match the supplied benchmark snapshot")

    expected_context_pin = _exact_pin(context, ("context_id", "version", "as_of"))
    if inputs["context"] != expected_context_pin:
        errors.append("context pin does not exactly match the supplied context snapshot")

    supplied_lenses: dict[str, dict[str, Any]] = {}
    for lens in lenses:
        lens_id = lens["lens_id"]
        if lens_id in supplied_lenses:
            errors.append(f"duplicate supplied lens snapshot: {lens_id}")
        supplied_lenses[lens_id] = lens
        expected_lens_id = f"expert.{lens['expert']['id']}"
        if lens_id != expected_lens_id:
            errors.append(
                f"lens identity does not match expert identity: {lens_id}/{lens['expert']['id']}"
            )
        source_ids = [source["id"] for source in lens["source_references"]]
        if len(source_ids) != len(set(source_ids)):
            errors.append(f"duplicate lens source identifier: {lens_id}")
        source_id_set = set(source_ids)
        for group in ("principles", "signature_moves", "likely_objections", "anti_patterns"):
            for claim in lens[group]:
                if not set(claim["source_refs"]) <= source_id_set:
                    errors.append(
                        f"dangling lens claim source reference: {lens_id}/{group}/{claim['id']}"
                    )
        if lens["as_of"] > lens["valid_until"]:
            errors.append(f"lens validity ends before its snapshot date: {lens_id}")

    lens_pins = inputs["lenses"]
    lens_ids = [pin["lens_id"] for pin in lens_pins]
    if len(lens_ids) != len(set(lens_ids)):
        errors.append("duplicate lens_id pin")
    for pin in lens_pins:
        lens = supplied_lenses.get(pin["lens_id"])
        if lens is None:
            errors.append(f"pinned lens snapshot was not supplied: {pin['lens_id']}")
        elif pin != _exact_pin(lens, ("lens_id", "version", "as_of")):
            errors.append(f"lens pin does not exactly match supplied snapshot: {pin['lens_id']}")

    generated_date = evaluation["generated_at"][:10]
    cutoff_date = inputs["source_cutoff"]["as_of"]
    if cutoff_date > generated_date:
        errors.append("source cutoff is later than evaluation generation")
    if benchmark["as_of"] > cutoff_date:
        errors.append("benchmark snapshot is later than the source cutoff")
    pinned_sources: dict[str, dict[str, Any]] = {}
    for lens in lenses:
        if lens["lens_id"] in lens_ids and lens["as_of"] > cutoff_date:
            errors.append(f"lens snapshot is later than the source cutoff: {lens['lens_id']}")
        if lens["lens_id"] in lens_ids:
            if lens["status"] != "active":
                errors.append(f"pinned lens is not active: {lens['lens_id']}")
            if generated_date > lens["valid_until"]:
                errors.append(f"pinned lens is expired at evaluation generation: {lens['lens_id']}")
            for source in lens["source_references"]:
                existing_source = pinned_sources.get(source["id"])
                if existing_source is not None and existing_source != source:
                    errors.append(
                        f"conflicting pinned lens source identifier: {source['id']}"
                    )
                else:
                    pinned_sources[source["id"]] = source
                for field in ("published_at", "retrieved_at"):
                    value = source.get(field)
                    if value is not None and value > lens["as_of"]:
                        errors.append(
                            f"lens source {field} is later than the lens snapshot: "
                            f"{lens['lens_id']}/{source['id']}"
                        )
                    if value is not None and value > cutoff_date:
                        errors.append(
                            f"lens source {field} is later than the source cutoff: "
                            f"{lens['lens_id']}/{source['id']}"
                        )
    if context["as_of"] > generated_date:
        errors.append("context snapshot is later than evaluation generation")
    if evaluation["synthetic"]:
        if not context["synthetic"]:
            errors.append("synthetic evaluation requires a synthetic context")
        if context["privacy"] != {"classification": "public", "publishable": True}:
            errors.append("synthetic evaluation requires a public, publishable context")
        for lens in lenses:
            if lens["lens_id"] in lens_ids and not lens["expert"]["synthetic"]:
                errors.append(
                    f"synthetic evaluation requires synthetic pinned lenses: {lens['lens_id']}"
                )
    else:
        if context["synthetic"]:
            errors.append("non-synthetic evaluation cannot use a synthetic context")
        for lens in lenses:
            if lens["lens_id"] in lens_ids and lens["expert"]["synthetic"]:
                errors.append(
                    f"non-synthetic evaluation cannot use synthetic pinned lenses: {lens['lens_id']}"
                )

    current_evidence = evaluation["current_score"]["observed_evidence"]
    north_star_evidence = evaluation["north_star_score"]["conditional_evidence"]
    current_ids = [item["id"] for item in current_evidence]
    north_star_ids = [item["id"] for item in north_star_evidence]
    current_id_set = set(current_ids)
    north_star_id_set = set(north_star_ids)
    if len(current_ids) != len(current_id_set):
        errors.append("duplicate current evidence identifier")
    if len(north_star_ids) != len(north_star_id_set):
        errors.append("duplicate north-star evidence identifier")
    if current_id_set & north_star_id_set:
        errors.append("current and north-star evidence identifiers overlap")
    generated_at = _datetime(evaluation["generated_at"])
    cutoff = date.fromisoformat(cutoff_date)
    pinned_source_ids = set(pinned_sources)
    for evidence in current_evidence:
        observed_at = _datetime(evidence["observed_at"])
        if observed_at > generated_at:
            errors.append(f"current evidence is later than evaluation generation: {evidence['id']}")
        if observed_at.date() > cutoff:
            errors.append(f"current evidence is later than the source cutoff: {evidence['id']}")
        if evidence["kind"] == "public_source" and not set(evidence["source_refs"]) <= pinned_source_ids:
            errors.append(f"dangling public-source evidence reference: {evidence['id']}")

    for dimension in evaluation["current_score"]["dimensions"]:
        if not set(dimension["evidence_refs"]) <= current_id_set:
            errors.append(f"dangling current evidence reference in dimension: {dimension['dimension_id']}")
    for dimension in evaluation["north_star_score"]["dimensions"]:
        if not set(dimension["evidence_refs"]) <= north_star_id_set:
            errors.append(f"dangling north-star evidence reference in dimension: {dimension['dimension_id']}")
    for evidence in north_star_evidence:
        if not set(evidence["basis_refs"]) <= current_id_set:
            errors.append(f"dangling north-star basis reference: {evidence['id']}")

    expected_dimensions = [item["id"] for item in benchmark["dimensions"]]
    for score_name in ("current_score", "north_star_score"):
        actual_dimensions = [item["dimension_id"] for item in evaluation[score_name]["dimensions"]]
        if evaluation["status"] == "complete" and actual_dimensions != expected_dimensions:
            errors.append(f"{score_name} dimensions do not match the pinned benchmark order")
        elif evaluation["status"] == "held":
            expected_subset = [item for item in expected_dimensions if item in actual_dimensions]
            if actual_dimensions != expected_subset or len(actual_dimensions) != len(set(actual_dimensions)):
                errors.append(f"{score_name} dimensions are not an ordered subset of the pinned benchmark")

    gate_ids = [gate["gate_id"] for gate in evaluation["hard_gates"]]
    expected_gate_ids = [gate["id"] for gate in benchmark["hard_gates"]]
    if gate_ids != expected_gate_ids:
        errors.append("hard gates do not match the pinned benchmark order")
    benchmark_gates = {gate["id"]: gate for gate in benchmark["hard_gates"]}
    for gate in evaluation["hard_gates"]:
        if not set(gate["evidence_refs"]) <= current_id_set:
            errors.append(f"dangling hard-gate evidence reference: {gate['gate_id']}")
        benchmark_gate = benchmark_gates.get(gate["gate_id"])
        expected_effect = "none" if gate["status"] == "pass" else (
            benchmark_gate["failure_effect"] if benchmark_gate else None
        )
        if expected_effect is not None and gate["effect"] != expected_effect:
            errors.append(f"hard-gate effect does not match status and benchmark: {gate['gate_id']}")

    expected_contribution_ids = [f"expert.{member}" for member in benchmark["council"]]
    contributions = evaluation["guru_contributions"]
    contribution_ids = [item["lens_id"] for item in contributions]
    if contribution_ids != expected_contribution_ids:
        errors.append("guru contributions do not account for the pinned council in benchmark order")
    active_contributions = [
        contribution for contribution in contributions if contribution["role"] != "abstain"
    ]
    active_weight = sum(contribution["weight"] for contribution in active_contributions)
    if evaluation["status"] == "complete" and not active_contributions:
        errors.append("a complete evaluation requires at least one non-abstaining guru contribution")
    elif active_contributions and abs(active_weight - 1.0) > 1e-9:
        errors.append(
            f"non-abstaining guru contribution weights must sum to 1.0, got {active_weight}"
        )
    for contribution in contributions:
        if contribution["role"] != "abstain":
            if contribution["lens_id"] not in lens_ids:
                errors.append(f"non-abstaining contribution has no pinned lens: {contribution['lens_id']}")
            if not set(contribution["evidence_refs"]) <= current_id_set | north_star_id_set:
                errors.append(f"unsupported guru contribution: {contribution['lens_id']}")
            lens = supplied_lenses.get(contribution["lens_id"])
            if lens is not None:
                claim_ids = [
                    claim["id"]
                    for group in ("principles", "signature_moves", "likely_objections", "anti_patterns")
                    for claim in lens[group]
                ]
                if len(claim_ids) != len(set(claim_ids)):
                    errors.append(f"duplicate lens claim identifier: {contribution['lens_id']}")
                if not set(contribution["lens_claim_refs"]) <= set(claim_ids):
                    errors.append(f"dangling lens claim reference: {contribution['lens_id']}")

    if evaluation["status"] == "held" and evaluation["verdict"]["decision"] != "hold":
        errors.append("a held evaluation must have a hold verdict")
    return errors


def validate_contract(
    evaluation: dict[str, Any],
    benchmark: dict[str, Any],
    context: dict[str, Any],
    lenses: list[dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    for instance, schema_name, label in (
        (benchmark, "guru-benchmark.schema.json", "benchmark"),
        (context, "context.schema.json", "context"),
        (evaluation, "evaluation.schema.json", "evaluation"),
    ):
        errors.extend(f"{label}: {error}" for error in schema_errors(instance, schema_name))
    for index, lens in enumerate(lenses):
        errors.extend(
            f"lens[{index}]: {error}"
            for error in schema_errors(lens, "expert-lens.schema.json")
        )
    if not errors:
        errors.extend(semantic_errors(evaluation, benchmark, context, lenses))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--context", type=Path, required=True)
    parser.add_argument("--lens", type=Path, action="append", default=[])
    args = parser.parse_args()

    errors = validate_contract(
        load(args.evaluation),
        load(args.benchmark),
        load(args.context),
        [load(path) for path in args.lens],
    )
    if errors:
        print("Evaluation contract validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("evaluation contract: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
