---
type: Design Notes
title: "build: design rationale (maintainer notes)"
description: The "why" behind build/SKILL.md's rules, relocated out of the loaded skill by #41 pass 2 (v1.9.1); the runtime never reads this file. Each entry is anchored to the section it explains.
timestamp: 2026-07-11
tags: [build, design-notes, context-budget]
---

# build: design rationale (maintainer notes)

`skills/build/SKILL.md` is loaded wholesale and re-read on every later orchestrator turn (~75× measured
on a real run), so it carries rules only. The rationale lives here, anchored by section. When editing
the skill, keep this file in sync: a rule whose "why" is deleted instead of relocated loses its guard
against future "simplification".

## Intro

- **Mission.** Build is where wit spends real tokens, so it is where the discipline matters most. The
  two levers (isolate, delegate) are what keep a hands-off build affordable and safe; the orchestrator
  never implements tasks itself because everything it retains is re-read on every later turn
  (workflow.md "Token budget").
- **The engage stamp** (`build engine engaged (wit <version>)`) exists so the invocation is auditable;
  the version is read from `plugin.json`, never guessed, for the same reason. The old closing flourish
  "the gate was the last question" restated workflow.md's no-questions rule: the design gate is the
  final human checkpoint, so nothing after it may ask the user anything.

## build:1 (isolate)

- **Why a dedicated worktree and branch:** the main checkout stays clean, and independent features can
  run in parallel because each feature owns its worktree.
- **Why the dossier "rides in with the checkout":** research commits `.wit/features/<slug>/` on main at
  the design gate and the worktree branches from main, so the dossier is present from the first
  command; main's copy catches up when the branch merges. The canonical statement of these mechanics
  (including the resume case) is `skills/build/references/worktrees-and-subagents.md`; the skill keeps
  only the facts build acts on.

## build:2 (parallel waves)

- **Why fresh runners, dispatched wide:** fresh agents keep context from rotting across a long build,
  and parallel dispatch keeps wall-clock short. "Sequential execution ... never the default" is the
  same point inverted: an idle DAG is wasted wall-clock.
- **Why "(the block stands)" after an unavailable-model re-dispatch:** the config didn't change, so the
  resolved-routing block is not rewritten; it is re-resolved only when absent or when `.wit/models.md`
  changed after its stamp. models.md's resolve-once rule is the canonical statement.
- **Why the frontend log line is load-bearing:** ship's checker (result mode) flags any `[frontend]` UI
  built blind while a design skill was installed, and the `frontend via` line in `progress.md` is the
  evidence it audits. The canonical delegation rule lives in integrations.md "Frontend work"; the skill
  no longer restates the checker's enforcement.
- **Why one committer, one `progress.md` writer:** runners edit disjoint files in a shared worktree;
  serializing commits and ticks through the orchestrator keeps history and state clean.
- **Why the `tokens.md` row is appended the moment the completion notification arrives:** the exact
  figure exists only in that notification; deferred, it is gone, and the ledger rule forbids
  estimates.
- **Why the wave-end gate:** runners lint/typecheck only what they touched (a repo-wide sweep can trip
  over siblings' in-flight files, per `agents/wit-task-runner.md`), so the full suite runs once,
  serially, at each wave boundary. Both refinements, the wave-end gate and the sole-runner exception,
  were proven in dry runs; the sole-runner exception keeps full TDD where no test-run collision is
  possible, because only multi-test waves need authored-not-run.
- **Why the cross-provider review is described as a layer:** it never replaces wit-code-checker, and it
  runs at wave boundaries only when the resolved-routing block's row says `per-wave`, which itself
  implies a provider is configured (canonical: models.md's cross-provider section).

## build:3 (when a task fails)

- **Why attempts are bounded (≈3):** thrashing burns tokens without producing new information; the cap
  forces the switch to a structured debugging pass, and it matches the runner's own 3-attempt auto-fix
  cap in `agents/wit-task-runner.md`.
- **Why plan amendments are written down:** code silently drifting from the spec is the failure mode wit
  guards against; workflow.md's "Amend deliberately" rule is the canonical statement.

## build:4 (keep scope honest)

- **Why:** scope creep hidden inside a task is how builds drift from their spec. Routing in-scope gaps
  to `tasks.md` and out-of-scope ideas to `.wit/roadmap.md` keeps every scope change visible and
  decided, never accidental.
