---
type: Design Notes
title: "scan: design rationale (maintainer notes)"
description: The "why" behind scan/SKILL.md's rules, relocated out of the loaded skill by #41 (v1.9.1); the runtime never reads this file; each entry is anchored to the section it explains.
timestamp: 2026-07-11
tags: [scan, design-notes, context-budget]
---

# scan: design rationale (maintainer notes)

`skills/scan/SKILL.md` is loaded wholesale at scan time, and two of its outputs (`constitution.md`,
`repo-map.md`) then sit in the orchestrator's context for entire runs, so the skill carries rules only.
The rationale lives here, anchored by section. When editing the skill, keep this file in sync: a rule
whose "why" is deleted instead of relocated loses its guard against future "simplification".

## Intro

- **Mission.** scan does the one-time groundwork so `/wi:dev` can run smoothly later; every later phase
  reads what scan wrote instead of re-deriving it. The four output files are the contract; the procedure
  is just how they get filled.
- **Why `--refresh` re-verifies instead of re-documenting:** repos move on without wi (humans commit,
  dependencies change, modules appear), and `dev` auto-invokes the refresh at feature start, so it must
  stay cheap; re-documenting is the expensive path and mostly churns prose.

## scan:2 (existing repos; the greenfield guided setup)

- **Why config/lock files, not source wholesale:** the stack signal lives in manifests and lockfiles;
  wholesale source reading burns the orchestrator's context (workflow.md's context budget). The same
  budget is why a large repo is scanned by a dispatched subagent that returns the filled-in templates
  instead of pulling the tree into the orchestrator.
- **Why the guided setup exists (instead of marking a greenfield repo UNKNOWN):** the point is to give
  later phases real ground truth. dev's handoff preflight arms the keep-alive condition from
  `repo-map.md`'s commands: `UNKNOWN - ask` blocks it, while a genuinely-absent tool recorded as
  `n/a - not configured` passes with that clause dropped (keep-alive.md's fill rule). An invented
  command would poison every later gate, which is why "don't invent it" is absolute. A later scaffolding
  feature can fill honest gaps; the confirmed intent is on record either way.
- **Why one folded question round:** the greenfield questions merge into scan:4's constitution-confirm
  so the user answers once, not twice.
- **Why the greenfield `.gitignore` names `.wi/features/*/.logs/`:** that dir is wi's redirected command
  output (workflow.md's output house rule); seeding the ignore at scan time keeps the first build from
  leaking caches, build artifacts, and command logs into `git status`.

## scan:5 (plugin bootstrap)

- **Why offer, don't force:** canonical in `plugin-bootstrap.md` (never install without asking; never
  block if the user declines). The plugins are an enhancement, not a requirement: wi's phase skills
  re-detect availability at run time and fall back gracefully, so a "skip now" is never fatal.

## scan:6 (commit)

- **Why scan commits its own outputs:** wi-directory.md's project-level rule (committed where written).
  The commit is what makes the committed-`.wi/` promise true and puts the docs in every future worktree,
  since build worktrees branch from main and inherit them.

## scan:7 (report; the lean-file warning)

- **Why the ~150-line ceiling is worth a warning line:** `constitution.md` and `repo-map.md` are held in
  the orchestrator's context for entire runs (workflow.md's context budget), so overweight there is paid
  on every turn (~75 re-reads measured on a real run). The ceiling itself is wi-directory.md's lean-file
  rule; scan only surfaces breaches.

## `--refresh` A (drift check)

- **Why facts, not prose:** the refresh verifies exactly what a later phase would trust (commands,
  stack, structure) and touches only what drifted; anything more re-opens the full documentation pass
  that `--refresh` exists to avoid.
- **Why unchanged config means commands stand:** re-running the suite "to check" costs minutes and
  proves nothing a config diff didn't already; the `--version`/`--help` probe is the fallback only when
  reading the config is inconclusive.
- **Why diagram updates are structural-only:** the mermaid is a module/dependency map, not a change log;
  churn inside existing nodes doesn't change the picture.
- **Why the config/lock enumeration was trimmed from the skill:** the stack-detection cookbook is the
  canonical list (pyproject, package.json, lockfiles, CI workflows, tool configs); repeating it in the
  skill invited drift between the two lists.

## `--refresh` B (memory hygiene)

- **Why the index target (roughly 30 lines):** learnings recall is via the index (wi-directory.md);
  every phase reads it per feature, so the compounding memory only stays useful if it stays lean.
- **Why promote-then-tombstone:** a standing rule belongs in its source of truth, where every phase
  already looks; the tombstone keeps the index honest about where the learning went, and deleting the
  detail file keeps the knowledge in exactly one place.
- **Why ADRs are never pruned:** they are the project's decision history; superseding with a new ADR
  preserves the trail a future maintainer follows.
- **Timing note (lag, not drift):** ship commits a feature's learnings on the feature branch, so main's
  `learnings.md` lacks in-flight features' lines until their PRs merge; wi-directory.md tells
  `scan --refresh` to read that as normal lag, not drift.

## Templates & the mermaid section

- **Why the `n/a - not configured` reminder sits inside the template block:** the token is machine-read
  (dev's handoff preflight and keep-alive.md's fill rule grep for that exact string), and the reminder
  riding the template is what stops a scan run from paraphrasing it.
- **Why the reserved-word list stays in the skill:** those IDs are real parse failures, observed rather
  than hypothetical: `graph` as a node ID collides with the diagram keyword and kills the whole render.
  The list is short and operative, so it stays loaded.
- **What `check_mermaid.py` catches (relocated catch-list):** reserved-word node IDs, unquoted
  special-char labels, unbalanced `subgraph`/`end`, unclosed fence; when `mmdc` (mermaid-cli) is
  installed it also does a true render. The skill mandates only "fix every error; never save a diagram
  that doesn't pass".
- **Why "tight and skimmable" closes the skill:** these files are read at the top of every later phase,
  so bloat there is paid many times over; the canonical ceiling is wi-directory.md's lean-file rule.
