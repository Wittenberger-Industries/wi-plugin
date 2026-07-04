---
type: Bootstrap
title: wi — cross-platform bootstrap
description: Entry point for non-Claude harnesses — how to read and run wi's skills on Codex CLI and Copilot CLI.
timestamp: 2026-06-09
tags: [wi, bootstrap, cross-platform, codex, copilot]
---

# wi — cross-platform bootstrap

This repository **is** the wi plugin: an opinionated, low-token, spec-driven dev loop. Its capabilities
are delivered as skills under `skills/` (`scan`, `dev`, `research`, `plan`, `build`, `ship`, `brainstorm`,
`rpa`) plus three subagent prompt templates under `agents/` (`wi-code-checker`, `wi-researcher`,
`wi-task-runner`). The `wi-` prefix is a deliberate cross-platform tag (PR #15); on Claude these render
as `wi:wi-<name>` — the stutter is accepted, and the checker stays `wi-code-checker` (skills call it
*the checker*).

## If you are not Claude Code
wi's skills use Claude Code tool names and the `${CLAUDE_PLUGIN_ROOT}` variable. Before following a skill,
read the mapping for your platform and apply it as you go:

- **Codex CLI:** `references/codex-tools.md`
- **GitHub Copilot CLI:** `references/copilot-tools.md`

Key rule: **`${CLAUDE_PLUGIN_ROOT}` is the wi plugin root** — the directory holding `skills/`, `agents/`,
`.claude-plugin/` — whether that's an installed plugin dir (e.g. Copilot's
`~/.copilot/installed-plugins/…`) or a clone of this repo. Resolve every `${CLAUDE_PLUGIN_ROOT}` path
against it.

## Invoking wi
- Start a feature: the `dev` skill (`/wi:dev` on Claude; `/wi-dev` on Copilot / `$wi-dev` on Codex once
  scan's bootstrap has installed the flat aliases into `~/.agents/skills/` — the raw plugin forms
  `/wi dev` and `$dev` always work; or describe the feature and let it auto-trigger).
- Bootstrap a repo first with the `scan` skill.
- Only scan/dev/rpa are user-facing commands. The phase skills (brainstorm, research, plan, build, ship)
  carry `user-invocable: false` — hidden from slash pickers, still invoked by the orchestrating skill and
  by natural language ("ship it").
- Persistence: wi hands off to a keep-alive loop at the end of brainstorm — Claude/Codex use built-in
  `/goal`; Copilot uses Autopilot flags (see the tool map). wi runs without it too, just less robustly.
- Superpowers precedence: during a run, superpowers skills fire only at wi's delegation points
  (`skills/research/references/integrations.md`) — never self-triggered mid-phase; wi's artifact formats
  always win.

These skills auto-trigger from their `description` fields. When a user's request matches one, use it.
