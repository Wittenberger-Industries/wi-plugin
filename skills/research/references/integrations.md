# Integrations — borrow, don't reinvent

wi is deliberately thin. Where a good skill already exists, wi **detects it and hands off**, adding only
its own opinions (the `.wi/` artifacts, the brainstorm-as-gate, the worktree discipline, the autonomous
pipeline). When nothing is installed, wi falls back to a light built-in version so it always works
standalone. `scan` offers to install the recommended set on first run (see the scan skill's
`plugin-bootstrap.md`).

## How to detect an available skill

A skill is "available" if it appears in the session's skills list, or its directory exists under a known
plugin/skills path. If unsure, use `find-skills` (vercel-labs/skills) to discover/install one, or fall
back. Never hard-fail because an optional skill is missing — degrade gracefully and say which mode you're in.

**Delegation is mandatory when the skill is present.** The fallback column applies only when it is
absent. Every delegating phase logs its mode to progress.md — `<phase> via <skill>` or `<phase> via wi
fallback (<skill> absent)` — so a run's delegation behavior is auditable afterwards. Running a fallback
while the preferred skill is installed is a defect.

## Phase -> preferred skill -> fallback

| wi phase | REQUIRED when installed | Fallback (only when absent) |
|----------|---------------------|----------------------|
| brainstorm | `superpowers:brainstorming` | the brainstorm skill's own dialogue |
| research | — (built in; researchers prefer a docs-lookup tool/MCP, e.g. Context7, when the session has one) | the `researcher` agent + light web/repo survey; ADR via plan's template |
| plan | `superpowers:writing-plans` | plan skill's templates (incl. the ADR template) |
| build | `superpowers:subagent-driven-development`, `using-git-worktrees`, `test-driven-development`, `dispatching-parallel-agents` | build skill + `agents/task-runner.md` |
| ship | `superpowers:requesting-code-review` + `verification-before-completion` + `finishing-a-development-branch` | ship skill's verification gate |
| debug (any phase) | `superpowers:systematic-debugging` | inline hypothesis-and-test |

When you delegate, wi still owns the artifacts: capture the external skill's result into the matching
`.wi/` file (e.g. a superpowers plan -> `tasks.md` in WI's format) so the rest of the loop and a resumed
run can read it. The external skill does the thinking; `.wi/` keeps the memory. The same rule applies to any equivalent
skill an environment happens to provide (a code-review or architecture suite, etc.): detect, delegate,
capture into `.wi/` — but wi only *offers to install* things with a known, verifiable slug.

## Frontend work

When `scan` flags a frontend (React/Vue/Svelte/Next, a UI framework in `package.json`, a `components/`
tree), route `[frontend]` tasks to a design skill instead of writing markup blind:

- `anthropics/skills:frontend-design` — primary, for building/refining UI.
- `pbakaus/impeccable` (audit, critique, polish) — for tightening an existing UI.
- `leonxlnx/taste-skill` — for visual/design-taste direction.

Backend and glue tasks stay in the normal build loop; a single goal can mix both (tasks are tagged).

## Backend / Python

The skills directory has no strong Python-backend skill, so wi encodes Python conventions itself in
`constitution.md` defaults (uv - pytest - ruff - mypy - src layout). Treat those as the opinionated
baseline; the constitution is where a project overrides them. Other stacks (Node/Go/Rust/...) are handled
generically from whatever `scan` recorded in `repo-map.md`.

## Sibling commands

`wi:rpa` (planned) will be another command in this same `wi` plugin, following the same `.wi/` +
brainstorm-then-autonomous shape for UiPath RPA workflows — leaning on UiPath skills the way wi leans
on superpowers. Keep the cross-cutting conventions (the `.wi/` spec, the handoff, integration-detection)
stable so the muscle memory transfers.
