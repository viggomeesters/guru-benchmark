"""Deterministic Markdown rendering for the public Guru Verdict contract."""

from __future__ import annotations

import html
import re
from decimal import Decimal
from typing import Mapping, Sequence


class RendererError(ValueError):
    """Raised when an evaluation cannot be rendered without inventing data."""


_FIRST_PERSON = re.compile(
    r"(?i)(?<![\w/])(?:i|i'm|i've|i'd|me|my|mine|myself|we|we're|we've|us|"
    r"our|ours|ourselves)(?![\w/])"
)
_GENERIC_PERSONA_IDENTITY = re.compile(
    r"(?i)(?<![\w-])(?:council(?:\s+members?)?|panel|"
    r"gurus?(?!\s+(?:score|verdict|contributions?)\b)|experts?|"
    r"lens(?:es)?|persons?|people|individuals?|authors?|speakers?|reviewers?|"
    r"advis(?:er|or)s?|celebrit(?:y|ies)|members?)(?![\w-])"
)
_HUMAN_PERSONA_PRONOUN = re.compile(
    r"(?i)(?<!\w)(?:he|she|they|them|him|her|his|hers|their|theirs)(?!\w)"
)
_QUOTATION = re.compile(
    r"[\"\u201c\u201d\u201e\u201f\u00ab\u00bb\u2039\u203a\u300c\u300d\u300e\u300f]|(?:^|\n)\s*>|"
    r"\u2018[^\u2019\n]+\u2019|'[^'\n]+'|`[^`\n]+`"
)
_TITLECASED_WORD = re.compile(r"(?<![\w-])[A-Z][a-z]+(?:[-'][A-Z]?[a-z]+)*(?![\w-])")
_SAFE_TITLECASED_WORDS = {
    # Public prose uses a deliberately small, identity-free vocabulary at sentence
    # boundaries. Any other title-cased word fails closed as a possible human name.
    "a",
    "adopt",
    "an",
    "analysis",
    "architecture",
    "context",
    "current",
    "decision",
    "design",
    "do",
    "evidence",
    "evaluation",
    "guru",
    "input",
    "injected",
    "it",
    "its",
    "no",
    "none",
    "north",
    "output",
    "pin",
    "prefer",
    "replay",
    "repository",
    "resolve",
    "result",
    "score",
    "source",
    "system",
    "test",
    "that",
    "the",
    "these",
    "this",
    "those",
    "verdict",
    "valid",
    "version",
}

_PUBLIC_ROLE_LABELS = (
    "model-guru",
    "type-guru",
    "skill-guru",
    "simplicity-guru",
    "delivery-guru",
    "security-guru",
    "automation-guru",
)

_PUBLIC_ROLE_BY_PINNED_LENS = {
    "expert.andrew-karpathy": "model-guru",
    "expert.matt-pocock": "type-guru",
    "expert.peter-steinberger": "skill-guru",
    "expert.rich-hickey": "simplicity-guru",
    "expert.dhh": "delivery-guru",
    "expert.simon-willison": "security-guru",
    "expert.mitchell-hashimoto": "automation-guru",
}


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise RendererError(f"{label} must be an object")
    return value


def _sequence(value: object, label: str) -> Sequence[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise RendererError(f"{label} must be an array")
    return value


def _required(item: Mapping[str, object], key: str, label: str) -> object:
    if key not in item:
        raise RendererError(f"{label} is missing required field {key!r}")
    return item[key]


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise RendererError(f"{label} must be a non-empty string")
    return value


def _prose(value: object, label: str) -> str:
    """Render untrusted prose inline without executable HTML or headings."""
    raw = _text(value, label)
    if _FIRST_PERSON.search(raw):
        raise RendererError(f"{label} must not contain first-person persona claims")
    normalized = html.escape(raw, quote=False)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    safe_lines = []
    for line in normalized.split("\n"):
        leading = len(line) - len(line.lstrip())
        if line[leading:].startswith("#"):
            line = line[:leading] + "&#35;" + line[leading + 1 :]
        safe_lines.append(line)
    return "<br>".join(safe_lines)


def _display(value: object) -> str:
    if value is None:
        return "Unavailable"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, Decimal):
        value = format(value, "f")
    elif isinstance(value, (int, float)):
        value = str(value)
    else:
        return str(value)
    if "." in value:
        value = value.rstrip("0").rstrip(".")
    return value


