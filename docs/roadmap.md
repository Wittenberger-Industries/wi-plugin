---
type: Roadmap
title: "Witloop roadmap: the live queue of open issues"
description: Tracking surface for all open issues; order, version targets, sequencing constraints, and the standing per-PR guardrails. Supersedes the 2026-07 triage doc as the thing that gets updated; that doc is frozen as the sweep's history.
timestamp: 2026-07-11
tags: [roadmap, triage, plan]
---

# Witloop roadmap (live)

**This file is the tracking surface for open work: update it here, not in the triage doc.**
History and rationale of the 2026-07 sweep live in `docs/plans/2026-07-10-issue-triage-35-42.md`
(frozen; PRs A–D shipped #35–#40, #42, #47, #49 as v1.6.0 → v1.8.0, Checkpoints A and B passed;
B's record: `docs/plans/2026-07-11-checkpoint-b-42.md`). Every issue below is spec-grade (acceptance
criteria + file lists in the body); the per-issue implementation plan is written from that AC at
pick-up, into `docs/plans/`, and rides in the PR.

## Queue (in order)

**The queue is empty** (2026-07-12): every actionable issue has shipped, #43 included. The one item
below stays owner-postponed; un-postpone it or file new work to continue.

| Slot | Issue | What | Version | Effort · Risk | Why this order |
|---|---|---|---|---|---|
| ⏸ postponed | **#34** cross-vendor MoA proposers | Let the MoA council use OpenAI / DeepSeek / Grok / Gemini | - | - | Postponed (owner, 2026-07-10); **its prerequisite #65 has now shipped** (skills thinned; #34's new cross-vendor mechanics go into `moa.md` only). Also simplified by #35, and #43's shipped models.md xAI + platform-map groundwork overlaps it. Owner un-postpones when ready |

## Sequencing rules (standing)

- **Strictly serial on the hotspots**: `build/SKILL.md`, `ship/SKILL.md`, `dev/SKILL.md`,
  `wit-directory.md`, `workflow.md`: never two branches editing them at once. Stacked PRs,
  squash-merge, rebase + retarget the next after each merge.
- **Agent charters are the most sensitive surface** (autonomous, no human in the loop): minimal
  additive diffs only; never alter report caps, output markers, verification-gate contracts, or
  tool lists. The sanctioned exceptions are spent (#41 charter passes and #52's one clause swap, both
  owner-directed and shipped); no open issue may touch them.
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
   manifests together (`.claude-plugin/plugin.json`, the wit entry in `marketplace.json`,
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

- **#34** (when un-postponed): #65 shipped, so add the cross-vendor proposer mechanisms to
  `references/moa.md` only; do not reinline them into the thinned SKILL bodies. #43's shipped
  groundwork already covers the models.md xAI entry + the platform model map.

## Shipped (roadmap-era)

- **#70 + #71** Grok ledger follow-ups: **v1.12.1**, PR #72 (2026-07-12, same day as #43; both measured
  on baseline-d, the first run of published 1.12.0). **#70**: ship finalized tokens.md with
  `token_report.py` unconditionally (the template `_PENDING` text and ship's finalize line named it with
  no platform fork; a Grok run under-logged 5 of 17 rows) - the platform pointer now rides the point of
  use (`_ledger.py` TEMPLATE + wi-directory copy + ship:6's finalize line: non-Claude hosts run the
  finalizer their tool map names, Grok = `grok_token_report.py --write`), and grok-tools.md adds the
  wave-gate row-append rule (Grok completions are pull-based; append-on-notification silently skips).
  **#71**: `grok_token_report.py --write` now subtracts measured human approval-waits
  (`events.jsonl` `permission_resolved.wait_ms`, summed inside the autonomous phase windows only) from
  the wall-clock and records the subtraction as its own Orchestrator line ("excl. manual steps" made
  literal; print mode reports the session-wide wait). Baseline-d evidence: one unattended prompt =
  21m50s of a 57m52s wall; net 36m02s ~= the 36m50s compute sum. 2 new tests (70 total), verified
  against the real session; Claude-side behavior byte-identical; three-way parity at 1.12.1.

