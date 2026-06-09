---
name: build
description: >
  Implement an approved plan in an isolated git worktree, one task at a time, each driven by a fresh
  subagent under TDD. Use this skill when the user says "/wi:build", "implement the plan", "start building",
  "execute the tasks", or as the build phase after the design gate (runs autonomously). It creates a dedicated
  worktree + branch, runs each task's failing-test-first cycle, commits per task, ticks progress.md, and
  routes frontend tasks to a design skill. Soft-integrates superpowers' using-git-worktrees,
  subagent-driven-development, and test-driven-development when installed.
---

# build — execute the plan, in isolation, task by task

Build is where wi spends real tokens, so it's where the discipline matters most. Two ideas keep it
affordable and safe: **isolate** the work in its own worktree, and **delegate** each task to a fresh
subagent that returns only a summary. You orchestrate; you do not implement every task in this context.

Precondition: a plan exists (`tasks.md`) **and the design gate passed** — approved interactively or
`auto-approve (--auto)`, recorded in `progress.md`. Refuse to build without it; route to the research
skill instead. First act once engaged: append `build engine engaged (wi <version>)` to progress.md's Log — read
<version> from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`, don't guess it — so the invocation is
auditable. From here build runs autonomously; the gate was the last question.
Inputs: `tasks.md`, `spec.md`, `constitution.md`, `repo-map.md`.

## 1 · Isolate (default: worktree + branch)

Create a dedicated worktree and branch for the goal so the main checkout stays clean and independent goals
can run in parallel. Exact commands and the no-git / opt-out variants are in
`${CLAUDE_PLUGIN_ROOT}/skills/build/references/worktrees-and-subagents.md`. **Delegation check:** if
`superpowers:using-git-worktrees` is in your available skills you MUST use it (log `worktree via
superpowers` to progress.md); this reference is the fallback when absent. Record the worktree path and
branch in `progress.md`.

Branch name: `wi/<slug>`. Worktree path: a sibling dir, e.g. `../<repo>-wi-<slug>`.

## 2 · Execute in parallel waves (the default)

Don't walk the task list one by one — schedule it. The plan's `Depends on` + `Files` fields define a DAG;
run it as wide as the DAG allows. Repeat until every task is ticked:

1. **Compute the ready set:** every unticked task whose dependencies are all done and whose `Files` don't
   overlap those of another ready/running task. File overlap serializes; everything else runs together.
   (`tasks.md`'s Waves section is the plan's precomputed answer — trust it unless reality diverged.)
2. **Dispatch the whole ready set at once** — one fresh `task-runner` (see `agents/task-runner.md`) per
   task, all in the same turn. Each gets exactly what it needs and nothing more: its task block, the
   relevant constitution rules, and the repo commands. Fresh agents keep context from rotting across a
   long build; parallel dispatch keeps wall-clock short.
3. **TDD per task** (per the constitution): failing test first, minimal implementation, green, refactor.
   `[frontend]` tasks MUST route through `frontend-design` when it's installed (log it; build markup blind
   only when it's absent) and still verify behavior.
4. **As each report returns:** check its Verify result, commit that task (`<type>: <task title>`) — you
   are the only committer, so commits stay serialized and clean — tick `progress.md`, append the runner's
   token count to the goal's `tokens.md` (it's in the task-completion notification and is NOT retrievable
   later), then recompute the ready set and dispatch the next wave without waiting for stragglers it
   doesn't depend on.

Escalations — two ready tasks that must touch the same file, or tests that can't run concurrently — are in
the reference (per-task worktrees; serial verify as a last resort). Sequential execution is the fallback
when the DAG is a chain, never the default: an idle DAG is wasted wall-clock.
(`superpowers:dispatching-parallel-agents` codifies the dispatch pattern if installed.)

Two scheduling refinements proven in dry runs: (a) **wave-end gate** — at each wave boundary run the full
lint + test commands once, serially, before dispatching the next wave; (b) **sole-runner exception** —
when exactly one task in a wave executes tests (the rest are docs/config), that runner keeps full TDD
(watch-fail / watch-pass); only multi-test waves switch to authored-not-run + orchestrator serial Verify.

## 3 · When a task fails

Don't thrash. Give the subagent a bounded number of attempts (≈3) to get its task green. If it's still
stuck, switch to a debugging pass (`superpowers:systematic-debugging` if installed): reproduce,
isolate, hypothesize, test. If the failure reveals the **plan** was wrong, stop and amend: note it in
`progress.md`, update `spec.md`/`tasks.md`, and continue — never let code silently drift from the spec.

## 4 · Keep scope honest

Only touch files the tasks name. If you disc