---
type: Skill
name: build
user-invocable: false
description: >
  Implement an approved plan in an isolated git worktree. Use this skill when the user says "/wit:build",
  "implement the plan", "start building", "execute the tasks", or as the build phase after the design
  gate (runs autonomously).
---

# build: execute the plan, in isolation, task by task

Two levers: **isolate** the work in its own worktree, and **delegate** each task to a fresh subagent
that returns only a summary. You orchestrate; you do not implement every task in this context.

Design rationale for this skill lives in the wit repo's `docs/design-notes/build.md` (maintainer doc,
never loaded at runtime).

Precondition: a plan exists (`tasks.md`) **and the design gate passed**: approved interactively or
`auto-approve (--auto)`, recorded in `progress.md`. Refuse to build without it; route to the research
skill instead. First act once engaged: append `build engine engaged (wit <version>)` to progress.md's
Log, <version> read from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`, never guessed. From here
build runs autonomously.
Inputs: `tasks.md`, `spec.md`, `constitution.md`, `repo-map.md`. That list is also the ceiling
(workflow.md's **context budget**): hold `tasks.md` (the active artifact) plus `progress.md` and the
two project files; consult `spec.md` **by section** when a task needs a criterion verbatim. Runners
read everything else; never pre-read a runner's source files "to prepare" a dispatch. On re-entry,
`progress.md`'s ticks + Log are the build's state; don't re-Read prior-phase artifacts to
reconstruct it. Reason lean throughout (the **compact-reasoning rule**,
`${CLAUDE_PLUGIN_ROOT}/references/compact-reasoning.md`): scheduling, dispatch, and report handling get
essential, decision-bearing thoughts only, never a re-derivation of what `tasks.md`/`progress.md`
already settle.

## 1 · Isolate (default: worktree + branch)

Create a dedicated worktree and branch for the feature. Exact commands and the no-git / opt-out
variants: `${CLAUDE_PLUGIN_ROOT}/skills/build/references/worktrees-and-subagents.md`. **Delegation
check:** if `superpowers:using-git-worktrees` is in your available skills you MUST use it (log
`worktree via superpowers` to progress.md); this reference is the fallback when absent (delegation
point; precedence: integrations.md). Record the worktree path and branch in `progress.md`.

Branch name: `wit/<slug>`. Worktree path: a sibling dir, e.g. `../<repo>-wit-<slug>`.

**The feature dossier rides in with the checkout.** Research committed `.wit/features/<slug>/` on main
at the design gate (`docs(<slug>): feature dossier (design gate)`); the worktree branches from main, so
the dossier is in place, nothing to move. During build the worktree's copy is canonical.

## 2 · Execute in parallel waves (the default)

Don't walk the task list one by one; schedule it. The plan's `Depends on` + `Files` fields define a DAG;
run it as wide as the DAG allows. Repeat until every task is ticked:

1. **Compute the ready set:** every unticked task whose dependencies are all done and whose `Files` don't
   overlap those of another ready/running task. File overlap serializes; everything else runs together.
   (`tasks.md`'s Waves section is the plan's precomputed answer; trust it unless reality diverged.)
2. **Dispatch the whole ready set at once**: one fresh `wit-task-runner` (`agents/wit-task-runner.md`) per
   task, all in the same turn. Each gets its task block, the relevant constitution rules, and the repo
   commands, nothing more. Pointers and rules, not pasted file bodies: the runner reads its own files
   (workflow.md's context budget). **Model per dispatch (tiered model routing):** pass each runner the
   `task-runner` tier from `progress.md`'s `## Model routing (resolved)` block, resolving or refreshing it
   and handling an unavailable model per `${CLAUDE_PLUGIN_ROOT}/references/models.md`'s resolve-once rule.
