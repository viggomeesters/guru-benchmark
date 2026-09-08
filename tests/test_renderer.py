from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from guru_benchmark import RendererError, render_guru_verdict  # noqa: E402


def evaluation_fixture():
    return json.loads(
        (ROOT / "tests/fixtures/evaluation/valid/synthetic-library-evaluation.json").read_text(
            encoding="utf-8"
        )
    )


class RendererGoldenTests(unittest.TestCase):
    def test_synthetic_evaluation_matches_complete_public_golden_output(self) -> None:
        rendered = render_guru_verdict(evaluation_fixture())
        golden = (ROOT / "tests/golden/synthetic-library-verdict.md").read_text(
            encoding="utf-8"
        )

        self.assertEqual(golden, rendered)

    def test_required_sections_are_rendered_once_and_in_contract_order(self) -> None:
        rendered = render_guru_verdict(evaluation_fixture())
        headings = [
            "# Guru Verdict",
            "# Guru Score",
            "# Ultimate Design",
            "# Opheldering",
            "# Guru Contributions",
            "# Next Moves",
            "# Pins & Evidence",
        ]

        positions = [rendered.index(heading) for heading in headings]
        self.assertEqual(positions, sorted(positions))
        for heading in headings:
            self.assertEqual(1, rendered.count(heading))

    def test_exact_provenance_and_all_council_rows_remain_visible(self) -> None:
        evaluation = evaluation_fixture()
        rendered = render_guru_verdict(evaluation)

        self.assertIn("guru-synthetic-evaluation-contract", rendered)
        self.assertIn("context.synthetic-library", rendered)
        self.assertIn("2026.09.1", rendered)
        self.assertIn("current.manifest-test", rendered)
        self.assertIn("north-star.immutable-pin", rendered)
        for contribution in evaluation["guru_contributions"]:
            row_prefix = f"| {contribution['lens_id']} | {contribution['role']} |"
            self.assertEqual(1, rendered.count(row_prefix))

    def test_current_and_north_star_scores_are_not_collapsed(self) -> None:
        rendered = render_guru_verdict(evaluation_fixture())

        self.assertIn("| Current Score | 5 | high |", rendered)
        self.assertIn("| North Star Score | 8.5 | medium |", rendered)
        self.assertIn("The synthetic replay test resolves a mutable alias", rendered)
        self.assertIn("An immutable release pin would make", rendered)


