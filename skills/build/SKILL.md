---
type: Skill
name: build
user-invocable: false
description: >
  Implement an approved plan in an isolated git worktree. Use this skill when the user says "/wi:build",
  "implement the plan", "start building", "execute the tasks", or as the build phase after the design
  gate (runs autonomously).
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
Inputs: `tasks.md`, `spec.md`, `constitution.md`, `repo-map.md`. That list is also the ceiling —
workflow.md's **context budget**: hold `tasks.md` (the active artifact) plus `progress.md` and the
two project files; consult `spec.md` **by section** when a task needs a criterion verbatim. Runners
read everything else — never pre-read a runner's source files "to prepare" a dispatch. On re-entry,
`progress.md`'s ticks + Log are the build's state; don't re-Read prior-phase artifacts to
reconstruct it.

## 1 · Isolate (default: worktree + branch)

Create a dedicated worktree and branch for the feature so the main checkout stays clean and independent features
can run in parallel. Exact commands and the no-git / opt-out variants are in
`${CLAUDE_PLUGIN_ROOT}/skills/build/references/worktrees-and-subagents.md`. **Delegation check:** if
`superpowers:using-git-worktrees` is in your available skills you MUST use it (log `worktree via
superpowers` to progress.md); this reference is the fallback when absent (delegation point — see
integrations.md precedence). Record the worktree path and branch in `progress.md`.

Branch name: `wi/<slug>`. Worktree path: a sibling dir, e.g. `../<repo>-wi-<slug>`.

**The feature dossier rides in with the checkout.** Research committed `.wi/features/<slug>/` on main at
the design gate (`docs(<slug>): feature dossier (design gate)`), and the worktree branches from main — so
the worktree starts with the dossier in place; nothing to move. During build the worktree's copy is
canonical; main's catches up when the branch merges. One fallback for pre-1.3 features: if the dossier is
still untracked in the main checkout, move `.wi/features/<slug>/` into the worktree and commit it as the
branch's **first commit** — `chore(<slug>): feature dossier` (moving, not copying, leaves main's working
tree clean).

## 2 · Execute in parallel waves (the default)

Don't walk the task list one by one — schedule it. The plan's `Depends on` + `Files` fields define a DAG;
run it as wide as the DAG allows. Repeat until every task is ticked:

1. **Compute the ready set:** every unticked task whose dependencies are all done and whose `Files` don't
   overlap those of another ready/running task. File overlap serializes; everything else runs together.
   (`tasks.md`'s Waves section is the plan's precomputed answer — trust it unless reality diverged.)
2. **Dispatch the whole ready set at once** — one fresh `wi-task-runner` (see `agents/wi-task-runner.md`) per
   task, all in the same turn. Each gets exactly what it needs and nothing more: its task block, the
   relevant constitution rules, and the repo commands. Pointers and rules, not pasted file bodies: the
   runner reads its own files (workflow.md's context budget). Fresh agents keep context from rotting across a
   long build; parallel dispatch keeps wall-clock short. **Model per dispatch (tiered model routing):** pass
   each runner the `task-runner` tier from `progress.md`'s `## Model routing (resolved)` block; block
   absent, or `.wi/models.md` changed after its stamp → resolve once now and rewrite the block
   (`${CLAUDE_PLUGIN_ROOT}/references/models.md`'s resolve-once rule). A model that errors as unavailable
   → re-dispatch on `inherit` and note it in `progress.md` (the block stands — the config didn't change).
   No config → inherit, as always.
3. **TDD per task** (per the constitution): failing test first, minimal implementation, green, refactor.
   **Frontend routing is operational, not just asserted** (integrations.md §Frontend work — delegation
   is mandatory when the skill is installed): a task tagged `[frontend]` MUST have its dispatch name the
   available design skill, the runner builds the UI *through it* and reports `frontend via
   frontend-design` (or `frontend via wi fallback (frontend-design absent)`), and you log that line to
   `progress.md` when the report returns (runners never write `progress.md`). Still verify behavior.
   (Ship's checker flags `[frontend]` UI built blind while the skill was installed.)
4. **As each report returns:** check its Verify result and **honor its `Self-Check` line** — tick
   `progress.md` and commit the task (`<type>: <task title>`) only when the runner reports `Self-Check:
   PASS`; a stub or an unmet Verify means the task is *not* done, no matter what the console printed. You
   are the only committer and `progress.md`'s only writer during build, so commits and ticks stay
   serialized and clean. Append the runner's `tokens.md` row the moment its completion notification
   arrives — the figure exists only there; if the file is somehow absent,
   `python ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/check_tokens.py --init .wi/features/<slug>/tokens.md`
   first (python fallback: workflow.md §Script invocation) — per wi-directory.md's **ledger rule** (exact tokens +
   `Duration`, `unavailable` when unobservable, never an estimate). Then recompute the ready set and dispatch
   the next wave without waiting for stragglers it doesn't depend on.
   A runner whose last line is **`## TASK AUTH-GATE`** (status `auth-gate` — a `401` / `run <x> login` /
   missing `ENV` wall) is **not** a failure to retry: don't commit it, record the exact unblock steps in
   `progress.md`, and let the keep-alive loop pause cleanly — it resumes once the human clears the gate.

Escalations — two ready tasks that must touch the same file, or tests that can't run concurrently — are in
the reference (per-task worktrees; serial verify as a last resort). Sequential execution is the fallback
when the DAG is a chain, never the default: an idle DAG is wasted wall-clock.
(`superpowers:dispatching-parallel-agents` codifies the dispatch pattern if installed.)

Two scheduling refinements proven in dry runs: (a) **wave-end gate** — at each wave boundary run the
full lint + test commands once, serially, before dispatching the next wave — output redirected per
workflow.md's output house rule (`… > .wi/features/<slug>/.logs/w<N>-tests.txt 2>&1`), verdict read
from the exit code + `tail -n 30`, failures pulled by grep, never the whole log — and when the
resolved-routing block's cross-provider row says `per-wave` (progress.md; #38's resolve-once rule),
also run **the cross-provider diff review** — the layer on top of wi-code-checker, when configured —
over the wave's diff there (`${CLAUDE_PLUGIN_ROOT}/references/models.md`, same bounded 2-round loop
as at ship); (b) **sole-runner exception** —
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
