---
name: plan
description: >
  Turn a decided brief into an executable plan: a spec with testable acceptance criteria, a small ordered
  task list (each task naming its files and its verification), a pitfalls list, and an ADR when a real
  decision was made. Use this skill when the user says "/wi:plan", "plan this out", "write the spec",
  "break this into tasks", or as the plan phase of the research skill (autonomous). Planning only writes inside .wi/ —
  no project code is touched yet. If superpowers:writing-plans is
  installed, use it and capture its output into .wi/ in WI's format.
---

# plan — brief → spec, tasks, pitfalls, ADR

Produce the artifacts that make build mechanical and review easy. Good planning front-loads the thinking
so the build phase is mostly typing, and so a fresh subagent can pick up any single task and execute it
without re-reading the whole world.

Inputs: `.wi/goals/<slug>/brief.md`, the chosen approach in `research/`, `.wi/repo-map.md`, `.wi/constitution.md`.
Outputs: `spec.md`, `tasks.md`, `pitfalls.md` (the approach ADR is usually written in the research phase).
**No source edits — planning only writes inside `.wi/`. Build starts only after the design gate, where the user confirms the architecture + design.**

## Procedure

1. **Write the spec** → `spec.md` (template in `${CLAUDE_PLUGIN_ROOT}/skills/plan/references/spec-template.md`).
   The non-negotiable part is **acceptance criteria that are testable** — each one should map to a check
   build can actually run. If you can't state how you'd verify a criterion, it isn't done being specified.

2. **Decide on an ADR (if research didn't already record it).** If the goal commits to anything hard to reverse — a datastore, a framework, an
   external service, a public API or schema shape, an auth model — record it as the next **ADR-NNNN** in the
   project-wide `.wi/adr/` log using `${CLAUDE_PLUGIN_ROOT}/skills/plan/references/adr-template.md`
   (global numbering; append the index.md row). Trivial
   goals get no ADR — don't manufacture decisions.

3. **List the pitfalls** → `pitfalls.md`. Walk the catalog in
   `${CLAUDE_PLUGIN_ROOT}/skills/plan/references/pitfalls-catalog.md` and keep only the ones that genuinely
   apply to *this* change. For each, note the specific way it could bite here and how a task will prevent
   it. This is cheap foresight that saves an expensive debug later.

   **Consume the research risks — all of them.** Every `Risks / unknowns` line from the researcher
   reports (and any unanswered question left in `research/questions.md`) ends up in exactly one place:
   resolved here (say how), or a `pitfalls.md` entry with the task that prevents/verifies it. A risk line
   that appears in no artifact was dropped — that's a defect, not a judgment call.

4. **Break it into tasks** → `tasks.md` (format below). Aim for small, independently verifiable steps.
   Each task names the files it touches and the exact command/test that proves it. Default to TDD: the
   first task for a piece of behavior writes the failing test. **Delegation check:** if
   `superpowers:writing-plans` is in your available skills you MUST use it for the decomposition —
   capturing the result in this format — and log `plan via superpowers:writing-plans` to progress.md.
   The inline format below is the fallback only when it's absent (log `plan via wi fallback`).

   **Shape the plan for parallelism.** build dispatches every unblocked task concurrently, so the
   dependency graph is the speed limit. Keep `Files` precise and disjoint between tasks wherever possible
   (the scheduler uses them for conflict detection); don't add `Depends on` edges that aren't real; and
   when several tasks share a foundation (a schema, an interface, a fixture), make the foundation its own
   early task so the rest fan out as one wide wave.

   **Docs follow structure.** If a task changes the architecture (new module, dependency, layer, external
   service), the structure docs (`.wi/architecture.md`, `.wi/overview.md`) go stale — ship's docs-sync
   updates them, but when the doc work is substantial give it its own `[docs]` task.

5. **Mirror the task titles** into `progress.md`, set Phase = `design-gate`, and stop. The research skill now presents
   the architecture (ADR) + design (spec) + wave overview to the user for confirmation — no code before
   their explicit go.

## `tasks.md` format

```markdown
# Tasks: <goal title>

> Ordered. Each task is small enough for one focused sitting and ends green.

## Task 1 — <title>   [backend|frontend|infra|test]
- **Files:** <path/a>, <path/b>
- **Do:** <precise change to make>
- **Verify:** <exact test or command that must pass, e.g. `pytest tests/test_auth.py::test_login_ok`>
- **Depends on:** <task ids, or ->

## Task 2 — <title>   [backend]
- **Files:** ...
- **Do:** ...
- **Verify:** ...
- **Depends on:** 1

## Waves  (derived from Depends on + Files — what build runs concurrently)
- Wave 1: tasks 1, 2
- Wave 2: tasks 3, 4, 5
- Wave 3: task 6
```

Tag frontend tasks so build routes them to a design skill. Keep verification concrete — "it works" is not
verification; a named test or command is. A plan whose tasks each end in a runnable check is a plan that
builds and ships without drama.

## Sizing heuristics

- If a task can't name its verification, split it until each piece can.
- If two tasks always change the same file in lockstep, merge them; if two *parallel* tasks merely brush
  the same file, move the shared piece into its own prerequisite task — shared files serialize a wave.
- 3-9 tasks is typical for a feature. Many more usually means the goal is too big — split it
  (one goal = one feature = one PR).