- **#43** Grok Build as the fourth platform: **v1.12.0**, PR #69 (2026-07-12). Thin adapter, every
  runtime claim measured on a real Grok Build 0.2.93 session (S1-S8 spike + two-run live E2E; record:
  `docs/plans/2026-07-12-43-grok-spike-results.md`). Corrected issue #43's own framing three ways: Grok's
  `/goal` is model-judged (`update_goal`) -> a THIRD keep-alive branch, not the Claude/Codex predicate
  family; `${CLAUDE_PLUGIN_ROOT}` is hook-only/empty in tool shells -> mandatory resolve-once protocol in
  `references/grok-tools.md` (the `installed_plugins.json` step resolves in practice, merge-gated on a
  live agent-resolved script run); `grok -w` is a standalone COPY, not a linked worktree -> path-based
  detection. models.md gained `## Platform model resolution` + xAI cross-provider (rides `_call_openai`,
  `XAI_BASE`); new `skills/ship/scripts/grok_token_report.py` finalizes tokens.md from Grok session files
  (exact per-subagent split; 8 tests). Charter exception: one owner-sanctioned token
  (`wi-code-checker` `color: magenta` -> `purple`; Grok silently drops agents on unsupported colors).
  Rode along owner-directed: **F1** (interactive `--auto` can no longer skip brainstorm; closed
  self-answer stamp set, headless-only carve-out) and **F2** (verify skill absence against the
  installed-plugins registry before any fallback stamp) - both surfaced by the baseline a/b/c comparison,
  where the brainstorm-skipping run graded C+ with a security BLOCKER while the dialogue runs graded A-
  on both harnesses; validate.py anchors both clauses. Byte-stable Claude/Codex/Copilot branches;
  three-way manifest parity; validate.py + 68 tests + CI green. Evidence archives (permanent):
  `D:\ClaudeCowork\wi-plugin\checkpoint-b\` (baseline-c runs + four-way quality review).

- **#65** centralize MoA/routing mechanics: **v1.11.1**, PR #68 (2026-07-12). The five always-loaded
  SKILL bodies (research/ship/build/dev/rpa) restated MoA proposer/aggregator/`layers` + routing
  resolve-once mechanics on top of pointing at `references/moa.md` + `references/models.md`; move-then-
  compress relocated the skill-only bits into the references (moa.md gained the proposer research-charter
  + dissent-to-ADR/gate wiring, the identical-proposer-prompt rule, the aggregator dedupe/max-severity/
  verify-before-drop rule, "counts as one review round"; models.md gained the warn-once clause at the
  apply step) and thinned each skill to a trigger + pointer. Always-loaded bodies -290 words (paid every
  turn); moa.md +114 (on-demand only, MoA off by default so most runs never load it). Every trigger +
  the four contract log strings intact; a `points: none` run is byte-identical to before. Independent
  removed-behavior audit SAFE; validate.py + 53 tests + CI green. Pure relocation -> patch. Plan:
  `docs/plans/2026-07-12-65-centralize-moa-routing.md`.
- **#52** dispatch-time skill pointer: **v1.11.0**, PR #67 (2026-07-12). Pinned runners have no `Skill`
  tool, so the orchestrator resolves a capability-tagged skill's `SKILL.md` path once per run into
  progress.md's new `## Skill paths (resolved)` block (lazy) and the dispatch hands the runner that path
  to Read; the broken "check your skills list" clause in `wi-task-runner.md` became the general
  dispatch-pointer contract (one clause swap, frontend as the worked instance). `integrations.md` made
  the capability → skill registry role explicit (new capability = registry row + plan tag, zero
  protocol/charter change; generality proven on paper in the PR). No `Skill` in any charter, no new
  agent type; checker rule + the two frontend log strings + rpa/uipath delegation byte-identical.
  Independent load-alone review CONSISTENT (9/9); validate.py + 53 tests + CI green. Plan:
  `docs/plans/2026-07-12-52-dispatch-skill-pointer.md`.
- **#53** ledger split labels: **v1.10.0**, PR #66 (2026-07-12). `token_report.py`'s `parse_agent_file`
  labels each `## Subagent detail` row from the harness sidecar `agent-<id>.meta.json` (`description` →
  `agentType` short name → old prompt prefix → `(no prompt)`); missing/unparseable meta.json falls
  through to the prompt prefix (older sessions, Codex/Copilot), never crashes. `wi-directory.md` gained
  the `description`==`Source` convention so the split and ledger tables join by name. Option 1 (name-by-
  convention), so the ledger byte format and `_ledger.py`/`check_tokens.py`/guardrail tests are untouched
  (clear of #48). 6 new tests; validate.py + 53 tests + CI green. Plan:
  `docs/plans/2026-07-12-53-ledger-split-labels.md`.
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
