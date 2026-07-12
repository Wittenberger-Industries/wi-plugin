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
a feature's changes live entirely apart from the main checkout: nothing half-built leaks into the user's
working tree, and two features can build at once.

### Create (default at build start)

```bash
# from the repo root; <slug> is the feature slug
git worktree add -b wit/<slug> ../<repo>-wit-<slug>
```

Then work happens in `../<repo>-wit-<slug>` on branch `wit/<slug>`. Record both in `progress.md`:

```
- **Worktree:** ../<repo>-wit-<slug>
- **Branch:** wit/<slug>
```

The feature folder arrives with the checkout: research commits the dossier on main at the design gate
(`docs(<slug>): feature dossier (design gate)`), and the worktree branches from main; `.wit/features/<slug>/`
is in place from the first command. During build the worktree's copy is canonical, and main's copy catches
up when the branch merges. Resume-safe: a dossier already present in the worktree needs nothing.

### Finish / clean up (done by the ship phase)

```bash
git worktree remove ../<repo>-wit-<slug>     # only after ship:8's remote-checks gate lands (green / none / user-accepted red)
git branch -d wit/<slug>                      # if fully merged
```

Never `git worktree remove --force` a tree with uncommitted work without telling the user.

### Variants

- **No git repo:** skip worktrees; work in place but still branch the discipline (small commits once a
  repo exists, or a clear changelog). Note "Worktree: -" in progress.md.
- **User opted for "branch, no worktree":** `git switch -c wit/<slug>` in the current checkout instead of
  adding a worktree. Everything else is identical.
- **Existing worktree for this feature (resume):** reuse it; don't create a second.
- **Restricted filesystems** (network/Windows mounts that forbid rmdir): put the worktree on a local
  path instead: `git worktree add` accepts any absolute path. Symptoms to expect otherwise: pytest
  tmpdir crashes and `git worktree remove` failing. scan's verify-the-commands step is the early warning.
- **Sandboxed / no-branch environments (e.g. Codex sandbox):** if `git rev-parse --git-dir` differs from
  `git rev-parse --git-common-dir` (already in a linked worktree) or `git branch --show-current` is empty
  (detached HEAD), do **not** create a worktree or try to push. Work in place, commit per task, and at
  ship hand the user a suggested branch name, commit message, and PR body to apply via the platform's
  native controls. Note "Worktree: - (sandboxed)" in progress.md.
- **Grok Build session worktrees:** Grok's own `grok -w` session worktree is an optional outer shell;
  keep the wit feature worktree canonical and do **not** nest it inside a session worktree. A Grok session
  workspace is a standalone **copy** of the repo, so the git signals above do not fire: detect it by cwd
  under `~/.grok/worktrees/` and then follow this same sandboxed variant
  (`${CLAUDE_PLUGIN_ROOT}/references/grok-tools.md`). Subagent `isolation: worktree` (`spawn_subagent`)
  stays the level-2 escalate only, exactly like the ladder below.

If `superpowers:using-git-worktrees` is installed, prefer it; it handles edge cases (submodules, dirty
trees) well. This file is the fallback.

## Subagent dispatch

Each task runs in a **fresh** subagent so context doesn't accumulate across a long build. Use the
`wit-task-runner` agent (`agents/wit-task-runner.md`). Scope its prompt tightly: give it the task and its
immediate context, not the whole project.

The dispatch mechanism is platform-specific (see `${CLAUDE_PLUGIN_ROOT}/references/codex-tools.md` /
`copilot-tools.md` / `grok-tools.md`): Claude uses the Agent/Task tool, Copilot uses the `task` tool and
`/fleet` for waves, Codex uses `spawn_agent` bounded by `[agents] max_threads`, Grok Build uses
`spawn_subagent` with the built-in `general-purpose` type and the runner prompt inline. The prompt
**content** is inline on every
platform: the skeleton below gives each runner its task block + context in full. The dispatch *target*
differs: on Claude Code, dispatch the **registered `wit-task-runner` agent** (build:2's instruction: the
plugin registers it, and tiered model routing rides the dispatch); only on platforms without reliable
named-agent registration (Codex: named-role dispatch is unreliable across builds there) pass the prompt
to a generic worker carrying the `agents/wit-task-runner.md` contract inline.

### Task-runner prompt skeleton

```
You are implementing ONE task from the plan. Stay strictly within its scope.

Environment: file access = <exact tools/paths the runner must use>; do NOT git commit/checkout/reset/
stash and do NOT write progress.md; the orchestrator commits and ticks. Test execution this wave:
<allowed (sole test-runner) | authored-not-run (the orchestrator verifies serially)>.

Repo / worktree: <path>   Branch: <wit/slug>
Constitution (obey these rules): <paste the relevant lines from .wit/constitution.md>
Repo commands: test-one = <cmd>, lint = <cmd>, typecheck = <cmd>   (from .wit/repo-map.md)

TASK <n>: <title>   [<tag>]
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

The subagent returns that short report; you tick `progress.md` (you are its single writer during build:
runners report, they never write it), commit, and move on. You never pull the
subagent's full transcript into your context; the report is enough.

### Parallel dispatch (the default)

build runs in waves: every task whose dependencies are met and whose `Files` are disjoint from the other
ready tasks is dispatched concurrently, in the same turn. Reports are reconciled as they return; the
orchestrator is the only committer, so parallel edits in one worktree stay safe: runners touch disjoint
files, commits land serially. The git landmines that bind runners sharing a worktree (the no-stash /
no-clean / no-reset list) are pinned once in `agents/wit-task-runner.md`, echoed by the prompt skeleton
above. `superpowers:dispatching-parallel-agents` codifies the pattern if installed.

The escalation ladder when parallel work would collide:

1. **Disjoint files, shared feature worktree** (default); cheapest: no extra environment setup, full speed
   for almost every wave.
2. **Per-task ephemeral worktree**: when two ready tasks genuinely must touch the same file, or a task's
   tests interfere with siblings (fixed port, shared db file, global fixture):
   `git worktree add -b wit/<slug>-t<N> ../<repo>-wit-<slug>-t<N> wit/<slug>`, run the task there, merge back
   into `wit/<slug>` in dependency order, then remove the worktree. Mind the cost: a fresh worktree often
   needs its own env (`uv sync` / `npm install`), so escalate when the conflict is real, not routinely.
3. **Serialize**: last resort, when the DAG is a chain or merge-back conflicts would outweigh the win.

Test concurrency: separate processes running separate unit tests are usually fine. If `repo-map.md` flags
the suite as **not parallel-safe** (shared on-disk DB, fixed ports, order-dependent tests), keep the
*implementation* parallel but run the wave's `Verify` commands serially as reports return, or give the
colliding tasks their own worktrees. Exception: a wave whose ONLY test-executing task runs alone keeps
full TDD execution in-runner.

## Commit hygiene during build

- One task → one commit. Subject: `<type>: <task title>` (`feat`, `fix`, `refactor`, `test`, `docs`).
- Keep generated files, large blobs, and secrets out. If `scan` found a `.gitignore`, trust it; if a new
  artifact type appears, add it.
- Don't squash yet: small commits make the ship-phase review legible. Squashing (if wanted) happens at PR.
