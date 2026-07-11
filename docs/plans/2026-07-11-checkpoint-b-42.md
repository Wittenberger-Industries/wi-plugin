---
type: Report
title: "Checkpoint B — real-run A/B for #42 (wi 1.7.2 vs 1.8.0): PASS"
description: "Two real /wi:dev --auto runs of the same feature idea on a private repo, same fork commit, same model, ~equal loaded input — the v1.8.0 (compact-reasoning) run generated ~56% fewer output tokens at equal-or-better implementation quality. Full evidence retained privately by the owner."
timestamp: 2026-07-11
tags: [testing, real-run, context-budget, tokens, checkpoint-b]
---

# Checkpoint B — real-run A/B for #42 (PASS)

**Method.** Two **real** (non-dry-run) `/wi:dev --auto` runs of the same feature idea on a private
production repo, launched from the same fork commit with the same `.wi/` config and the same
orchestrator model (100% of assistant turns in both runs). Only the plugin bytes differed:
**baseline-a = wi 1.7.2** (main@76b62e4) vs **baseline-b = wi 1.8.0** (prd-42@78e12db). The completed
baseline-a branch was hidden from b's repo during the run, so b derived its design independently.
Both transcripts plus every sidecar subagent transcript were frozen and analyzed with the same stdlib
pass (assistant-turn `usage` sums); the in-run `tokens.md` ledgers served as the ship-time cross-check.
Fresh input was ~equal (within 1%) — the loaded procedures weigh the same, so every delta below is
**generated** tokens, #42's target stream.

## Results (relative deltas, baseline-a → baseline-b)

| metric | Δ |
|---|---|
| Orchestrator output tokens (generated) | **−58%** |
| Orchestrator output per assistant turn | **−39%** (decomposition-independent) |
| Total output tokens (orchestrator + subagents) | **−56%** |
| Subagent tokens (per-dispatch exact, ledger) | −41% |
| Σ subagent compute wall-clock | −57% |
| Total cache-read | −50% |
| Estimated run cost (list prices) | **−54%** |

**Like-for-like dispatch slices** (same job, same charter, same model): each of the three researchers
~−30%, plan-mode checker −32%, result-mode checker −29%, the e2e task-runner −53%.

## Quality (the gate's real question)

- Both runs: design gate passed with a plan-mode checker round; ship verification gate fully green
  (typecheck / lint / format / build / tests); result-mode checker **0 BLOCKER** with every acceptance
  criterion confirmed delivered and wired; identical dossier manifests; ADRs share the same core
  decision, independently derived.
- **Post-hoc independent code review** (three parallel reviewers: one per branch against its own spec,
  one head-to-head on the shared core) graded **both implementations "excellent"** — and found the
  v1.8.0 run **equal-or-better on every shared area**, including the security-critical path, where it
  independently chose the more fail-safe design. The token saving did not come out of quality.
- Known run-shape variance (task decomposition granularity, test volume tracking it) is of the same
  class the Pile-1 comparison observed with zero plugin delta; the per-turn and like-for-like slices
  above carry the verdict independently of shape.

## Verdict

**PASS.** #42's success criteria are met on a real run: a large measured drop in generated output
tokens at ~equal loaded input, with green gates, 0-BLOCKER checker passes, and no depth regression on
the carved-out hard steps (research recommendations, checker findings, plan coverage) — confirmed by
an independent code-level review of both implementations. PR D (#51) clears its merge gate.

Raw transcripts, per-run facts, absolute figures, and the unredacted comparison are retained privately
by the owner (outside this repository).
