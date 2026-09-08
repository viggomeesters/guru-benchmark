import copy
import json
import unittest
from pathlib import Path
import sys

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
sys.path.insert(0, str(ROOT / "scripts"))

from evaluation_contract import semantic_errors, validate_contract  # noqa: E402


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def context_fixture():
    return load(ROOT / "tests/fixtures/context/valid/synthetic-library-context.json")


def evaluation_fixture():
    return load(ROOT / "tests/fixtures/evaluation/valid/synthetic-library-evaluation.json")


def benchmark_fixture():
    return load(ROOT / "tests/fixtures/benchmark/synthetic-evaluation-contract.json")


def validator(schema_name: str):
    registry = Registry()
    for path in SCHEMAS.glob("*.schema.json"):
        schema = load(path)
        if "$id" in schema:
            registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    schema = load(SCHEMAS / schema_name)
    return Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())


def contract_errors(evaluation):
    return validate_contract(
        evaluation,
        benchmark_fixture(),
        context_fixture(),
        [load(ROOT / "lenses/fixtures/valid/synthetic-systems-builder.json")],
    )


class EvaluationContractTests(unittest.TestCase):
    def test_valid_synthetic_context_and_evaluation_pass(self):
        context = context_fixture()
        evaluation = evaluation_fixture()

        self.assertEqual([], list(validator("context.schema.json").iter_errors(context)))
        self.assertEqual([], list(validator("guru-benchmark.schema.json").iter_errors(benchmark_fixture())))
        self.assertEqual([], list(validator("evaluation.schema.json").iter_errors(evaluation)))
        self.assertEqual([], contract_errors(evaluation))
        self.assertTrue(context["synthetic"])
        self.assertTrue(evaluation["synthetic"])

    def test_every_reproducibility_pin_requires_an_exact_version(self):
        original = evaluation_fixture()
        locations = [
            ("benchmark", None, "version"),
            ("lenses", 0, "version"),
            ("context", None, "version"),
            ("source_cutoff", None, "version"),
        ]

        for group, index, field in locations:
            with self.subTest(pin=group):
                evaluation = copy.deepcopy(original)
                pin = evaluation["inputs"][group]
                if index is not None:
                    pin = pin[index]
                del pin[field]
                messages = " ".join(error.message for error in validator("evaluation.schema.json").iter_errors(evaluation))
                self.assertIn(field, messages)

    def test_moving_latest_aliases_are_rejected(self):
        original = evaluation_fixture()
        mutations = [
            (original["inputs"]["benchmark"], "version"),
            (original["inputs"]["lenses"][0], "version"),
            (original["inputs"]["context"], "version"),
            (original["inputs"]["source_cutoff"], "version"),
        ]

        for target, field in mutations:
            with self.subTest(field=field):
                evaluation = copy.deepcopy(original)
                if target is original["inputs"]["benchmark"]:
                    evaluation["inputs"]["benchmark"][field] = "latest"
                elif target is original["inputs"]["lenses"][0]:
                    evaluation["inputs"]["lenses"][0][field] = "latest"
                elif target is original["inputs"]["context"]:
                    evaluation["inputs"]["context"][field] = "latest"
                else:
                    evaluation["inputs"]["source_cutoff"][field] = "latest"
                errors = list(validator("evaluation.schema.json").iter_errors(evaluation))
                self.assertTrue(errors)

    def test_current_score_accepts_only_observed_evidence(self):
        evaluation = evaluation_fixture()
        evaluation["current_score"]["conditional_evidence"] = evaluation["north_star_score"]["conditional_evidence"]
        del evaluation["current_score"]["observed_evidence"]

        messages = " ".join(error.message for error in validator("evaluation.schema.json").iter_errors(evaluation))
        self.assertIn("observed_evidence", messages)
        self.assertIn("conditional_evidence", messages)

    def test_current_dimensions_reject_north_star_evidence_references(self):
        evaluation = evaluation_fixture()
        evaluation["current_score"]["dimensions"][0]["evidence_refs"] = ["north-star.immutable-pin"]

        errors = list(validator("evaluation.schema.json").iter_errors(evaluation))

        self.assertTrue(errors)

    def test_north_star_score_requires_conditional_evidence_and_unmet_assumptions(self):
        evaluation = evaluation_fixture()
        evaluation["north_star_score"]["observed_evidence"] = evaluation["current_score"]["observed_evidence"]
        del evaluation["north_star_score"]["conditional_evidence"]
        del evaluation["north_star_score"]["unmet_assumptions"]

        messages = " ".join(error.message for error in validator("evaluation.schema.json").iter_errors(evaluation))
        self.assertIn("conditional_evidence", messages)
        self.assertIn("unmet_assumptions", messages)
        self.assertIn("observed_evidence", messages)

    def test_north_star_dimensions_reject_current_evidence_references(self):
        evaluation = evaluation_fixture()
        evaluation["north_star_score"]["dimensions"][0]["evidence_refs"] = ["current.manifest-test"]

        errors = list(validator("evaluation.schema.json").iter_errors(evaluation))

        self.assertTrue(errors)

    def test_fixture_pins_the_exact_context_snapshot_and_uses_an_earlier_source_cutoff(self):
        context = context_fixture()
        evaluation = evaluation_fixture()

        self.assertEqual(
            {key: context[key] for key in ("context_id", "version", "as_of")},
            evaluation["inputs"]["context"],
        )
        self.assertLess(
            evaluation["inputs"]["source_cutoff"]["as_of"],
            evaluation["generated_at"][:10],
        )

    def test_fixture_pins_exact_benchmark_and_lens_snapshots(self):
        benchmark = benchmark_fixture()
        lens = load(ROOT / "lenses/fixtures/valid/synthetic-systems-builder.json")
        evaluation = evaluation_fixture()

        self.assertEqual(
            {key: benchmark[key] for key in ("benchmark_id", "version", "as_of")},
            evaluation["inputs"]["benchmark"],
        )
        self.assertEqual(
            [{key: lens[key] for key in ("lens_id", "version", "as_of")}],
            evaluation["inputs"]["lenses"],
        )
        self.assertLessEqual(
            lens["as_of"],
            evaluation["inputs"]["source_cutoff"]["as_of"],
        )

    def test_failed_or_unknown_hard_gate_cannot_fail_open(self):
        for status in ("fail", "unknown"):
            with self.subTest(status=status):
                evaluation = evaluation_fixture()
                evaluation["hard_gates"][0].update(status=status, effect="none")
                evaluation["verdict"]["decision"] = "go"
                self.assertTrue(list(validator("evaluation.schema.json").iter_errors(evaluation)))

    def test_hard_gates_cannot_use_conditional_north_star_evidence(self):
        evaluation = evaluation_fixture()
        evaluation["hard_gates"][0]["evidence_refs"] = ["north-star.immutable-pin"]

        self.assertIn("hard-gate evidence", " ".join(contract_errors(evaluation)))

    def test_current_evidence_cannot_postdate_generation_or_source_cutoff(self):
        for observed_at in ("2026-09-07T11:00:00Z", "2026-09-08T00:00:00Z"):
            with self.subTest(observed_at=observed_at):
                evaluation = evaluation_fixture()
                evaluation["current_score"]["observed_evidence"][0]["observed_at"] = observed_at

                self.assertIn("current evidence", " ".join(contract_errors(evaluation)))

    def test_supplied_lens_claims_must_resolve_source_references(self):
        lens = load(ROOT / "lenses/fixtures/valid/synthetic-systems-builder.json")
        lens["principles"][0]["source_refs"] = ["source.does-not-exist"]

        errors = validate_contract(
            evaluation_fixture(),
            benchmark_fixture(),
            context_fixture(),
            [lens],
        )

        self.assertIn("lens claim source reference", " ".join(errors))

    def test_pinned_lens_sources_cannot_postdate_source_cutoff(self):
        for field in ("published_at", "retrieved_at"):
            with self.subTest(field=field):
                lens = load(ROOT / "lenses/fixtures/valid/synthetic-systems-builder.json")
                lens["source_references"][0][field] = "2099-01-01"

                errors = validate_contract(
                    evaluation_fixture(),
                    benchmark_fixture(),
                    context_fixture(),
                    [lens],
                )

                self.assertIn(f"source {field} is later than the source cutoff", " ".join(errors))

    def test_pinned_lens_sources_cannot_postdate_lens_snapshot(self):
        for field in ("published_at", "retrieved_at"):
            with self.subTest(field=field):
                lens = load(ROOT / "lenses/fixtures/valid/synthetic-systems-builder.json")
                lens["source_references"][0][field] = "2026-09-07"
                evaluation = evaluation_fixture()
                evaluation["inputs"]["source_cutoff"]["as_of"] = "2026-09-07"

                errors = validate_contract(
                    evaluation,
                    benchmark_fixture(),
                    context_fixture(),
                    [lens],
                )

                self.assertIn(f"source {field} is later than the lens snapshot", " ".join(errors))

    def test_public_source_evidence_must_resolve_to_a_pinned_lens_source(self):
        evaluation = evaluation_fixture()
        evidence = evaluation["current_score"]["observed_evidence"][0]
        evidence["kind"] = "public_source"
        evidence["source_refs"] = ["source.does-not-exist"]

        self.assertIn("dangling public-source evidence reference", " ".join(contract_errors(evaluation)))

    def test_conflicting_source_ids_across_pinned_lenses_are_rejected(self):
        evaluation = evaluation_fixture()
        benchmark = benchmark_fixture()
        first_lens = load(ROOT / "lenses/fixtures/valid/synthetic-systems-builder.json")
        second_lens = copy.deepcopy(first_lens)
        second_lens["lens_id"] = "expert.synthetic-second-builder"
        second_lens["expert"]["id"] = "synthetic-second-builder"
        second_lens["expert"]["display_name"] = "Synthetic Second Builder"
        second_lens["source_references"][0]["url"] = (
            "https://example.invalid/guru-benchmark/conflicting-design-notes"
        )

        evaluation["inputs"]["lenses"].append(
            {key: second_lens[key] for key in ("lens_id", "version", "as_of")}
        )
        benchmark["council"][1] = "synthetic-second-builder"
        evaluation["guru_contributions"][0]["weight"] = 0.75
        evaluation["guru_contributions"][1] = {
            "lens_id": "expert.synthetic-second-builder",
            "public_label": "type-guru",
            "role": "supporting",
            "weight": 0.25,
            "weight_rationale": "The second lens adds relevant corroborating contract evidence.",
            "contribution": "Prefer an explicit, replayable contract boundary.",
            "confidence": "medium",
            "evidence_refs": ["north-star.immutable-pin"],
            "lens_claim_refs": ["contract-first"],
        }

        errors = validate_contract(
            evaluation,
            benchmark,
            context_fixture(),
            [first_lens, second_lens],
        )

        self.assertIn("conflicting pinned lens source identifier", " ".join(errors))

    def test_pinned_lens_identity_status_and_validity_are_enforced(self):
        original = load(ROOT / "lenses/fixtures/valid/synthetic-systems-builder.json")

        mismatched = copy.deepcopy(original)
        mismatched["expert"]["id"] = "different-person"
        errors = validate_contract(evaluation_fixture(), benchmark_fixture(), context_fixture(), [mismatched])
        self.assertIn("lens identity", " ".join(errors))

        draft = copy.deepcopy(original)
        draft["status"] = "draft"
        errors = validate_contract(evaluation_fixture(), benchmark_fixture(), context_fixture(), [draft])
        self.assertIn("not active", " ".join(errors))

        expired = copy.deepcopy(original)
        expired["valid_until"] = "2026-09-06"
        evaluation = evaluation_fixture()
        evaluation["generated_at"] = "2026-09-07T12:00:00Z"
        errors = validate_contract(evaluation, benchmark_fixture(), context_fixture(), [expired])
        self.assertIn("expired", " ".join(errors))

    def test_non_abstaining_contribution_requires_resolved_lens_claim(self):
        evaluation = evaluation_fixture()
        contribution = evaluation["guru_contributions"][0]
        del contribution["lens_claim_refs"]
        messages = " ".join(
            error.message for error in validator("evaluation.schema.json").iter_errors(evaluation)
        )
        self.assertIn("lens_claim_refs", messages)

        evaluation = evaluation_fixture()
        evaluation["guru_contributions"][0]["lens_claim_refs"] = ["fabricated-claim"]
        self.assertIn("dangling lens claim reference", " ".join(contract_errors(evaluation)))

    def test_abstention_cannot_claim_lens_provenance(self):
        evaluation = evaluation_fixture()
        evaluation["guru_contributions"][1]["lens_claim_refs"] = ["contract-first"]

        self.assertTrue(list(validator("evaluation.schema.json").iter_errors(evaluation)))

    def test_contribution_weights_require_rationale_and_normalize(self):
        missing_rationale = evaluation_fixture()
        del missing_rationale["guru_contributions"][0]["weight_rationale"]
        messages = " ".join(
            error.message
            for error in validator("evaluation.schema.json").iter_errors(missing_rationale)
        )
        self.assertIn("weight_rationale", messages)

        unnormalized = evaluation_fixture()
        unnormalized["guru_contributions"][0]["weight"] = 0.2
        self.assertIn("weights must sum to 1.0", " ".join(contract_errors(unnormalized)))

        all_abstain = evaluation_fixture()
        all_abstain["guru_contributions"][0].update(
            role="abstain",
            weight=0,
            weight_rationale="The available evidence is insufficient for a defensible weight.",
            evidence_refs=[],
            lens_claim_refs=[],
        )
        self.assertIn(
            "requires at least one non-abstaining",
            " ".join(contract_errors(all_abstain)),
        )

    def test_dangling_evidence_references_are_rejected(self):
        mutations = [
            ("current_score", "dimensions"),
            ("north_star_score", "dimensions"),
            ("hard_gates", None),
            ("guru_contributions", None),
        ]
        for section, child in mutations:
            with self.subTest(section=section):
                evaluation = evaluation_fixture()
                target = evaluation[section]
                if child:
                    target = target[child]
                target[0]["evidence_refs"] = ["current.does-not-exist"]
                self.assertTrue(contract_errors(evaluation))

        evaluation = evaluation_fixture()
        evaluation["north_star_score"]["conditional_evidence"][0]["basis_refs"] = ["current.does-not-exist"]
        self.assertIn("basis reference", " ".join(contract_errors(evaluation)))

    def test_duplicate_lens_ids_and_future_source_cutoffs_are_rejected(self):
        duplicate = evaluation_fixture()
        duplicate["inputs"]["lenses"].append(copy.deepcopy(duplicate["inputs"]["lenses"][0]))
        self.assertTrue(list(validator("evaluation.schema.json").iter_errors(duplicate)))
        self.assertTrue(contract_errors(duplicate))

        future = evaluation_fixture()
        future["inputs"]["source_cutoff"]["as_of"] = "2026-09-08"
        self.assertIn("source cutoff", " ".join(contract_errors(future)))

    def test_every_pinned_benchmark_member_has_exactly_one_contribution(self):
        evaluation = evaluation_fixture()
        evaluation["guru_contributions"].pop()
        self.assertIn("pinned council", " ".join(contract_errors(evaluation)))

    def test_public_role_labels_are_required_controlled_and_unique(self):
        missing = evaluation_fixture()
        del missing["guru_contributions"][0]["public_label"]
        self.assertIn("public_label", " ".join(contract_errors(missing)))

        uncontrolled = evaluation_fixture()
        uncontrolled["guru_contributions"][0]["public_label"] = "andrew-karpathy"
        self.assertIn("public_label", " ".join(contract_errors(uncontrolled)))

        duplicate = evaluation_fixture()
        duplicate["guru_contributions"][1]["public_label"] = duplicate["guru_contributions"][0]["public_label"]
        self.assertIn("public_label", " ".join(contract_errors(duplicate)))

        permuted = evaluation_fixture()
        permuted["guru_contributions"][0]["public_label"], permuted["guru_contributions"][1]["public_label"] = (
            permuted["guru_contributions"][1]["public_label"],
            permuted["guru_contributions"][0]["public_label"],
        )
        self.assertIn("public_label", " ".join(contract_errors(permuted)))

    def test_cross_document_pins_must_match_supplied_snapshots(self):
        mutations = [
            ("benchmark", "version", "2026.08"),
            ("context", "version", "2026.09.2"),
            ("lenses", "version", "2026.09.1"),
        ]
        for group, field, value in mutations:
            with self.subTest(pin=group):
                evaluation = evaluation_fixture()
                target = evaluation["inputs"][group]
                if group == "lenses":
                    target = target[0]
                target[field] = value
                self.assertIn("does not exactly match", " ".join(contract_errors(evaluation)))

    def test_shipped_validator_rejects_held_go_mismatch(self):
        evaluation = evaluation_fixture()
        evaluation["status"] = "held"
        evaluation["verdict"]["decision"] = "go"

        self.assertTrue(contract_errors(evaluation))

    def test_scores_and_gates_must_match_pinned_benchmark(self):
        for section in ("current_score", "north_star_score"):
            with self.subTest(section=section):
                evaluation = evaluation_fixture()
                evaluation[section]["dimensions"][0]["dimension_id"] = "different-dimension"
                self.assertIn("pinned benchmark", " ".join(contract_errors(evaluation)))

        evaluation = evaluation_fixture()
        evaluation["hard_gates"][0]["gate_id"] = "different-gate"
        self.assertIn("hard gates", " ".join(contract_errors(evaluation)))

    def test_confidential_context_cannot_be_publishable(self):
        context = context_fixture()
        context["privacy"] = {"classification": "confidential", "publishable": True}
        self.assertTrue(list(validator("context.schema.json").iter_errors(context)))

    def test_synthetic_evaluation_rejects_non_synthetic_or_private_inputs(self):
        context = context_fixture()
        context["synthetic"] = False
        context["privacy"] = {"classification": "confidential", "publishable": False}
        errors = validate_contract(
            evaluation_fixture(),
            benchmark_fixture(),
            context,
            [load(ROOT / "lenses/fixtures/valid/synthetic-systems-builder.json")],
        )
        self.assertIn("requires a synthetic context", " ".join(errors))
        self.assertIn("requires a public, publishable context", " ".join(errors))

        lens = load(ROOT / "lenses/fixtures/valid/synthetic-systems-builder.json")
        lens["expert"]["synthetic"] = False
        errors = validate_contract(
            evaluation_fixture(),
            benchmark_fixture(),
            context_fixture(),
            [lens],
        )
        self.assertIn("requires synthetic pinned lenses", " ".join(errors))

    def test_non_synthetic_evaluation_rejects_synthetic_inputs(self):
        evaluation = evaluation_fixture()
        evaluation["synthetic"] = False

        errors = contract_errors(evaluation)

        self.assertIn("cannot use a synthetic context", " ".join(errors))
        self.assertIn("cannot use synthetic pinned lenses", " ".join(errors))

    def test_complete_evaluation_requires_explicit_non_actions(self):
        evaluation = evaluation_fixture()
        del evaluation["non_actions"]
        messages = " ".join(
            error.message for error in validator("evaluation.schema.json").iter_errors(evaluation)
        )
        self.assertIn("non_actions", messages)

        evaluation = evaluation_fixture()
        evaluation["non_actions"] = []
        self.assertTrue(list(validator("evaluation.schema.json").iter_errors(evaluation)))

    def test_held_evaluation_can_abstain_from_unsupported_scores(self):
        evaluation = evaluation_fixture()
        evaluation["status"] = "held"
        evaluation["verdict"]["decision"] = "hold"
        evaluation["current_score"].update(overall=None, dimensions=[], observed_evidence=[])
        evaluation["north_star_score"].update(
            overall=None,
            dimensions=[],
            conditional_evidence=[],
            unmet_assumptions=[],
        )
        evaluation["score_dispersion"] = None
        evaluation["hard_gates"][0].update(status="unknown", effect="hold", evidence_refs=[])
        evaluation["guru_contributions"][0] = {
            "lens_id": "expert.synthetic-systems-builder",
            "public_label": "model-guru",
            "role": "abstain",
            "weight": 0,
            "weight_rationale": "The available evidence is insufficient for a defensible weight.",
            "contribution": "Evidence was insufficient to score responsibly.",
            "confidence": "low",
            "evidence_refs": [],
            "lens_claim_refs": [],
        }

        self.assertEqual([], contract_errors(evaluation))

    def test_complete_evaluation_still_requires_scores_and_evidence(self):
        evaluation = evaluation_fixture()
        evaluation["current_score"].update(overall=None, dimensions=[], observed_evidence=[])
        evaluation["north_star_score"].update(
            overall=None,
            dimensions=[],
            conditional_evidence=[],
            unmet_assumptions=[],
        )
        evaluation["score_dispersion"] = None

        messages = " ".join(
            error.message for error in validator("evaluation.schema.json").iter_errors(evaluation)
        )
        self.assertIn("is not of type 'number'", messages)
        self.assertIn("should be non-empty", messages)


if __name__ == "__main__":
    unittest.main()
