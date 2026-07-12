---
type: Bootstrap
title: "Witloop: cross-platform bootstrap"
description: Entry point for non-Claude harnesses; how to read and run Witloop's skills on Codex CLI, Copilot CLI, and Grok Build.
timestamp: 2026-06-09
tags: [witloop, bootstrap, cross-platform, codex, copilot, grok]
---

# Witloop: cross-platform bootstrap

This repository **is** Witloop (plugin id `wit`, formerly `wi`): an opinionated, low-token, spec-driven dev loop. Its capabilities
are delivered as skills under `skills/` (`scan`, `dev`, `research`, `plan`, `build`, `ship`, `brainstorm`,
`rpa`) plus three subagent prompt templates under `agents/` (`wit-code-checker`, `wit-researcher`,
`wit-task-runner`). The `wit-` prefix is a deliberate cross-platform tag (PR #15); on Claude these render
as `wit:wit-<name>`; the stutter is accepted, and the checker stays `wit-code-checker` (skills call it
*the checker*).

## If you are not Claude Code
wit's skills use Claude Code tool names and the `${CLAUDE_PLUGIN_ROOT}` variable. Before following a skill,
read the mapping for your platform and apply it as you go:

- **Codex CLI:** `references/codex-tools.md`
- **GitHub Copilot CLI:** `references/copilot-tools.md`
- **Grok Build:** `references/grok-tools.md`

Key rule: **`${CLAUDE_PLUGIN_ROOT}` is the wit plugin root** (the directory holding `skills/`, `agents/`,
`.claude-plugin/`) whether that's an installed plugin dir (e.g. Copilot's
`~/.copilot/installed-plugins/…`) or a clone of this repo. Resolve every `${CLAUDE_PLUGIN_ROOT}` path
against it.

## Invoking wit
- Start a feature: the `dev` skill (`/wit:dev` on Claude; `/wit-dev` on Copilot / `$wit-dev` on Codex once
  scan's bootstrap has installed the flat aliases into `~/.agents/skills/`; the raw plugin forms
  `/wit dev` and `$dev` always work; or describe the feature and let it auto-trigger).
- Bootstrap a repo first with the `scan` skill.
- Only scan/dev/rpa are user-facing commands. The phase skills (brainstorm, research, plan, build, ship)
  carry `user-invocable: false`; hidden from slash pickers, still invoked by the orchestrating skill and
  by natural language ("ship it").
- Persistence: wit hands off to a keep-alive loop at the end of brainstorm: Claude/Codex use built-in
  `/goal`; Grok Build uses its native (model-judged) `/goal`; Copilot uses Autopilot flags (see the tool
  map). wit runs without it too, just less robustly.
- Superpowers precedence (integrations.md "Who initiates", `skills/research/references/integrations.md`):
  delegation points only, never self-triggered mid-phase; wit's artifact formats always win.

These skills auto-trigger from their `description` fields. When a user's request matches one, use it.
