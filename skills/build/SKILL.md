---
type: Skill
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
2. **Dispatch the whole ready set at once** — one fresh `wi-task-runner` (see `agents/wi-task-runner.md`) per
   task, all in the same turn. Each gets exactly what it needs and nothing more: its task block, the
   relevant constitution rules, and the repo commands. Fresh agents keep context from rotting across a
   long build; parallel dispatch keeps wall-clock short.
3. **TDD per task** (per the constitution): failing test first, minimal implementation, green, refactor.
   **Frontend routing is operational, not just asserted:** when a task is tagged `[frontend]`, the dispatch
   MUST name the available design skill in that runner's charter — detect `frontend-design` (per
   `integrations.md`) and tell the runner to build/refine the UI *through it*, not blind. The runner enforces
   this (`agents/wi-task-runner.md`) and logs `frontend via frontend-design` (or `frontend via wi fallback
   (frontend-design absent)`) to `progress.md`; markup is authored by hand only when no design skill is
   installed. Still verify behavior. (A `[frontend]` task built blind while `frontend-design` was installed
   is a defect ship's checker flags.)
4. **As each report returns:** check its Verify result and **honor its `Self-Check` line** — tick
   `progress.md` and commit the task (`<type>: <task title>`) only when the runner reports `Self-Check:
   PASS`; a stub or an unmet Verify means the task is *not* done, no matter what the console printed. You
   are the only committer, so commits stay serialized and clean. Append the runner's token count as a row to
   the goal's `tokens.md` (it's in the task-completion notification and is NOT retrievable later; if the file
   is somehow absent, `python3 ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/check_tokens.py --init .wi/goals/<slug>/tokens.md`
   first), then recompute the ready set and dispatch the next wave without waiting for stragglers it doesn't depend on.
   A runner that returns **`auth-gate`** (a `401` / `run <x> login` / missing `ENV` wall) is **not** a
   failure to retry: don't commit it, record the exact unblock steps in `progress.md`, and let the
   keep-alive loop pause cleanly — it resumes once the human clears the gate.

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

Only touch files the tasks name. If you discover necessary work the plan missed, don't absorb it
silently: in-scope gaps become a new task in `tasks.md` (noted in `progress.md`); out-of-scope ideas go
to `.wi/roadmap.md`. Scope creep hidden inside a task is how builds drift from their spec.