class RendererSafetyTests(unittest.TestCase):
    def test_persona_style_contribution_fails_closed(self) -> None:
        evaluation = copy.deepcopy(evaluation_fixture())
        evaluation["guru_contributions"][0]["contribution"] = (
            "I would use an immutable input."
        )

        with self.assertRaisesRegex(RendererError, "first-person persona claims"):
            render_guru_verdict(evaluation)

    def test_persona_style_weight_rationale_fails_closed(self) -> None:
        evaluation = copy.deepcopy(evaluation_fixture())
        evaluation["guru_contributions"][0]["weight_rationale"] = (
            "We give this lens the strongest weight."
        )

        with self.assertRaisesRegex(RendererError, "first-person persona claims"):
            render_guru_verdict(evaluation)

    def test_third_person_persona_attribution_fails_closed(self) -> None:
        evaluation = copy.deepcopy(evaluation_fixture())
        evaluation["guru_contributions"][0]["contribution"] = (
            "The synthetic systems builder says this design should ship."
        )

        with self.assertRaisesRegex(RendererError, "lens identity into a persona claim"):
            render_guru_verdict(evaluation)

    def test_generic_collective_identity_fails_closed(self) -> None:
        evaluation = copy.deepcopy(evaluation_fixture())
        evaluation["verdict"]["rationale"] = "The panel prefers this option."

        with self.assertRaisesRegex(RendererError, "council into a persona claim"):
            render_guru_verdict(evaluation)

    def test_arbitrary_named_human_identity_fails_closed(self) -> None:
        for claim in ("Ada endorses immutable pins.", "Evidence from Grace is unavailable."):
            with self.subTest(claim=claim):
                evaluation = copy.deepcopy(evaluation_fixture())
                evaluation["verdict"]["rationale"] = claim
                with self.assertRaisesRegex(RendererError, "possible named identity"):
                    render_guru_verdict(evaluation)

    def test_lens_identity_cannot_be_personified_with_an_unlisted_verb(self) -> None:
        for claim in (
            "The synthetic systems builder endorses this design.",
            "The synthetic systems builder suggests this design should ship.",
            "Synthetic systems builder mandates immutable inputs.",
        ):
            with self.subTest(claim=claim):
                evaluation = copy.deepcopy(evaluation_fixture())
                evaluation["guru_contributions"][0]["contribution"] = claim
                with self.assertRaisesRegex(RendererError, "lens identity into a persona claim"):
                    render_guru_verdict(evaluation)

    def test_collective_council_cannot_be_personified_with_an_unlisted_verb(self) -> None:
        claims = (
            "The council endorses this design.",
            "Council members champion this design.",
            "This design is approved by the experts.",
            "Council members decree that this design must ship.",
        )
        for claim in claims:
            with self.subTest(claim=claim):
                evaluation = copy.deepcopy(evaluation_fixture())
                evaluation["verdict"]["rationale"] = claim
                with self.assertRaisesRegex(RendererError, "council into a persona claim"):
                    render_guru_verdict(evaluation)

    def test_generic_lens_cannot_be_personified(self) -> None:
        claims = (
            "This lens endorses the design based on its beliefs.",
            "A lens favors this option.",
            "The result follows their preferences.",
            "The council is relevant to this decision.",
            "The panel is included as context.",
            "Experts are listed in the pinned inputs.",
        )
        for claim in claims:
            with self.subTest(claim=claim):
                evaluation = copy.deepcopy(evaluation_fixture())
                evaluation["guru_contributions"][0]["contribution"] = claim
                with self.assertRaisesRegex(RendererError, "council into a persona claim"):
                    render_guru_verdict(evaluation)

    def test_persona_claim_categories_fail_without_relying_on_attribution_verbs(self) -> None:
        claims = (
            ("We mandate immutable inputs.", "first-person persona claims"),
            ("Synthetic systems builder celebrates immutable inputs.", "attributed persona claims"),
            ("A lens celebrates immutable inputs.", "council into a persona claim"),
            ("The council celebrates immutable inputs.", "council into a persona claim"),
            ("A reviewer records approval of this design.", "council into a persona claim"),
            ("They record approval of this design.", "council into a persona claim"),
            ('\"Immutable inputs are best.\"', "quotation claims"),
        )
        for claim, message in claims:
            with self.subTest(claim=claim):
                evaluation = copy.deepcopy(evaluation_fixture())
                evaluation["verdict"]["rationale"] = claim
                with self.assertRaisesRegex(RendererError, message):
                    render_guru_verdict(evaluation)

    def test_less_common_persona_states_and_quote_forms_fail_closed(self) -> None:
        claims = (
            "An advisor has confidence in immutable inputs.",
            "The speaker records approval of this design.",
            "Claim:'Approved.'",
            "`Immutable inputs are best.`",
            "«Immutable pins are best.»",
        )
        for claim in claims:
            with self.subTest(claim=claim):
                evaluation = copy.deepcopy(evaluation_fixture())
                evaluation["verdict"]["rationale"] = claim
                with self.assertRaises(RendererError):
                    render_guru_verdict(evaluation)

    def test_lens_identity_matching_normalizes_hyphenated_forms(self) -> None:
        evaluation = copy.deepcopy(evaluation_fixture())
        evaluation["verdict"]["rationale"] = (
            "Synthetic-systems-builder celebrates immutable inputs."
        )

        with self.assertRaisesRegex(
            RendererError, "attributed persona claims|council into a persona claim"
        ):
            render_guru_verdict(evaluation)

    def test_pinned_lens_identity_fails_closed_without_a_contribution_row(self) -> None:
        evaluation = copy.deepcopy(evaluation_fixture())
        evaluation["inputs"]["lenses"].append(
            {
                "lens_id": "expert.synthetic-release-reviewer",
                "version": "2026.09.0",
                "as_of": "2026-09-06",
            }
        )
        evaluation["verdict"]["rationale"] = (
            "Synthetic release reviewer celebrates this design."
        )

        with self.assertRaisesRegex(
            RendererError, "attributed persona claims|council into a persona claim"
        ):
            render_guru_verdict(evaluation)

    def test_curly_and_markdown_quotation_claims_fail_closed(self) -> None:
        for claim in (
            "\u201cImmutable inputs are best.\u201d",
            "\u00abImmutable inputs are best.\u00bb",
            "\u2039Immutable inputs are best.\u203a",
            "\u300cImmutable inputs are best.\u300d",
            "'Immutable inputs are best.'",
            "'Approved.'",
            "> Immutable inputs are best.",
            "Claim:'Approved.'",
        ):
            with self.subTest(claim=claim):
                evaluation = copy.deepcopy(evaluation_fixture())
                evaluation["clarification"]["summary"] = claim
                with self.assertRaisesRegex(RendererError, "quotation claims"):
                    render_guru_verdict(evaluation)

    def test_identity_free_analytical_language_remains_renderable(self) -> None:
        for claim in (
            "The analysis is convinced immutable pins are best.",
            "The result backs this design.",
            "The verdict embraces this architecture.",
            "The output supports this recommendation.",
            "The analysis chooses immutable pins.",
            "The result recommends this design.",
            "The evaluation rejects the moving alias.",
            "The analysis asserts immutable pins are best.",
            "The result claims this design is correct.",
            "The evaluation concludes that this should ship.",
            "The evidence determines the preferred architecture.",
            "It concludes that immutable pins are best.",
            "Its evidence supports immutable pins.",
        ):
            with self.subTest(claim=claim):
                evaluation = copy.deepcopy(evaluation_fixture())
                evaluation["verdict"]["rationale"] = claim
                self.assertIn(claim, render_guru_verdict(evaluation))

    def test_hyphenated_lens_identity_fails_closed(self) -> None:
        evaluation = copy.deepcopy(evaluation_fixture())
        evaluation["verdict"]["rationale"] = (
            "Synthetic-systems-builder celebrates immutable inputs."
        )

        with self.assertRaisesRegex(RendererError, "attributed persona claims"):
            render_guru_verdict(evaluation)

    def test_real_lens_surname_cannot_be_personified(self) -> None:
        evaluation = copy.deepcopy(evaluation_fixture())
        evaluation["guru_contributions"][0]["lens_id"] = "expert.andrew-karpathy"
        evaluation["guru_contributions"][0]["contribution"] = (
            "Karpathy endorses this design."
        )

        with self.assertRaisesRegex(RendererError, "lens identity into a persona claim"):
            render_guru_verdict(evaluation)

        evaluation = copy.deepcopy(evaluation_fixture())
        evaluation["guru_contributions"][0]["lens_id"] = "expert.andrew-karpathy"
        evaluation["guru_contributions"][0]["contribution"] = "Andrew champions this design."
        with self.assertRaisesRegex(RendererError, "lens identity into a persona claim"):
            render_guru_verdict(evaluation)

    def test_persona_attribution_fails_closed_in_every_public_prose_section(self) -> None:
        prose_paths = (
            ("verdict", "rationale"),
            ("current_score", "observed_evidence", 0, "statement"),
            ("north_star_score", "conditional_evidence", 0, "statement"),
            ("north_star_score", "conditional_evidence", 0, "condition"),
            ("north_star_score", "unmet_assumptions", 0),
            ("ultimate_design",),
            ("non_actions", 0),
            ("clarification", "summary"),
            ("next_moves", 0, "action"),
            ("next_moves", 0, "expected_evidence"),
        )
        for path in prose_paths:
            with self.subTest(path=path):
                evaluation = copy.deepcopy(evaluation_fixture())
                target = evaluation
                for segment in path[:-1]:
                    target = target[segment]
                target[path[-1]] = (
                    "According to the synthetic systems builder, this is correct."
                )
                with self.assertRaisesRegex(RendererError, "attributed persona claims"):
                    render_guru_verdict(evaluation)

    def test_first_person_persona_claim_fails_closed_outside_contributions(self) -> None:
        evaluation = copy.deepcopy(evaluation_fixture())
        evaluation["verdict"]["rationale"] = (
            "I would adopt immutable pins after the compatibility test passes."
        )

        with self.assertRaisesRegex(RendererError, "first-person persona claims"):
            render_guru_verdict(evaluation)

        evaluation = copy.deepcopy(evaluation_fixture())
        evaluation["next_moves"][0]["action"] = (
            "The synthetic systems builder recommends changing the input."
        )
        with self.assertRaisesRegex(RendererError, "attributed persona claims"):
            render_guru_verdict(evaluation)

    def test_according_to_persona_attribution_fails_closed(self) -> None:
        evaluation = copy.deepcopy(evaluation_fixture())
        evaluation["guru_contributions"][0]["contribution"] = (
            "According to the synthetic systems builder, this design should ship."
        )

        with self.assertRaisesRegex(RendererError, "attributed persona claims"):
            render_guru_verdict(evaluation)

    def test_multiline_prose_cannot_inject_contract_headings(self) -> None:
        evaluation = copy.deepcopy(evaluation_fixture())
        evaluation["verdict"]["rationale"] = (
            "Valid rationale.\n\n# Guru Score\n\nInjected content."
        )

        rendered = render_guru_verdict(evaluation)

        self.assertEqual(1, rendered.count("# Guru Score"))
        self.assertIn("Valid rationale.<br><br>&#35; Guru Score", rendered)

    def test_untrusted_html_is_escaped_in_prose_and_tables(self) -> None:
        evaluation = copy.deepcopy(evaluation_fixture())
        evaluation["verdict"]["rationale"] = (
            "Valid rationale with <script>alert(unsafe)</script>."
        )
        evaluation["guru_contributions"][0]["contribution"] = (
            "Prefer an <img src=x onerror=alert(unsafe)> immutable input."
        )

        rendered = render_guru_verdict(evaluation)

        self.assertNotIn("<script>", rendered)
        self.assertNotIn("<img", rendered)
        self.assertIn("&lt;script&gt;", rendered)
        self.assertIn("&lt;img src=x onerror=alert(unsafe)&gt;", rendered)

    def test_untrusted_evidence_refs_cannot_inject_html_or_headings(self) -> None:
        evaluation = copy.deepcopy(evaluation_fixture())
        evaluation["current_score"]["observed_evidence"][0]["source_refs"] = [
            "source.safe\n# Guru Score<script>alert('unsafe')</script>"
        ]
        evaluation["north_star_score"]["conditional_evidence"][0]["basis_refs"] = [
            "current.safe\n# Guru Verdict<img src=x onerror=alert('unsafe')>"
        ]

        rendered = render_guru_verdict(evaluation)

        self.assertEqual(1, rendered.count("# Guru Score"))
        self.assertEqual(1, rendered.count("# Guru Verdict"))
        self.assertNotIn("<script>", rendered)
        self.assertNotIn("<img", rendered)

    def test_missing_provenance_is_not_silently_invented(self) -> None:
        evaluation = copy.deepcopy(evaluation_fixture())
        del evaluation["inputs"]["benchmark"]["version"]

        with self.assertRaisesRegex(RendererError, "missing required field 'version'"):
            render_guru_verdict(evaluation)

    def test_version_pins_are_rendered_as_exact_strings(self) -> None:
        evaluation = copy.deepcopy(evaluation_fixture())
        evaluation["inputs"]["benchmark"]["version"] = "2026.10"

        rendered = render_guru_verdict(evaluation)

        self.assertIn("| Benchmark | guru-synthetic-evaluation-contract | 2026.10 |", rendered)

    def test_complete_evaluation_without_non_actions_fails_closed(self) -> None:
        evaluation = copy.deepcopy(evaluation_fixture())
        del evaluation["non_actions"]

        with self.assertRaisesRegex(RendererError, "missing required field 'non_actions'"):
            render_guru_verdict(evaluation)

    def test_renderer_is_available_from_the_package(self) -> None:
        from guru_benchmark import render, render_evaluation

        self.assertIs(render, render_guru_verdict)
        self.assertIs(render_evaluation, render_guru_verdict)


if __name__ == "__main__":
    unittest.main()