def _cell(value: object) -> str:
    """Escape a value for a single deterministic Markdown table cell."""
    return (
        html.escape(_display(value), quote=False)
        .replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("\n", "<br>")
    )


def _refs(value: object, label: str) -> str:
    values = _sequence(value, label)
    return ", ".join(_text(item, label) for item in values) if values else "None"


def _public_label(value: object, label: str) -> str:
    raw = _text(value, label)
    if raw not in _PUBLIC_ROLE_LABELS:
        raise RendererError(f"{label} must be a controlled public_label")
    return raw.replace("-", " ").title()


def _label_for_lens(public_labels: Mapping[str, str], lens_id: str, label: str) -> str:
    try:
        return public_labels[lens_id]
    except KeyError as error:
        raise RendererError(f"{label} has no public_label mapping") from error


def _table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(_cell(value) for value in row) + " |" for row in rows)
    return lines


def _reject_public_persona_claims(
    evaluation: Mapping[str, object], contributions: Sequence[object]
) -> None:
    """Keep identities structured by rejecting persona language in all public prose."""
    aliases: set[str] = set()
    normalized_aliases: set[str] = set()

    def add_lens_aliases(lens_id: str) -> None:
        aliases.add(lens_id.casefold())
        slug = lens_id.removeprefix("expert.")
        aliases.add(slug.casefold())
        aliases.add(slug.replace("-", " ").casefold())
        normalized_aliases.add(re.sub(r"[^a-z0-9]", "", slug.casefold()))
        if not slug.startswith("synthetic-"):
            aliases.update(part.casefold() for part in slug.split("-") if len(part) >= 2)

    for index, raw in enumerate(contributions):
        item = _mapping(raw, f"guru_contributions[{index}]")
        add_lens_aliases(
            _text(
                _required(item, "lens_id", f"guru_contributions[{index}]"),
                f"guru_contributions[{index}].lens_id",
            )
        )

    inputs = _mapping(_required(evaluation, "inputs", "evaluation"), "inputs")
    pinned_lenses = _sequence(_required(inputs, "lenses", "inputs"), "inputs.lenses")
    for index, raw in enumerate(pinned_lenses):
        item = _mapping(raw, f"inputs.lenses[{index}]")
        add_lens_aliases(
            _text(
                _required(item, "lens_id", f"inputs.lenses[{index}]"),
                f"inputs.lenses[{index}].lens_id",
            )
        )

    public_prose: list[tuple[str, object]] = []
    verdict = _mapping(_required(evaluation, "verdict", "evaluation"), "verdict")
    public_prose.append(("verdict.rationale", _required(verdict, "rationale", "verdict")))
    public_prose.append(("ultimate_design", _required(evaluation, "ultimate_design", "evaluation")))
    clarification = _mapping(
        _required(evaluation, "clarification", "evaluation"), "clarification"
    )
    public_prose.append(
        ("clarification.summary", _required(clarification, "summary", "clarification"))
    )
    current = _mapping(_required(evaluation, "current_score", "evaluation"), "current_score")
    for index, raw in enumerate(
        _sequence(_required(current, "observed_evidence", "current_score"), "observed_evidence")
    ):
        item = _mapping(raw, f"observed_evidence[{index}]")
        public_prose.append(
            (f"observed_evidence[{index}].statement", _required(item, "statement", "observed evidence"))
        )
    north_star = _mapping(
        _required(evaluation, "north_star_score", "evaluation"), "north_star_score"
    )
    for index, raw in enumerate(
        _sequence(
            _required(north_star, "conditional_evidence", "north_star_score"),
            "conditional_evidence",
        )
    ):
        item = _mapping(raw, f"conditional_evidence[{index}]")
        public_prose.extend(
            (
                (f"conditional_evidence[{index}].statement", _required(item, "statement", "conditional evidence")),
                (f"conditional_evidence[{index}].condition", _required(item, "condition", "conditional evidence")),
            )
        )
    for index, value in enumerate(
        _sequence(_required(north_star, "unmet_assumptions", "north_star_score"), "unmet_assumptions")
    ):
        public_prose.append((f"unmet_assumptions[{index}]", value))
    for index, raw in enumerate(contributions):
        item = _mapping(raw, f"guru_contributions[{index}]")
        public_prose.extend(
            (
                (f"guru_contributions[{index}].weight_rationale", _required(item, "weight_rationale", "guru contribution")),
                (f"guru_contributions[{index}].contribution", _required(item, "contribution", "guru contribution")),
            )
        )
    for field in ("non_actions", "next_moves"):
        if field == "non_actions":
            for index, value in enumerate(_sequence(evaluation.get(field, []), field)):
                public_prose.append((f"non_actions[{index}]", value))
        else:
            for index, raw in enumerate(_sequence(_required(evaluation, field, "evaluation"), field)):
                item = _mapping(raw, f"next_moves[{index}]")
                public_prose.extend(
                    (
                        (f"next_moves[{index}].action", _required(item, "action", "next move")),
                        (f"next_moves[{index}].expected_evidence", _required(item, "expected_evidence", "next move")),
                    )
                )

    for label, value in public_prose:
        raw = _text(value, label)
        if _FIRST_PERSON.search(raw):
            raise RendererError(f"{label} must not contain first-person persona claims")
        if _QUOTATION.search(raw):
            raise RendererError(f"{label} must not contain quotation claims")
        if re.search(r"(?i)\baccording\s+to\b", raw):
            raise RendererError(f"{label} must not contain attributed persona claims")
        if _GENERIC_PERSONA_IDENTITY.search(raw) or _HUMAN_PERSONA_PRONOUN.search(raw):
            raise RendererError(f"{label} must not turn the council into a persona claim")
        text = raw.casefold()
        compact_text = re.sub(r"[^a-z0-9]", "", text)
        if any(
            alias and re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", text)
            for alias in aliases
        ) or any(alias and alias in compact_text for alias in normalized_aliases):
            if label.startswith("guru_contributions["):
                raise RendererError(
                    f"{label} must not turn a lens identity into a persona claim"
                )
            raise RendererError(f"{label} must not contain attributed persona claims")
        unsafe_titlecased = {
            match.group(0)
            for match in _TITLECASED_WORD.finditer(raw)
            if match.group(0).casefold() not in _SAFE_TITLECASED_WORDS
        }
        if unsafe_titlecased:
            raise RendererError(f"{label} must not contain a possible named identity")


