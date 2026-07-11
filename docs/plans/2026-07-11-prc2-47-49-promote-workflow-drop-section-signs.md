---
type: Implementation Plan
title: "PR C2 — #47 promote workflow.md to top-level references/ + #49 replace section-sign citations with plain names (v1.7.2)"
description: Housekeeping pair — pure git mv of the house-rules reference plus its six literal-path citation sites, then a repo-wide sweep of the section-sign symbol to quoted headings / step N / section N, enforced by a new validate.py lint.
timestamp: 2026-07-11
tags: [consistency, safe-refactor, housekeeping, plan]
---

# PR C2 — #47 + #49 (v1.7.2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. This plan is markdown prose surgery: "tests" are `scripts/validate.py`, `pytest tests/`, grep assertions, planted-lint checks, and file-tail checks.

**Goal:** land GitHub issues #47 (promote `workflow.md` from `skills/research/references/` to top-level `references/`) and #49 (replace every section-sign citation in shipped text with plain names, plus a lint that bans the symbol) as one patch release, v1.7.2 — mechanical housekeeping, no behavior change.

**Architecture:** #47 first (move + path updates, moved file byte-identical), then #49 (the symbol sweep rewrites the citation strings #47 just touched, so each line reaches its final form inside one PR — the reason the triage doc pairs them). Baseline: `main@2d0436a` (v1.7.1).

## Global constraints (triage guardrails)

- `python scripts/validate.py` + `pytest tests/` green after each commit; check file **tails** after bulk markdown edits (repo has shipped mid-sentence truncations). Never pipe validate.py through `tail` (exit code swallowed).
- Agent charters (`agents/*.md`): **symbol swaps only** — never alter report caps, output markers, verification-gate contracts, or tool lists.
- No new files outside whitelisted dirs (`references/` and `docs/` are whitelisted).
- No AI attribution in commits/PRs.
- Version: `.claude-plugin/plugin.json`, the wi entry in `.claude-plugin/marketplace.json` (top-level `0.1.0` schema version stays), **and** `.codex-plugin/plugin.json` (validate.py enforces three-way parity) → **1.7.2**.

---

## #47 — inventory of literal-path citation sites (6, verified at baseline)

