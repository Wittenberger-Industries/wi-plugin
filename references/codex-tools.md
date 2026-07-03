---
type: Reference
title: Codex CLI — tool & capability mapping for wi
description: Claude Code → Codex CLI tool-name and capability equivalents used when running wi on Codex.
timestamp: 2026-06-09
tags: [codex, tools, portability, reference]
---

# Codex CLI — tool & capability mapping for wi

wi's skills are written with Claude Code names. On Codex CLI, use these equivalents.

## ${CLAUDE_PLUGIN_ROOT}
`${CLAUDE_PLUGIN_ROOT}` is the **wi plugin root** — the directory holding `skills/`, `agents/`, and
`.claude-plugin/`. Codex sets `CLAUDE_PLUGIN_ROOT` (and `PLUGIN_ROOT`) for compatibility, so most refs
resolve as-is. If a ref doesn't resolve in a skill context, treat it as the installed wi plugin dir and
read the file by its path under that root. This covers cross-skill refs such as `ship` reading
`${CLAUDE_PLUGIN_ROOT}/skills/scan/scripts/check_mermaid.py`.

## Tools
| wi/skill says | Codex equivalent |
|---|---|
| Read / Write / Edit a file | native file tools / `apply_patch` |
| Bash / run a command | `shell` |
| Grep / Glob | native search (`shell` with `rg`/`grep`/`find`) |
| dispatch a subagent / task-runner | `spawn_agent` (parallel: multiple `spawn_agent`, or `spawn_agents_on_csv`) |
| parallel waves | `spawn_agent` bounded by `[agents] max_threads` (default 6); inline the task-runner/researcher prompt — do not rely on named-role dispatch |
| TodoWrite | `update_plan` |
| WebFetch / WebSearch | `web_search` |
| invoke a wi skill | skills load natively — `$skill-name` or `/skills` (entry points also as `$wi-scan`/`$wi-dev`/`$wi-rpa` once scan's bootstrap installs the flat aliases to `~/.agents/skills/`); just follow its instructions |

## /goal keep-alive
Codex has a native `/goal`. Use the same condition line wi prints. For non-interactive runs, `codex exec`
with `--ask-for-approval never --sandbox workspace-write`.

## Worktrees
If the sandbox blocks branch/push (detached HEAD / externally managed worktree), do **not** fail: commit
all work in place and hand the user a suggested branch name, commit message, and PR body to apply via the
app's native controls. Detect with read-only `git rev-parse --git-dir`/`--git-common-dir` and
`git branch --show-current` before creating a worktree.

## Subagent caveat
Repo-local custom-agent *roles* are not reliably selectable by name across Codex builds. wi's build/research
fan-out passes the agent prompt inline to a generic worker, so this caveat does not block wi.
