---
type: Reference
title: "Integrations: borrow, don't reinvent"
description: "How wit detects installed skills and delegates to them (brainstorm, plan, build, ship, frontend design, debug), falling back to a light built-in version only when a preferred skill is absent."
timestamp: 2026-06-12
tags: [research, reference]
---

# Integrations: borrow, don't reinvent

wit is deliberately thin. Where a good skill already exists, wit **detects it and hands off**, adding only
its own opinions (the `.wit/` artifacts, the brainstorm-as-gate, the worktree discipline, the autonomous
pipeline). When nothing is installed, wit falls back to a light built-in version so it always works
standalone. `scan` offers to install the recommended set on first run (see the scan skill's
`plugin-bootstrap.md`).

## How to detect an available skill

A skill is "available" if it appears in the session's skills list, or its directory exists under a known
plugin/skills path. The deterministic sources, on any harness: the Claude plugin registry
(`~/.claude/plugins/installed_plugins.json` - each entry's `installPath`, skills under
`<installPath>/skills/`) and the flat `~/.agents/skills/` dir; harnesses that load Claude plugins
(Grok Build) read the same registry (the platform tool map has the concrete paths). **Never stamp a
`(<skill> absent)` fallback from memory: verify absence against the session list AND the registry
first.** If unsure, use `find-skills` (vercel-labs/skills) to discover/install one, or fall
back. Never hard-fail because an optional skill is missing; degrade gracefully and say which mode you're in.

**Delegation is mandatory when the skill is present.** The fallback column applies only when it is
absent. Every delegating phase logs its mode to progress.md: `<phase> via <skill>` or `<phase> via wit
fallback (<skill> absent)`, so a run's delegation behavior is auditable afterwards. Running a fallback
while the preferred skill is installed is a defect; speed, `--auto`, or "wit's format is required anyway"
are not bypass reasons - the delegate supplies the method, wit supplies the artifact.

This file is also the canonical **capability -> skill registry**: each row (and the "Frontend work"
mapping below) maps a wit capability to the skill(s) that serve it and the fallback. Pinned runners have
no Skill tool, so a capability-tagged task reaches its skill by pointer, not invocation: the orchestrator
resolves the mapped skill's `SKILL.md` absolute path once per run (progress.md's
`## Skill paths (resolved)` block) and the dispatch hands the runner that path to Read. Adding a new
skill-mediated capability is therefore a **registry row plus a plan tag** (today `[frontend]`) and
nothing else: the pointer protocol, the charters, and the plan format are unchanged.

## Delegation matrix

| wit phase | superpowers skill (REQUIRED when installed) | initiator | artifact mapping | fallback when absent |
|----------|---------------------------------------------|-----------|------------------|----------------------|
| brainstorm | `superpowers:brainstorming` | wit, brainstorm:0 | `brief.md` | the brainstorm skill's own dialogue |
| research | - (built in; researchers prefer a docs-lookup tool/MCP, e.g. Context7, when the session has one) | wit, research:1c (researcher dispatch) | `research/` notes + the ADR | the `wit-researcher` agent (`agents/wit-researcher.md`) + light web/repo survey; ADR via plan's template |
| plan | `superpowers:writing-plans` | wit, plan:4 (decomposition) | `spec.md` + `tasks.md` (wit format) | plan skill's templates (incl. the ADR template) |
| build | `superpowers:using-git-worktrees`, `test-driven-development`, `subagent-driven-development`, `dispatching-parallel-agents` | wit, build:1 (worktree) and build:2 (waves + runners) | worktree/branch + task commits | build skill + `agents/wit-task-runner.md` |
| ship | `superpowers:verification-before-completion` + `finishing-a-development-branch`; `requesting-code-review` runs **inline in wit-code-checker result mode** (its template passed into the dispatch), logged `review via wit-code-checker + superpowers:requesting-code-review[inline]` | wit, ship:1 (verification), ship:2 (checker dispatch carrying the line review), ship:7 (close-out) | `verification.md` + `PR.md` | ship's verification gate + the checker's built-in line review, logged `review via wit-code-checker (wit line review; superpowers absent)`, ship's variant of the generic fallback line |
| debug (any phase) | `superpowers:systematic-debugging` | wit, the failing phase (e.g. build:3) | `progress.md` log entry | inline hypothesis-and-test |

When you delegate, wit still owns the artifacts: capture the external skill's result into the matching
`.wit/` file (e.g. a superpowers plan -> `tasks.md` in Witloop's format) so the rest of the loop and a resumed
run can read it. The external skill does the thinking; `.wit/` keeps the memory. The same rule applies to any equivalent
skill an environment happens to provide (a code-review or architecture suite, etc.): detect, delegate,
capture into `.wit/`, but wit only *offers to install* things with a known, verifiable slug.

### Who initiates: wit does

During an active wit run (`dev`, `rpa`, or any phase skill in flight), superpowers skills are invoked
**only** at the delegation points in the matrix: wit initiates, the delegate executes. A superpowers
skill description matching the current moment ("before touching code", "starting feature work", "before
merging") is **not** a trigger; self-invocation outside the matrix bypasses wit's phase logging and
artifact contract. If one fires anyway, capture its output into the matching `.wit/` artifact and log the
deviation in progress.md. wit's artifact formats always win: a plan lands in `tasks.md`, never
`docs/plans/`; a review lands in `verification.md`. Phases dispatched as subagents (research
investigation, build tasks, checker passes) are structurally immune (superpowers disables itself inside
subagents), so this rule is what protects the inline phases: the brainstorm dialogue, plan writing, the
design gate, and ship orchestration.

## Frontend work

When `scan` flags a frontend (React/Vue/Svelte/Next, a UI framework in `package.json`, a `components/`
tree), route `[frontend]` tasks to a design skill instead of writing markup blind:

- `anthropics/skills:frontend-design`: primary, for building/refining UI.
- `pbakaus/impeccable` (audit, critique, polish): for tightening an existing UI.
- `leonxlnx/taste-skill`: for visual/design-taste direction.

**Delegation is mandatory when the skill is present**, the same rule as the phase table above. A
`[frontend]` task built without `frontend-design` while it's installed is a defect, not a style choice.
Operationally (the pointer protocol above): pinned runners have no Skill tool, so `build` resolves the
design skill's `SKILL.md` path once per run (progress.md's `## Skill paths (resolved)` block) and each
`[frontend]` dispatch hands the runner that path; the runner Reads it, builds the UI through the guidance,
and logs `frontend via frontend-design` (or `frontend via wit fallback (frontend-design absent)`) to
`progress.md`, and ship's checker (result mode) flags any `[frontend]` UI that shipped blind while the
skill was installed. Backend and glue tasks stay in the normal build loop; a
single feature can mix both (tasks are tagged).

## Backend / Python

The skills directory has no strong Python-backend skill, so wit encodes Python conventions itself in
`constitution.md` defaults (uv - pytest - ruff - mypy - src layout). Treat those as the opinionated
baseline; the constitution is where a project overrides them. Other stacks (Node/Go/Rust/...) are handled
generically from whatever `scan` recorded in `repo-map.md`.

## Sibling commands

`wit:rpa` is another command in this same `wit` plugin: it shipped at v0.7.0 and is a headline feature of
1.0.0, following the same `.wit/` + brainstorm-then-autonomous shape for UiPath RPA workflows, leaning on
UiPath skills the way wit leans on superpowers. The cross-cutting conventions (the `.wit/` spec, the handoff,
integration-detection) stay stable across both, so the muscle memory transfers.
