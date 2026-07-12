---
type: Roadmap
title: "wi roadmap: the live queue of open issues"
description: Tracking surface for all open issues; order, version targets, sequencing constraints, and the standing per-PR guardrails. Supersedes the 2026-07 triage doc as the thing that gets updated; that doc is frozen as the sweep's history.
timestamp: 2026-07-11
tags: [roadmap, triage, plan]
---

# wi roadmap (live)

**This file is the tracking surface for open work: update it here, not in the triage doc.**
History and rationale of the 2026-07 sweep live in `docs/plans/2026-07-10-issue-triage-35-42.md`
(frozen; PRs A–D shipped #35–#40, #42, #47, #49 as v1.6.0 → v1.8.0, Checkpoints A and B passed;
B's record: `docs/plans/2026-07-11-checkpoint-b-42.md`). Every issue below is spec-grade (acceptance
criteria + file lists in the body); the per-issue implementation plan is written from that AC at
pick-up, into `docs/plans/`, and rides in the PR.

## Queue (in order)

| Slot | Issue | What | Version | Effort · Risk | Why this order |
|---|---|---|---|---|---|
| next | **#53** ledger split labels | `token_report.py` split rows labeled from `agent-<id>.meta.json` `description` (+ the description==Source convention) instead of 48-char prompt prefixes | minor (artifact format) | S · Low | After #48 (shared `_ledger.py`/`check_tokens.py`/tests surface); small |
| then | **#52** dispatch-time skill pointer | Generalized capability-tag → registry → resolved SKILL.md path in the dispatch; frontend first; fixes the unreachable `[frontend]` delegation (charters have no Skill tool) | minor (runner behavior) | S–M · Low–Medium | After #41 (shipped): touches `build/SKILL.md` + a charter (hotspots, strictly serial). Owner decision 2026-07-11: pointer, **not** a Skill-bearing variant agent; Checkpoint B's baseline-b runners empirically validated the read-the-skill-file mechanism |
| parallel, gated | **#43** Grok Build platform | Fourth platform adapter (`references/grok-tools.md`, keep-alive `/goal`-family branch, AGENTS.md row, bootstrap, models.md xAI entry) | minor | M · Low–Medium | Independent of the sweep; **gated on Grok Build beta access**: every runtime claim verified on a real session. The planned **release/1.8.0 → Grok "baseline-c" comparison** doubles as its verification run (evidence method: the Checkpoint B harness) |
| queued, before #34 | **#65** centralize MoA/routing mechanics | Thin the always-loaded skill bodies (`research`/`ship`/`build`/`dev`/`rpa` SKILL.md) to a trigger + pointer; the MoA proposer/aggregator/`layers` + routing resolve-once mechanics live only in `references/moa.md` + `references/models.md` (loaded on demand, so the MoA-off common case stops paying for them every turn) | patch (pure relocation) | S–M · Low | **Land before #34**: shrinks #34 and keeps its new cross-vendor mechanics in `moa.md` only, not reinlined into the skills. Touches the serial hotspots; same family as #40 (dedup restated rules) |
| ⏸ postponed | **#34** cross-vendor MoA proposers | Let the MoA council use OpenAI / DeepSeek / Grok / Gemini | - | - | Postponed (owner, 2026-07-10). Revisit after the sweep: #35 already landed (simplifies it), #43's models.md xAI groundwork overlaps it, and **#65 lands first** (thins the skills; #34's new mechanisms then go into `moa.md` only) |

## Sequencing rules (standing)

- **Strictly serial on the hotspots**: `build/SKILL.md`, `ship/SKILL.md`, `dev/SKILL.md`,
  `wi-directory.md`, `workflow.md`: never two branches editing them at once. Stacked PRs,
  squash-merge, rebase + retarget the next after each merge.
- **Agent charters are the most sensitive surface** (autonomous, no human in the loop): minimal
  additive diffs only; never alter report caps, output markers, verification-gate contracts, or
  tool lists. The #41 charter passes (owner-directed, 2026-07-11) were the one sanctioned exception;
  currently only #52 may touch them.
- **No em-dashes anywhere** (owner, 2026-07-11): shipped text, scripts, manifests, PR bodies, and
  commits are em-dash free; machine-read markers use hyphen forms. Frozen archives (`docs/plans/`,
  `docs/specs/`) keep their original punctuation.
