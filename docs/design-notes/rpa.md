---
type: Design Notes
title: "rpa: design rationale (maintainer notes)"
description: The "why" behind rpa/SKILL.md's rules, relocated out of the loaded skill by #41 (the runtime never reads this file); each entry is anchored to the step it explains.
timestamp: 2026-07-11
tags: [rpa, design-notes, context-budget]
---

# rpa: design rationale (maintainer notes)

`skills/rpa/SKILL.md` is loaded wholesale on every rpa run, so it carries rules only. The rationale
lives here, anchored by step. When editing the skill, keep this file in sync; a rule whose "why" is
deleted instead of relocated loses its guard against future "simplification".

## Intro

- **Mission.** `wit:rpa` is the rigorous front half of an RPA build: it does the thinking
  (ingest → TO-BE → SDD) and hands a high-fidelity spec to UiPath's own skills for the build. That
  split is why the skill never authors XAML/flows itself and why every build step delegates.
- **Why "borrow, don't reinvent" points at a table:** `uipath-bootstrap.md`'s capability table is the
  single source of truth for the delegated-skill slugs; wit delegates by capability, never by a
  hard-coded name, so an upstream slug rename costs one table edit instead of a sweep.
- **Why the UI-vs-API default cuts both ways:** connectors/APIs are preferred where one exists because
  they are more robust than UI selectors; "UI is a fine answer when it doesn't" is the counterweight
  that stops the flow from forcing API answers onto genuinely UI-shaped processes.

## rpa:1 (bootstrap)

- **Why the .NET 8 runtime is a prerequisite:** the `uip` CLI and the UiPath build toolchain need it;
  the check/install mechanics live in `uipath-bootstrap.md`, which the step follows.

## rpa:2 (ingest and register)

- **Why the run-slug is numbered:** `NNNN-<name>` mirrors the `ADR-NNNN` convention, one global 4-digit
  ordinal so runs list in implementation order; the derivation detail is canonical in ingest:1
  (wit-directory.md's Slugs bullet).
- **Why the first-run setup is a trigger plus a citation:** models.md "First-run setup" is canonical
  for the whole procedure, including the warn-once on an orchestrator-tier mismatch; restating it in
  the skill was belt-and-suspenders and drifted twice historically.
- **Why `rpa-build` is a role label:** there is no `agents/rpa-build.md`; the label exists so RPA build
  delegations can be routed independently of the other roles without registering a new agent. The
  resolution chain (override → `wit-task-runner` role → `inherit`) is canonical in models.md's dispatch
  rule.
- **Why project-level outputs commit where written:** the post-gate worktree branches from main and
  must already carry `inputs.md` / `components.md` / `orchestrator.md` / `models.md` /
  `rpa-constitution.md`; the canonical statement is rpa-directory.md's "Project-level files" bullets.
- **A trimmed restatement:** the old step 2 also noted that at ship the cross-provider diff review
  layers on top of wit-code-checker's result-mode pass; that is ship:2's rule (rpa:7 reuses ship), and
  nothing at rpa:2 depends on it beyond resolving the routing rows.

## rpa:3 (brainstorm)

- **Why the mode stamp exists:** the engine (superpowers vs wit fallback) and the interactivity
  (dialogue vs self-answered) must be auditable per run; the exact stamp strings and the headless rule
  are canonical in brainstorm-protocol.md.
- **The Orchestrator-provisioning elicitation list** (org/tenant/folder link, UiPath Agent names, the
  queue / asset / storage-bucket / published-process names) is canonical in protocol:6, together with
  the `.wit/orchestrator.md` manifest template it fills.

## rpa:4 (plan)

- **What the two architecture diagrams contain** is canonical in the framework references the step
  routes to: `refr-architecture.md` (Runtime diagram: Dispatcher + every Performer + queues + systems +
  Orchestrator) and `maestro-architecture.md` (flow diagram: trigger + nodes + systems/agents).
- **Why sdd:1.3/sdd:3.1/sdd:7.2–7.6 fill from `.wit/orchestrator.md`:** those SDD sections need the
  concrete elicited resource names, not placeholders; the manifest is where brainstorm captured them.
- **Why the dev-verification strategy rides `tasks.md`:** so the design gate approves *how the build
  will verify*, not just what it builds; a tenant-less run otherwise discovers at build time that its
  queue-dependent runtime checks cannot run.

## rpa:5 (design gate)

- **Why the ledger row is appended on the completion notification:** the token figure exists only in
  that notification (wit-directory.md's ledger rule; a round returning without one records
  `unavailable`, never an estimate). The pre-gate scaffold mirrors the dev flow's research-start
  scaffold so the first checker round always has a ledger to append to; rpa:6's scaffold-if-absent
  stays as the fallback for runs that reach build without one.
- **Why the dossier commits on main at the gate:** the gate decision is made against committed
  artifacts, and the build worktree (branched from main) starts with them; like the ADR, the dossier
  rides the branch and the PR. The mid-build reopen skips the main commit because the worktree branch
  already carries the amendments and merges them back.
- **Why learnings are harvested at the gate, not only at ship:** wit:rpa's front and back halves often
  run in different environments, so without a gate-time harvest a front-half-only run leaves no
  compounded knowledge; ship confirms the *candidate (pre-build)* entries against the build and
  promotes the general ones.

## rpa:6 (build)

- **"Framework-neutral" is load-bearing:** `build-uipath.md` and `build-maestro.md` both point back to
  rpa:6 as the one place the worktree + branch are created, so neither build reference may create its
  own isolate. It is also the same first step as `wit:build`, on purpose: one worktree discipline.
- **Why "never Blank":** scaffolding each unit as REFramework per the SDD is the contract with
  `uipath-rpa`; a Blank project silently drops the state machine, config, and retry semantics the SDD
  assumes.

## rpa:7 (verify and ship)

- **Why publish can never fail the run:** the PR is the deliverable; publish is a best-effort
  post-gate convenience, so a missing tenant connection or a publish error is recorded with its
  recovery `uip` command instead of failing a shipped feature.
- **Why a prod folder needs explicit gate approval:** publishing to prod is the flow's one
  production-facing action; `--auto` may never select it on its own.
- **Why the dossier manifest is cited, not restated:** ship's tidy reads the run manifest from
  rpa-directory.md ("take the manifest from the flow's directory reference, not from memory"), so
  restating the file list in the skill only created a second copy that could drift. `orchestrator.md`
  stays project-level (updated in place, never swept) because it is a cross-run registry, not run
  ephemera.

## What carries over from the wit spine

- **Why the roster exists:** `wit:rpa` swaps the *domain* (UiPath/SDD/PDD) into the same machine; the
  spine disciplines (gate, worktrees, waves, docs-sync, compound, token report, `check_mermaid.py`,
  plugin-bootstrap) are inherited, not redefined, so the section lists them instead of re-specifying
  them.