def render_guru_verdict(evaluation: Mapping[str, object]) -> str:
    """Render a schema-valid evaluation as stable, inspectable Markdown.

    The renderer deliberately does not fill absent fields or infer provenance.
    It fails closed when required public-contract data is unavailable.
    """
    evaluation = _mapping(evaluation, "evaluation")
    verdict = _mapping(_required(evaluation, "verdict", "evaluation"), "verdict")
    gates = _sequence(_required(evaluation, "hard_gates", "evaluation"), "hard_gates")
    current = _mapping(_required(evaluation, "current_score", "evaluation"), "current_score")
    north_star = _mapping(
        _required(evaluation, "north_star_score", "evaluation"), "north_star_score"
    )
    clarification = _mapping(
        _required(evaluation, "clarification", "evaluation"), "clarification"
    )
    contributions = _sequence(
        _required(evaluation, "guru_contributions", "evaluation"), "guru_contributions"
    )
    next_moves = _sequence(_required(evaluation, "next_moves", "evaluation"), "next_moves")
    inputs = _mapping(_required(evaluation, "inputs", "evaluation"), "inputs")
    _reject_public_persona_claims(evaluation, contributions)
    public_labels: dict[str, str] = {}
    for index, raw in enumerate(contributions):
        item = _mapping(raw, f"guru_contributions[{index}]")
        lens_id = _text(
            _required(item, "lens_id", f"guru_contributions[{index}]"),
            f"guru_contributions[{index}].lens_id",
        )
        public_labels[lens_id] = _public_label(
            _required(item, "public_label", f"guru_contributions[{index}]"),
            f"guru_contributions[{index}].public_label",
        )
        if item["public_label"] != _PUBLIC_ROLE_LABELS[index]:
            raise RendererError(
                f"guru_contributions[{index}].public_label does not match its pinned lens order"
            )
        pinned_label = _PUBLIC_ROLE_BY_PINNED_LENS.get(lens_id)
        if pinned_label is not None and item["public_label"] != pinned_label:
            raise RendererError(
                f"guru_contributions[{index}].public_label does not match its pinned lens id"
            )
    if len(public_labels) != len(contributions) or len(set(public_labels.values())) != len(public_labels):
        raise RendererError("guru contribution public_label values must be unique")

    status = _text(_required(evaluation, "status", "evaluation"), "status")
    decision = _text(_required(verdict, "decision", "verdict"), "verdict.decision")
    rationale = _prose(_required(verdict, "rationale", "verdict"), "verdict.rationale")
    confidence = _text(_required(verdict, "confidence", "verdict"), "verdict.confidence")

    lines = [
        "# Guru Verdict",
        "",
        f"**{decision}** — {rationale}",
        "",
        "# Guru Score",
        "",
        *_table(
            ("Measure", "Value", "Confidence"),
            (
                ("Current Score", _required(current, "overall", "current_score"), _required(current, "confidence", "current_score")),
                ("North Star Score", _required(north_star, "overall", "north_star_score"), _required(north_star, "confidence", "north_star_score")),
                ("Score dispersion", _required(evaluation, "score_dispersion", "evaluation"), "—"),
                ("Verdict", decision, confidence),
            ),
        ),
        "",
        "## Hard gates",
        "",
    ]

    gate_rows = []
    for index, raw in enumerate(gates):
        gate = _mapping(raw, f"hard_gates[{index}]")
        gate_rows.append(
            (
                _required(gate, "gate_id", f"hard_gates[{index}]"),
                _required(gate, "status", f"hard_gates[{index}]"),
                _required(gate, "effect", f"hard_gates[{index}]"),
                _refs(_required(gate, "evidence_refs", f"hard_gates[{index}]"), f"hard_gates[{index}].evidence_refs"),
            )
        )
    lines.extend(_table(("Gate", "Status", "Effect", "Evidence refs"), gate_rows))

    lines.extend(["", "## Current Score", ""])
    current_dimensions = _sequence(_required(current, "dimensions", "current_score"), "current_score.dimensions")
    lines.extend(
        _table(
            ("Dimension", "Score", "Evidence refs"),
            [
                (
                    _required(_mapping(item, f"current_score.dimensions[{index}]"), "dimension_id", f"current_score.dimensions[{index}]"),
                    _required(_mapping(item, f"current_score.dimensions[{index}]"), "score", f"current_score.dimensions[{index}]"),
                    _refs(_required(_mapping(item, f"current_score.dimensions[{index}]"), "evidence_refs", f"current_score.dimensions[{index}]"), f"current_score.dimensions[{index}].evidence_refs"),
                )
                for index, item in enumerate(current_dimensions)
            ],
        )
    )
    lines.extend(["", "Observed evidence:", ""])
    observed = _sequence(_required(current, "observed_evidence", "current_score"), "current_score.observed_evidence")
    if observed:
        for index, raw in enumerate(observed):
            item = _mapping(raw, f"current_score.observed_evidence[{index}]")
            source_refs = _refs(item.get("source_refs", []), f"current_score.observed_evidence[{index}].source_refs")
            lines.append(
                f"- `{_text(_required(item, 'id', 'observed evidence'), 'observed evidence id')}` "
                f"({_text(_required(item, 'kind', 'observed evidence'), 'observed evidence kind')}, "
                f"observed {_text(_required(item, 'observed_at', 'observed evidence'), 'observed_at')}): "
                f"{_prose(_required(item, 'statement', 'observed evidence'), 'observed evidence statement')} "
                f"Source refs: {_prose(source_refs, 'observed evidence source_refs')}."
            )
    else:
        lines.append("- None")

    lines.extend(["", "## North Star Score", ""])
    north_dimensions = _sequence(_required(north_star, "dimensions", "north_star_score"), "north_star_score.dimensions")
    lines.extend(
        _table(
            ("Dimension", "Score", "Evidence refs"),
            [
                (
                    _required(_mapping(item, f"north_star_score.dimensions[{index}]"), "dimension_id", f"north_star_score.dimensions[{index}]"),
                    _required(_mapping(item, f"north_star_score.dimensions[{index}]"), "score", f"north_star_score.dimensions[{index}]"),
                    _refs(_required(_mapping(item, f"north_star_score.dimensions[{index}]"), "evidence_refs", f"north_star_score.dimensions[{index}]"), f"north_star_score.dimensions[{index}].evidence_refs"),
                )
                for index, item in enumerate(north_dimensions)
            ],
        )
    )
    lines.extend(["", "Conditional evidence:", ""])
    conditional = _sequence(_required(north_star, "conditional_evidence", "north_star_score"), "north_star_score.conditional_evidence")
    if conditional:
        for index, raw in enumerate(conditional):
            item = _mapping(raw, f"north_star_score.conditional_evidence[{index}]")
            lines.append(
                f"- `{_text(_required(item, 'id', 'conditional evidence'), 'conditional evidence id')}`: "
                f"{_prose(_required(item, 'statement', 'conditional evidence'), 'conditional evidence statement')} "
                f"Condition: {_prose(_required(item, 'condition', 'conditional evidence'), 'conditional evidence condition')} "
                "Basis refs: "
                f"{_prose(_refs(_required(item, 'basis_refs', 'conditional evidence'), 'conditional evidence basis_refs'), 'conditional evidence basis_refs')}."
            )
    else:
        lines.append("- None")
    lines.extend(["", "Unmet assumptions:", ""])
    assumptions = _sequence(_required(north_star, "unmet_assumptions", "north_star_score"), "north_star_score.unmet_assumptions")
    lines.extend(f"- {_prose(item, 'unmet assumption')}" for item in assumptions)
    if not assumptions:
        lines.append("- None")

    lines.extend(
        [
            "",
            "# Ultimate Design",
            "",
            _prose(_required(evaluation, "ultimate_design", "evaluation"), "ultimate_design"),
            "",
            "Explicit non-actions:",
            "",
        ]
    )
    raw_non_actions = (
        _required(evaluation, "non_actions", "evaluation")
        if status == "complete"
        else evaluation.get("non_actions", [])
    )
    non_actions = _sequence(raw_non_actions, "non_actions")
    lines.extend(f"- {_prose(item, 'non_action')}" for item in non_actions)
    if not non_actions:
        lines.append("- None specified")

    lines.extend(
        [
            "",
            "# Opheldering",
            "",
            f"Required: {_display(_required(clarification, 'required', 'clarification'))}.",
            "",
            _prose(_required(clarification, "summary", "clarification"), "clarification.summary"),
            "",
            "# Guru Contributions",
            "",
        ]
    )
    contribution_rows = []
    for index, raw in enumerate(contributions):
        item = _mapping(raw, f"guru_contributions[{index}]")
        contribution_rows.append(
            (
                public_labels[_text(_required(item, "lens_id", f"guru_contributions[{index}]"), f"guru_contributions[{index}].lens_id")],
                _required(item, "role", f"guru_contributions[{index}]"),
                _required(item, "weight", f"guru_contributions[{index}]"),
                _required(item, "weight_rationale", f"guru_contributions[{index}]"),
                _required(item, "contribution", f"guru_contributions[{index}]"),
                _required(item, "confidence", f"guru_contributions[{index}]"),
                _refs(_required(item, "evidence_refs", f"guru_contributions[{index}]"), f"guru_contributions[{index}].evidence_refs"),
                _refs(_required(item, "lens_claim_refs", f"guru_contributions[{index}]"), f"guru_contributions[{index}].lens_claim_refs"),
            )
        )
    lines.extend(
        _table(
            ("Public role", "Role", "Weight", "Weight rationale", "Contribution", "Confidence", "Evidence refs", "Lens claim refs"),
            contribution_rows,
        )
    )

    lines.extend(["", "# Next Moves", ""])
    ordered_moves = []
    for index, raw in enumerate(next_moves):
        item = _mapping(raw, f"next_moves[{index}]")
        order = _required(item, "order", f"next_moves[{index}]")
        if not isinstance(order, int) or isinstance(order, bool):
            raise RendererError(f"next_moves[{index}].order must be an integer")
        ordered_moves.append((order, index, item))
    for order, _, item in sorted(ordered_moves):
        lines.append(
            f"{order}. {_prose(_required(item, 'action', 'next move'), 'next move action')} "
            f"Expected evidence: {_prose(_required(item, 'expected_evidence', 'next move'), 'next move expected_evidence')}"
        )
    if not ordered_moves:
        lines.append("None.")

    benchmark = _mapping(_required(inputs, "benchmark", "inputs"), "inputs.benchmark")
    context = _mapping(_required(inputs, "context", "inputs"), "inputs.context")
    source_cutoff = _mapping(_required(inputs, "source_cutoff", "inputs"), "inputs.source_cutoff")
    lenses = _sequence(_required(inputs, "lenses", "inputs"), "inputs.lenses")
    lines.extend(
        [
            "",
            "# Pins & Evidence",
            "",
            *_table(
                ("Artifact", "Identifier", "Version", "As of"),
                (
                    ("Benchmark", _required(benchmark, "benchmark_id", "inputs.benchmark"), _required(benchmark, "version", "inputs.benchmark"), _required(benchmark, "as_of", "inputs.benchmark")),
                    ("Context", _required(context, "context_id", "inputs.context"), _required(context, "version", "inputs.context"), _required(context, "as_of", "inputs.context")),
                    ("Source cutoff", "source-cutoff", _required(source_cutoff, "version", "inputs.source_cutoff"), _required(source_cutoff, "as_of", "inputs.source_cutoff")),
                ),
            ),
            "",
            "Public role pins:",
            "",
        ]
    )
    lines.extend(
        _table(
            ("Public role", "Version", "As of"),
            [
                (
                    _label_for_lens(
                        public_labels,
                        _text(_required(_mapping(item, f"inputs.lenses[{index}]"), "lens_id", f"inputs.lenses[{index}]"), f"inputs.lenses[{index}].lens_id"),
                        f"inputs.lenses[{index}]",
                    ),
                    _required(_mapping(item, f"inputs.lenses[{index}]"), "version", f"inputs.lenses[{index}]"),
                    _required(_mapping(item, f"inputs.lenses[{index}]"), "as_of", f"inputs.lenses[{index}]"),
                )
                for index, item in enumerate(lenses)
            ],
        )
    )
    lines.extend(
        [
            "",
            f"- Evaluation: `{_text(_required(evaluation, 'evaluation_id', 'evaluation'), 'evaluation_id')}`",
            f"- Generated at: {_text(_required(evaluation, 'generated_at', 'evaluation'), 'generated_at')}",
            f"- Schema version: {_text(_required(evaluation, 'schema_version', 'evaluation'), 'schema_version')}",
            f"- Status: {status}",
            f"- Synthetic: {_display(_required(evaluation, 'synthetic', 'evaluation'))}",
        ]
    )
    return "\n".join(lines) + "\n"


# Compact aliases for callers that name either the artifact or the operation.
render_evaluation = render_guru_verdict
render = render_guru_verdict


__all__ = ["RendererError", "render", "render_evaluation", "render_guru_verdict"]
