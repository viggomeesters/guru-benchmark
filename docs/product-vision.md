# Product Vision

## North star

Make world-class technical judgment reusable, source-grounded, updateable, and executable without reducing experts to role-play.

## Audience

Guru Benchmark is for developers, technical leaders, reviewers, and AI agents who need a disciplined second opinion on architecture, implementation, AI engineering, and product-engineering decisions.

## Product promise

Given a concrete question, artifact, or design, Guru Benchmark produces one context-weighted **Guru Verdict** with a scorecard, confidence, hard-gate status, disagreement clarification, an aspirational design, and ordered next moves.

## Wedge

The first useful slice is a versioned AI-engineering benchmark with a fixed founding council:

- Andrew/Andrej Karpathy
- Matt Pocock
- Peter Steinberger
- Rich Hickey
- David Heinemeier Hansson (DHH)
- Simon Willison
- Mitchell Hashimoto

Every council member participates, but relevance and evidence determine whether a lens is primary, supporting, a counterweight, or explicitly abstaining.

## Principles

1. **Evidence before persona.** A lens may summarize sourced positions, label an inference, or abstain. It may not invent views or quotations.
2. **Context before consensus.** The user's constraints and the question domain determine lens relevance.
3. **Weighted synthesis, not equal voting.** Specialist evidence carries more weight without erasing useful counterarguments.
4. **Hard failures cannot be averaged away.** Correctness, security, privacy, recoverability, and evidence gates cap the verdict.
5. **Clarify material disagreement.** The default is one answer; divergence is explained when it would change the decision.
6. **Temporal reproducibility.** A historical verdict remains reproducible against the exact benchmark and lens snapshots used.
7. **Current reality and aspiration stay separate.** Current Score and North Star Score are distinct.
8. **Action over admiration.** Output ends in ordered, testable next moves.

## Non-goals

- Impersonating living people.
- Fabricating quotations or private beliefs.
- Treating fame as evidence or expertise as universal.
- Producing an untraceable arithmetic average.
- Scraping or republishing copyrighted source corpora.
- Shipping a hosted service, model-training system, or production evaluator during repository foundation.

## Assumptions

- Public sources can support bounded, attributed lens snapshots.
- Some questions will have insufficient evidence and require abstention.
- Domain weighting can be transparent enough to review and reproduce.
- A weighted median plus explicit hard gates is more robust than a simple mean.
- Users value a compact synthesis more than seven independent essays.

## Success criteria

- A fresh clone validates all contracts with one documented local command.
- Every evaluation identifies its benchmark version, source cutoff, context profile, lens contributions, weights, confidence, hard gates, and disagreement state.
- Unsupported quotations and unlabeled inferences fail validation.
- Old snapshots remain valid after new benchmark releases.
- A new developer or agent can identify and claim the next implementation task without private context.
