---
type: Reference
title: "Worktrees & subagent dispatch"
description: "The mechanics behind the build phase's two levers: isolation (worktrees) and delegation (subagents)."
timestamp: 2026-06-09
tags: [build, reference]
---

# Worktrees & subagent dispatch

The mechanics behind the build phase's two levers: isolation (worktrees) and delegation (subagents).

## Git worktrees

A worktree is a second working directory backed by the same repo, checked out to its own branch. It lets
a goal's changes live entirely apart from the main checkout — nothing half-built leaks into the user's
working tree, and two goals can build at once.

### Create (default at build start)

```bash
# from the repo root; <slug> is the goal slug
git worktree add -b wi/<slug> ../<repo>-wi-<slug>
```

Then work happens in `../<repo>-wi-<slug>` on branch `wi/<slug>`. Record both in `progress.md`:

```
- **Worktree:** ../<repo>-wi-<slug>
- **Branch:** wi/<slug>
```

If `.wi/` should be visible inside the worktree (it is, since it's committed), nothing extra is needed.
The goal folder travels with the branch.

### Finish / clean up (done by the ship phase)

```bash
git worktree remove ../<repo>-wi-<slug>     # after the branch is merged/PR'd
git branch -d wi/<slug>                      # if fully merged
```

Never `git worktree remove --force` a tree with uncommitted work without telling the user.

### Variants

- **No git repo:** skip worktrees; work in place but still branch the discipline (small commits once a
  repo exists, or a clear changelog). Note "Worktree: -" in progress.md.
- **User opted for "branch, no worktree":** `git switch -c wi/<slug>` in the current checkout instead of
  adding a worktree. Everything else is identical.
- **Existing worktree for this goal (resume):** reuse it; don't create a second.
- **Restricted filesystems** (network/Windows mounts that forbid rmdir): put the worktree on a local
  path instead — `git worktree add` accepts any absolute path. Symptoms to expect otherwise: pytest
  tmpdir crashes and `git worktree remove` failing. scan's verify-the-commands step is the early warning.
- **Sandboxed / no-branch environments (e.g. Codex sandbox):** if `git rev-parse --git-dir` differs from
  `git rev-parse --git-common-dir` (already in a linked worktree) or `git branch --show-current` is empty
  (detached HEAD), do **not** create a worktree or try to push. Work in place, commit per task, and at
  ship hand the user a suggested branch name, commit message, and PR body to apply via the platform's
  native controls. Note "Worktree: - (sandboxed)" in progress.md.

If `superpowers:using-git-worktrees` is installed, prefer it — it handles edge cases (submodules, dirty
trees) well. This file is the fallback.

## Subagent dispatch

Each task runs in a **fresh** subagent so context doesn't accumulate across a long build. Use the
`task-runner` agent (`agents/task-runner.md`). Scope its prompt tightly — give it the task and its
immediate context, not the whole project.

The dispatch mechanism is platform-specific (see `${CLAUDE_PLUGIN_ROOT}/references/codex-tools.md` /
`copilot-tools.md`): Claude uses the Agent/Task tool, Copilot uses the `task` tool and `/fleet` for waves,
Codex uses `spawn_agent` bounded by `[agents] max_threads`. On every platform, pass the task-runner prompt
**inline** to a generic worker — don't depend on a pre-registered named agent (Codex named-role dispatch
is unreliable across builds).

### Task-runner prompt skeleton

```
You are implementing ONE task from the plan. Stay strictly within its scope.

Environment: file access = <exact tools/paths the runner must use>; do NOT git commit/checkout/reset/
stash — the orchestrator commits. Test execution this wave: <allowed — sole test-runner | authored-not-run
— the orchestrator verifies serially>.

Repo / worktree: <path>   Branch: <wi/slug>
Constitution (obey these rules): <paste the relevant lines from .wi/constitution.md>
Repo commands: test-one = <cmd>, lint = <cmd>, typecheck = <cmd>   (from .wi/repo-map.md)

TASK <n> — <title>   [<tag>]
- Files: <paths>
- Do: <the change>
- Verify: <exact command that must pass>
- Depends on: <already-done task ids>

Process:
1. If this is new behavior, write the failing test FIRST and run it; confirm it fails for the right reason.
2. Implement the minimum to make Verify pass. Watch it pass.
3. Run lint + typecheck; fix what you introduced.
4. Refactor if needed; keep the test green.
Report back: files changed, the Verify command + its result, and anything that surprised you or suggests
the plan needs amending. Keep the report under ~15 lines. Do not touch files outside this task.
```

The subagent returns that short report; you tick `progress.md`, commit, and move on. You never pull the
subagent's full transcript into your context — the report is enough.

### Parallel dispatch (the default)

build runs in waves: every task whose dependencies are met and whose `Files` are disjoint from the other
ready tasks is dispatched concurrently, in the same turn. Reports are reconciled as they return; the
orchestrator is the only committer, so parallel edits in one worktree stay safe — runners touch disjoint
files, commits land serially. `superpowers:dispatching-parallel-agents` codifies the pattern if installed.

The escalation ladder when parallel work would collide:

1. **Disjoint files, shared goal worktree** (default) — cheapest: no extra environment setup, full speed
   for almost every wave.
2. **Per-task ephemeral worktree** — when two ready tasks genuinely must touch the same file, or a task's
   tests interfere with siblings (fixed port, shared db file, global fixture):
   `git worktree add -b wi/<slug>-t<N> ../<repo>-wi-<slug>-t<N> wi/<slug>`, run the task there, merge back
   into `wi/<slug>` in dependency order, then remove the worktree. Mind the cost — a fresh worktree often
   needs its own env (`uv sync` / `npm install`), so escalate when the conflict is real, not routinely.
3. **Serialize** — last resort, when the DAG is a chain or merge-back conflicts would outweigh the win.

Test concurrency: separate processes running separate unit tests are usually fine. If `repo-map.md` flags
the suite as **not parallel-safe** (shared on-disk DB, fixed ports, order-dependent tests), keep the
*implementation* parallel but run the wave's `Verify` commands serially as reports return — or give the
colliding tasks their own worktrees. Exception: a wave whose ONLY test-executing task runs alone keeps
full TDD execution in-runner.

## Commit hygiene during build

- One task → one commit. Subject: `<type>: <task title>` (`feat`, `fix`, `refactor`, `test`, `docs`).
- Keep generated files, large blobs, and secrets out. If `scan` found a `.gitignore`, trust it; if a new
  artifact type appears, add it.
- Don't squash yet — small commits make the ship-phase review legible. Squashing (if wanted) happens at PR.