- `release/1.8.0` is pinned (Checkpoint-B-validated bytes) for the Grok Build comparison; don't
  delete it; the local `checkpoint-b` evidence folder outside the repo is permanent.

## Standing guardrails (apply to every PR)

1. **Rules inventory** before/after for any PR that moves, rewords, or deletes rule text; attach it
   to the PR body. Test: *does each touched file still make correct decisions if loaded alone?*
2. `python scripts/validate.py` + `pytest tests/` green (never pipe validate.py through `tail`:
   exit code swallowed); after bulk markdown edits check file **tails** (the repo has shipped
   mid-sentence truncations; validate.py guards only trailing-newline + fence balance).
3. Behavior/artifact changes → **minor** bump, pure relocation/compression → patch; all **three**
   manifests together (`.claude-plugin/plugin.json`, the wi entry in `marketplace.json`,
   `.codex-plugin/plugin.json`; validate.py enforces parity).
4. New files only in `.gitignore`-whitelisted dirs (`references/`, `docs/`); any new top-level path
   needs a `!/path` line or it silently vanishes.
5. Citations use `name:N` locators (`ship:8`, `sdd:7.1.3`) or quoted headings; never the section
   sign (validate.py bans it), never spelled-out step/section words.
6. No AI attribution in commits or PRs.
7. Quality-sensitive changes validate against a **real run**, not a dry-run (a simulation shares the
   model's blind spots); the Checkpoint B harness (frozen A/B transcripts + `analyze.py` + dossier
   snapshot-diff + independent code review) is the reusable method.

## Pick-up notes (carried from the triage doc + the issues)

- **#52**: log strings and the checker contract stay byte-identical; the generality proof (new
  capability = registry row + tag, zero protocol changes) is demonstrated on paper in the PR body.
- **#53**: prefer the meta.json `description` + description==Source convention over the id-join
  (no ledger byte-format change); keep the count-mismatch note; `--write` stays idempotent.
- **#65**: keep the *trigger* line in each SKILL body (the orchestrator must know when to reach for
  `moa.md`); evict only the restated mechanics. No behavior change: a `points: none` run dispatches
  identically to today. Serial on the hotspots; sequence ahead of #34, never parallel with it.
- **#43**: all runtime claims (install path, namespace, `/goal` semantics vs wi's condition
  template, model ids) verified on a real Grok Build session before merge; keep-alive lands in the
  `/goal` family branch with the headless `-p`/`--max-turns`/`--continue` fallback.

## Shipped (roadmap-era)

- **#41 compress skill prose, FULL SERIES**: **v1.9.1 → v1.9.10**, PRs #55-#64, merged in stack
  order 2026-07-12. Nine loaded files compressed (ship #55, research #56, build #57, dev #58,
  rpa #59, scan #60, and the three charters #61-#63 under an explicit owner override of the
  additive-only rule): 17,750 → 15,624 words (−12.0%), roughly −3,240 tokens per full context load;
  every rule, contract string (559 grep-verified), template, command, threshold, and `name:N`
  anchor intact; rationale relocated to `docs/wi-design-notes/<file>.md` (one per pass, never
  loaded at runtime). Verified per file by a load-alone Q&A agent (131/131 scenarios after four
  verbatim restorations at assembly) and an independent removed-behavior audit (9/9 CLEAN);
  validate.py + 47 tests + CI green on every PR. PR #64 closed the series with the repo-wide
  em-dash sweep (884 substitutions across 47 files, shared markers reconciled to hyphen forms;
  `docs/plans/` and `docs/specs/` frozen). Method record: the E1 plan doc
  `docs/plans/2026-07-11-pre1-41-ship-compress.md`; per-file inventories ride in the PR bodies.
- **#48** drop legacy/backward-compat support: **v1.9.0**, PR #54 (2026-07-11). Seven
  compat families deleted (deleted-vs-relabeled disposition table in the PR body); dev classifier =
  five classes, `feature-folder-cases.md` = four case sections; validate.py bans `.wi/goals`
  unconditionally; the ledger gate accepts only the Duration format (retires the #35 legacy-ledger
  guardrail). Stays-list honored: `agents/` byte-identical, self-repair mechanisms relabeled, not
  removed. Plan: `docs/plans/2026-07-11-prd2-48-drop-legacy.md`. −294 words of shipped prose.
