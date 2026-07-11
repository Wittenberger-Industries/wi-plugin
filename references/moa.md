---
type: Reference
title: "Mixture of Agents: optional proposer/aggregator layer at wi's judgment points"
description: "An optional, default-off Mixture-of-Agents layer configured in .wi/models.md: N proposer agents answer the same judgment independently, an optional second layer refines against all round-1 proposals, and one aggregator synthesizes the single answer, applied at wi's two judgment points, the research approach decision and the checker's result-mode review at ship."
timestamp: 2026-07-04
tags: [moa, models, reference]
---

# Mixture of Agents: optional proposer/aggregator layer at wi's judgment points

wi normally forms each judgment once. **Mixture of Agents (MoA)** deepens the two judgments that decide a
feature's fate: **N proposer agents answer the SAME query independently**, an optional **second layer**
lets each proposer refine after reading all round-1 proposals, and **one aggregator agent** synthesizes
the single final answer. It applies at exactly two points, **research** (the approach decision behind the
ADR) and **review** (the checker's result-mode pass at ship), and nowhere else: MoA never replaces wi's
phases, it deepens the two decisions.

**Off by default.** Both presets (smart AND simple) write `points: none`; a `.wi/models.md` that lacks the
section entirely is treated as `points: none`, no migration needed. MoA is enabled only by hand-editing
`.wi/models.md` and setting `points`. The pricing rule carries over: no preset or default ever writes
`fable` here; a hand-written row may name any tier.

## The config section (in `.wi/models.md`)

```markdown
## Mixture of Agents
| Key | Value |
|-----|-------|
| points | <none \| research \| review \| research+review> |
| proposers | <comma list of tiers, e.g. opus, sonnet, sonnet> |
| layers | <1 \| 2> |
| aggregator | <fable\|opus\|sonnet\|haiku\|inherit> |
```

- `points`: which judgment points run MoA; `research+review` enables both.
- `proposers`: count = N (2–5). Proposer diversity comes from independent contexts and (optionally)
  differing tiers.
- `layers`: 1 or 2 (layer semantics below).
- `aggregator`: the tier of the single aggregator dispatch.

## Dispatch markers

The role rides the Agent dispatch prompt:

- Proposer: `MoA role: proposer <i>/<N>`; each proposer is told it is one of N independent proposers; it
  must commit to ONE answer; it must not hedge across options.
- Aggregator: `MoA role: aggregator` (+ the proposer outputs).
- No marker → non-MoA behavior, unchanged.

## Layer semantics (both points)

Layer 1: N proposers answer independently, in parallel, same turn. If `layers: 2`: a second parallel
round: each proposer receives ALL round-1 proposals (research: the proposal files; review: the union of
round-1 findings) and returns a refinement (may change position; must say why). The aggregator always runs
last, exactly once, at the `aggregator` tier; proposers run at their listed tiers (each resolved like any
dispatch: the literal tier, or `inherit`).

## Research point: who writes what

Proposer i writes `.wi/features/<slug>/research/proposal-<i>.md` (layer 2: `proposal-<i>-r2.md`); the
aggregator writes `research/proposal-synthesis.md` and returns the recommendation. All ephemeral
(`research/` already is). The ORCHESTRATOR (research skill) still adopts the recommendation, writes the
ADR, and owns Phase flips: the aggregator recommends, it does not decide.

Log line (progress.md): `approach via MoA (<N> proposers, <L> layers, aggregator <tier>)`

## Review point: who writes what

Proposer checkers RETURN findings only: they NEVER write `verification.md`; the aggregator checker alone
writes `verification.md` (both passes' sections, one verdict marker). wi has exactly one review agent
CONTRACT, `wi-code-checker`; MoA runs multiple INSTANCES of it, and only the aggregator instance writes
`verification.md`. Do not "fix" this by splitting the review into a second agent type.

Log line (progress.md): `review via MoA (<N> proposers, <L> layers, aggregator <tier>)`, appended to the
existing review log label (e.g. `review via wi-code-checker + superpowers:requesting-code-review[inline] + MoA (3 proposers, 1 layer, aggregator opus)`).

## Token ledger

Every proposer and aggregator dispatch appends its own `tokens.md` row on completion, including the
row's `Duration` cell, same convention as researchers/checkers today.

## Cost

Each enabled point costs ~N×(L)+1 dispatches instead of the single dispatch (or, at research, instead of
the orchestrator reconciling alone). That multiplier is the whole trade (deeper judgment for more
dispatches) and it is why `points: none` is the default.

## Scope

`dev` features get both points; `rpa` runs mirror the **review** point only.

Tiered model routing (single-agent dispatch tiers) is the separate
`${CLAUDE_PLUGIN_ROOT}/references/models.md`; the two compose, but neither requires the other.
