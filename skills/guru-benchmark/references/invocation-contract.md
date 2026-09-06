# Invocation Contract

## Natural-language entrypoints

The canonical entrypoints are:

```text
Guru Benchmark <request>
North Star critique <subject>
North Star design <subject>
North Star delta <subject>
North Star devil <subject>
```

The prefix selects the skill; the remaining text is the request. Preserve multiline context and artifact paths after the prefix.

## Structured request

Structured callers use `request.schema.json`.

Required:

- `mode`: `critique`, `design`, `delta`, or `devil`;
- `subject`: the system or decision being evaluated;
- `context`: the observable current context;
- `benchmark`: exact benchmark id and version.

Recommended:

- `artifact_paths` or public URLs;
- `product_stage`;
- `dominant_risks`;
- `constraints` and `non_goals`;
- `decision_horizon`;
- `desired_depth`;
- `allow_current_research`;
- `public_output`.

## Context normalization

Before judging, explicitly separate:

| Class | Meaning |
|---|---|
| observed | directly inspected artifact/runtime fact |
| provided | user statement not independently verified |
| pinned | benchmark or lens fact from a versioned repository artifact |
| researched | newly retrieved dated public evidence |
| assumed | necessary working assumption |
| unknown | unresolved fact that may change the verdict |

A provided statement is not automatically observed evidence. If a material claim can be inspected with available tools, inspect it rather than asking the user to prove it.

## Version behavior

- Evaluation time and evidence cutoff are different fields.
- Never modify a pinned benchmark or lens while evaluating it.
- If current research changes the likely conclusion, show the delta and recommend a future versioned lens update rather than silently rewriting the active lens.
- A missing compatible lens produces an abstention, not a guessed profile.

## Public-output boundary

When `public_output=true`:

- redact private paths, identities, credentials, proprietary data, and private user context;
- cite only public-safe evidence;
- describe omitted evidence as an evidence gap;
- never publish generated chain-of-thought or copied source corpora.