3. **TDD per task** (per the constitution): failing test first, minimal implementation, green, refactor.
   **Skill-mediated routing is operational, not just asserted** (integrations.md: delegation is mandatory
   when installed). Pinned runners have no Skill tool, so for a task tagged for a skill-mediated
   capability (today `[frontend]` → a design skill) resolve the mapped skill's `SKILL.md` absolute path
   **once per run** into `progress.md`'s `## Skill paths (resolved)` block (block absent, or the `.wit/`
   skill set changed after its stamp → resolve now, same staleness rule as the routing block;
   capability→skill map is integrations.md; a run with no tagged task resolves nothing). The dispatch then
   names the skill and hands the runner that path; the runner Reads it and does that aspect *through* the
   guidance and reports `<capability> via <skill>` (a frontend task: `frontend via frontend-design`, or
   `frontend via wit fallback (frontend-design absent)` when the path is unresolvable), and you log that
   line to `progress.md` when the report returns (runners never write `progress.md`). Still verify
   behavior.
4. **As each report returns:** check its Verify result and **honor its `Self-Check` line**: tick
   `progress.md` and commit the task (`<type>: <task title>`) only when the runner reports
   `Self-Check: PASS`; a stub or an unmet Verify means the task is *not* done, no matter what the
   console printed. You are the only committer and `progress.md`'s only writer during build. Append the
   runner's `tokens.md` row the moment its completion notification arrives; if the file is absent,
   `python ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/check_tokens.py --init .wit/features/<slug>/tokens.md`
   first (python fallback: workflow.md "Script invocation"), per wit-directory.md's **ledger rule** (exact
   tokens + `Duration`, `unavailable` when unobservable, never an estimate). Then recompute the ready set
   and dispatch the next wave without waiting for stragglers it doesn't depend on.
   A runner whose last line is **`## TASK AUTH-GATE`** (status `auth-gate`: a `401` / `run <x> login` /
   missing `ENV` wall) is **not** a failure to retry: don't commit it, record the exact unblock steps in
   `progress.md`, and let the keep-alive loop pause cleanly; it resumes once the human clears the gate.

Escalations (two ready tasks that must touch the same file, or tests that can't run concurrently) are in
the reference (per-task worktrees; serial verify as a last resort). Sequential execution is the fallback
when the DAG is a chain, never the default.
(`superpowers:dispatching-parallel-agents` codifies the dispatch pattern if installed.)

Two scheduling refinements: (a) **wave-end gate**: at each wave boundary run the full lint + test
commands once, serially, before dispatching the next wave; output redirected per workflow.md's
output house rule (`… > .wit/features/<slug>/.logs/w<N>-tests.txt 2>&1`), verdict from the exit code +
`tail -n 30`, failures pulled by grep, never the whole log. When the resolved-routing block's
cross-provider row says `per-wave` (progress.md; #38's resolve-once rule), also run **the
cross-provider diff review** (the layer on top of wit-code-checker) over the wave's diff there
(`${CLAUDE_PLUGIN_ROOT}/references/models.md`, same bounded 2-round loop as at ship).
(b) **sole-runner exception**: when exactly one task in a wave executes tests (the rest are docs/config),
that runner keeps full TDD (watch-fail / watch-pass); only multi-test waves switch to authored-not-run +
orchestrator serial Verify.

## 3 · When a task fails

Don't thrash. Give the subagent a bounded number of attempts (≈3) to get its task green. If it's still
stuck, switch to a debugging pass (`superpowers:systematic-debugging` if installed): reproduce,
isolate, hypothesize, test. If the failure reveals the **plan** was wrong, stop and amend: append a stamped Reflection line to
`progress.md` (`- <ts> **Reflection** <check that failed>: <what went wrong, one clause> - earlier catch: plan`),
update `spec.md`/`tasks.md`, and continue; never let code silently drift from the spec.

## 4 · Keep scope honest

Only touch files the tasks name. If you discover necessary work the plan missed, don't absorb it
silently: in-scope gaps become a new task in `tasks.md` (noted in `progress.md`); out-of-scope ideas go
to `.wit/roadmap.md`.
