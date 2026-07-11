---
type: Implementation Plan
title: "PR D — #42 compress runtime reasoning: one canonical directive + hard-step carve-outs (v1.8.0)"
description: One shared references/ note minting the compact-reasoning rule (essential, decision-bearing thoughts only), cited from the three agent charters and the build/dev/rpa orchestrator skills; carve-outs keep full depth on hard steps; merge gated on Checkpoint B (a real /wi:dev run vs a frozen baseline).
timestamp: 2026-07-11
tags: [context-budget, agents, careful-refactor, plan]
---

# PR D — #42 (v1.8.0)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. This plan is markdown prose surgery: "tests" are `scripts/validate.py`, `pytest tests/`, grep assertions, charter-diff audits, and file-tail checks.

**Goal:** land GitHub issue #42 — compress the internal reasoning ("monologue") the orchestrator and subagents *generate* at runtime — as v1.8.0. Additive directive, no behavior change to any report format, cap, marker, gate, or rule. Baseline: `main@76b62e4` (v1.7.2).

**Why minor:** an agent-runtime behavior directive (how agents reason), not a relocation/compression of existing prose → **1.8.0** per the triage doc's grouping table.

**Grouping decision:** the issue sketches "one charter/skill per PR"; the triage doc (roadmap layer, decided later) groups #42 as a single PR D — the shared-reference form makes per-file PRs pointless, since the directive text lives once in `references/` and each touch point carries only a citation line. Reverting the PR reverts the whole norm cleanly.

## Architecture

- **Canonical owner:** new `references/compact-reasoning.md` (top-level — it is cited from `agents/*` and cross-skill, so a skill-scoped home would dangle on per-skill installs; same reasoning as #47's promotion of workflow.md). Mints the handle **the compact-reasoning rule** (sibling of workflow.md's **context budget** / **output house rule** — #42 is the third token stream: generated reasoning, beside loaded prose (#41) and retained tool output (#36)).
- **Six touch points, pointer-style** (#40's lesson applied proactively): each states the operational core in 2-4 lines and cites the note — never a restatement of the full rationale.
  - `agents/wi-task-runner.md` — after the anti-thrash (5+ reads) paragraph; no charter-specific carve-out (none named by the issue).
  - `agents/wi-researcher.md` — end of ## Output, beside the report/budget discipline; carve-out: tech-choice survey/comparison/decision keeps full depth.
  - `agents/wi-code-checker.md` — after the preamble; carve-out: the adversarial verification itself keeps full depth.
  - `skills/build/SKILL.md` — end of the Inputs/context-budget paragraph (build is the multiplier hotspot: task-runner waves + checker rounds).
  - `skills/dev/SKILL.md` — Boundaries, beside the context-budget bullet, stated run-wide (dev sequences every phase, so the umbrella covers phase orchestration without editing `research/SKILL.md`, which #42's file list deliberately excludes — its orchestrator-side work is mostly carve-out territory: plan decomposition + the gate).
  - `skills/rpa/SKILL.md` — "What carries over from the wi spine" (the spine-discipline roster).
- **Citation forms:** skills cite with the `${CLAUDE_PLUGIN_ROOT}/references/compact-reasoning.md` path once (validate.py's broken-ref check then guards it mechanically); charters cite the bare repo-relative path (precedent: wi-task-runner's integrations.md cite). Locators per the name:N convention; no section signs, no spelled-out step/section words.

## Rules inventory (the carve-out list — attach to the PR body)

The directive: **essential, decision-bearing thoughts only** — reason enough to decide correctly, then act; no meta-narration, no restating the dispatch/plan handed in, no re-deriving what an artifact already settles. Depth that must survive goes in the artifact (notes file, spec, report), never in monologue.

Carve-outs that keep **full reasoning depth** (from the issue, verbatim scope):

| Hard step | Where it lives | Guarded by |
|---|---|---|
| Research approach selection (tech-choice survey, comparison, decision) | `wi-researcher` loop | charter carve-out line + note |
| Adversarial verification (coverage tracing, refutation, evidence) | `wi-code-checker` both modes | charter carve-out line + note |
| Plan decomposition (spec/tasks; SDD on rpa runs) | research skill's plan phase / rpa:4 | note (cited run-wide from dev) |
| Design gates (assembling + weighing what is rendered) | research gate / rpa:5 | note (cited run-wide from dev) |

Unchanged by decree (the standing charter rule): report caps (~15/~20 lines), output markers (`## TASK COMPLETE`, `## RESEARCH COMPLETE`, `## CHECK PASSED`/`## ISSUES FOUND`), verification-gate contracts, tool lists, read/token budgets, MoA roles.

## Global constraints (triage guardrails)

- `python scripts/validate.py` + `pytest tests/` green after each commit (never pipe validate.py through `tail` — exit code swallowed); check file **tails** after every markdown edit (repo has shipped mid-sentence truncations).
- Agent charters: **one additive directive paragraph each, nothing else** — never alter report caps, output markers, verification-gate contracts, or tool lists.
- New file only in whitelisted `references/` (deny-all `.gitignore`).
- No AI attribution in commits/PRs.
- Version → **1.8.0** in all three manifests: `.claude-plugin/plugin.json`, the wi entry in `.claude-plugin/marketplace.json` (top-level `0.1.0` schema version stays), `.codex-plugin/plugin.json` (validate.py enforces three-way parity).

## Tasks

- [ ] Commit 1: this plan doc (`docs(plans): PR D plan — #42 compact reasoning`).
- [ ] Commit 2: `references/compact-reasoning.md` (OKF `type: Reference`; the rule, the carve-outs, the boundary) + the six citation sites above.
- [ ] Commit 3: version bump 1.8.0 across the three manifests.
- [ ] Push `prd-42`, open the PR: `Fixes #42`, body carries the carve-out inventory, the loaded-weight delta (this PR *adds* loaded lines; the saving is output tokens at runtime), and the Checkpoint B merge gate.

## Verification (PR-level)

- [ ] validate.py + pytest green; OKF frontmatter on the new note parses; `${CLAUDE_PLUGIN_ROOT}` ref resolves.
- [ ] Charter-diff audit: `git diff main -- agents/` shows exactly one added paragraph per charter, no deletions, no edits to caps/markers/contracts/tool lists.
- [ ] Grep: all six touch points cite `compact-reasoning.md`; no section signs, no `sdd:13`/`section 13`, no other banned strings introduced.
- [ ] File tails intact on every edited file (validate.py's truncation guards green).
- [ ] Version parity 1.8.0 across the three manifests (validate.py check).

## Checkpoint B — the merge gate (not part of this implementation session)

Per the triage doc: **PR D merges only after Checkpoint B passes** — one **real** `/wi:dev` run (not a dry-run: a simulation shares the model's blind spots), snapshot-diffed against a frozen pre-#42 baseline. Pass = same files, decisions, gate outcomes, and report contents — only the reasoning got shorter; the token ledger (`tokens.md` + ship's `token_report.py`) shows the output-token drop at equal quality, and the hard-step artifacts (research recommendation, checker findings, plan coverage) show no depth regression. Baseline material: the Pile-1 comparison method in `docs/plans/2026-07-10-pile1-dryrun-comparison.md` (its snapshot-as-regression method, now applied to a real run).