Only `skills/research/SKILL.md` uses the `${CLAUDE_PLUGIN_ROOT}/` form (mechanically guarded by validate.py's broken-ref check); the other five are bare backticked paths, proven by the grep acceptance check instead. Bare-name `workflow.md` citations (the majority) are path-independent and stay untouched.

| Site | Current form | New form |
|---|---|---|
| `skills/research/SKILL.md` "Phase contracts" footer | `${CLAUDE_PLUGIN_ROOT}/skills/research/references/workflow.md` | `${CLAUDE_PLUGIN_ROOT}/references/workflow.md` |
| `skills/scan/SKILL.md` (python-fallback note) | `` `skills/research/references/workflow.md` `` | `` `references/workflow.md` `` |
| `references/models.md` (diff-review python-fallback note) | same | same |
| `skills/rpa/references/build-uipath.md` | same | same |
| `skills/rpa/references/build-maestro.md` | same | same |
| `skills/rpa/references/uipath-bootstrap.md` | same | same |

`docs/plans/` mentions of the old path are historical archives — out of scope, unchanged (same rule #49 applies to docs/).

- [ ] `git mv skills/research/references/workflow.md references/workflow.md` (byte-identical; expect R100 in the diff).
- [ ] Update the six citation sites above — path string only, nothing else on the line changes in this commit.
- [ ] Commit 2 of the PR (after the plan-doc commit): validate.py green proves the `${CLAUDE_PLUGIN_ROOT}` ref resolves; `grep -rn "skills/research/references/workflow" skills agents references scripts tests .claude-plugin README.md AGENTS.md` returns nothing.

## #49 — sweep inventory by replacement shape (baseline: 121 section-sign lines across 30 files)

**Amended convention (owner decision, 2026-07-11, mid-PR):** the issue's spelled-out `step N` / `section N` forms were rejected during implementation as too wordy per cite; the owner chose the **`name:N` locator** (the `file:line` idiom) for every numbered citation instead. Quoted headings stay. Pre-existing cite-shaped `step N` / `section N` words in shipped text (from PR C-era edits) convert to locators too, so the repo carries exactly one convention.

Shapes (one rule per citation shape):

1. **Named section → quoted heading.** `workflow.md "Script invocation"` (10 sites), `integrations.md "Who initiates"` (dev, rpa, AGENTS.md), `integrations.md "Frontend work"` (build, wi-task-runner), `models.md "First-run setup"` (dev, rpa). Targets verified verbatim: `## Script invocation`, `### Who initiates: wi does`, `## Frontend work`, `## First-run setup (dev / rpa entry points)` — the quoted text is the heading's stable prefix, as the issue's own examples spell it.
2. **Numbered skill step → `skill:N` locator.** `ship:8`, `build:2`, `research:0`, `research:1c`, `plan:2`, `dev:4`, `rpa:6`, `scan:4`. In-file self-cites carry the file's own name (`ship:2` inside ship/SKILL — a bare `:2` is never valid); discrete lists repeat the locator (`ship:1/ship:8`); `wi:ship step 2` normalizes to `ship:2` (no double colon); `rpa/SKILL step 7` → `rpa:7`.
3. **Numbered document/ToC section → `doc:N` locator.** `sdd:10 in the base ToC`, `sdd:7.1.3`, `sdd:1.3/sdd:3.1/sdd:7.2–7.6` (discrete lists repeat; ranges collapse into one locator: `sdd:1-7`, `sdd:7.2–7.6`) across sdd-template, rpa-directory, refr-/maestro-architecture, verification-gate (rpa), brainstorm-protocol, connectors, build-uipath, wi-code-checker, rpa/SKILL, README diagram label; brainstorm-protocol's **own** numbered sections cite as `protocol:5`, `protocol:6a` (its established shorthand), ingest.md's as `ingest:1` (never `ingest.md:1` — that reads as a line number).

Files in the sweep (section-sign line counts at baseline): ship/SKILL 20 · brainstorm-protocol 13 · rpa/SKILL 12 · sdd-template 9 · rpa-directory 7 · rpa verification-gate 6 · integrations 5 · models 4 · wi-code-checker 4 (5 symbols — **charter: symbol swap only**) · research/SKILL, wi-directory, dev/SKILL, keep-alive, refr-architecture, maestro-architecture, build-uipath, validate.py 3 each · build/SKILL, worktrees-and-subagents, scan/SKILL, build-maestro 2 each · plan/SKILL, workflow.md, connectors, ingest, uipath-bootstrap, ship verification-gate, wi-task-runner (charter), README.md, AGENTS.md 1 each.

README.md and AGENTS.md sit outside the lint scope but are shipped repo text citing the same conventions — swept for consistency (2 lines total).

- [ ] Sweep shapes 1–3 across `skills/ agents/ references/` + README.md + AGENTS.md; reflow lines where needed; `docs/` untouched.
- [ ] Convert pre-existing cite-shaped `step N` / `section N` words in lint scope to locators (models.md first-run/dispatch lines, feature-folder-cases.md, rpa verification-gate's `rpa step 7`, …) — citation forms only; headings, labels, and step-intro lines (the cite *targets*) stay.
- [ ] `scripts/validate.py`: retarget `DEAD_SDD_S13` to the retired anchor's new spellings (`sdd:13` or case-insensitive `section 13`, word-bounded), update its message; add the section-sign ban over the existing `lint_scope` (skills / agents / references / .claude-plugin); update the module docstring (which itself drops the symbol and names the locator convention).
- [ ] Commit 3: validate.py + pytest green; `grep -rn "§" skills agents references .claude-plugin` → zero hits.

## Verification (PR-level)

- [ ] Planted-lint check: a temp file in lint scope containing the section sign fails validate.py; one containing `section 13` fails the dead-anchor lint; both removed after.
- [ ] Agent-charter diffs reviewed: `agents/wi-code-checker.md` (4 lines) and `agents/wi-task-runner.md` (1 line) show symbol swaps only.
- [ ] Spot-check each quoted-heading cite resolves against its target file (grep the quoted text).
- [ ] File tails intact on every edited file; validate.py's truncation guards green.
- [ ] Version parity 1.7.2 across the three manifests.
- [ ] PR body carries the per-issue evidence; `Fixes #47`, `Fixes #49`; squash-merge per repo convention.
