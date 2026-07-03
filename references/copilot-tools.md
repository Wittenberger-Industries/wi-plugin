---
type: Reference
title: Copilot CLI — tool & capability mapping for wi
description: Claude Code → GitHub Copilot CLI tool-name and capability equivalents used when running wi on Copilot.
timestamp: 2026-06-09
tags: [copilot, tools, portability, reference]
---

# Copilot CLI — tool & capability mapping for wi

wi's skills are written with Claude Code names. On Copilot CLI, use these equivalents.

## ${CLAUDE_PLUGIN_ROOT}
Copilot has no plugin-root variable. `${CLAUDE_PLUGIN_ROOT}` means the **wi plugin root** — the directory
holding `skills/`, `agents/`, and `.claude-plugin/`. Where that root lives depends on how wi was installed:

- **Preferred — plugin install:** `copilot plugin install Wittenberger-Industries/wi-plugin` (Copilot CLI
  reads `.claude-plugin/plugin.json` and defaults to `skills/` + `agents/`). The whole repo lands under
  `~/.copilot/installed-plugins/…` — that installed directory is the wi root. Update with
  `copilot plugin update wi`.
- **Fallback — clone:** `git clone` + `/skills add <repo>/skills` (older CLI versions). The clone is the
  wi root.

Either way, install wi **whole** and resolve every `${CLAUDE_PLUGIN_ROOT}` path against that root. This is
why per-skill `gh skill install` is discouraged: cross-skill refs such as `ship` reading
`${CLAUDE_PLUGIN_ROOT}/skills/scan/scripts/check_mermaid.py`, and the plugin-version read from
`.claude-plugin/plugin.json`, need the shared root.

## Tools
| wi/skill says | Copilot equivalent |
|---|---|
| Read | `view` |
| Write | `create` |
| Edit | `edit` / `apply_patch` |
| Bash | `bash` |
| Grep / Glob | `grep` / `glob` |
| dispatch a subagent / task-runner | `task` tool (custom agent) |
| parallel waves | `/fleet` (monitor with `/tasks`) |
| WebFetch | `web_fetch` |
| WebSearch | no equivalent — use `web_fetch` with a search URL |
| invoke a wi skill | skills load natively — `/wi <skill>` (plugin), `/wi-scan`/`/wi-dev`/`/wi-rpa` (flat aliases), or auto-trigger by description |

## /goal keep-alive
Copilot has no predicate `/goal`. Use **Autopilot**: relaunch with the completion condition in the prompt —
`copilot --autopilot --max-autopilot-continues <N> --no-ask-user --allow-all -p "<prompt incl. done-condition>"`.
Completion is model-judged and continuation-capped, not a hard predicate. `--no-ask-user --allow-all` runs
fully unattended (prompts suppressed, all tools/paths granted); drop `--allow-all` to keep risky-action
confirmations.

## Command namespace
`/wi:dev` etc. do not exist. Plugin-installed skills are auto-prefixed with the plugin name — wi's entry
points invoke as `/wi scan`, `/wi dev`, `/wi rpa` (the prefix is Copilot's, not configurable; a separator
inside a skill `name` makes it silently fail to load). For a one-token form, scan's bootstrap offers to
copy the flat aliases from `references/skill-aliases/` into `~/.agents/skills/`, giving `/wi-scan`,
`/wi-dev`, `/wi-rpa` (flat skills carry no prefix). The clone + `/skills add` fallback registers skills
flat too. The phase skills (brainstorm, research, plan, build, ship) are `user-invocable: false`: hidden
from the `/` picker, invoked by the orchestrating skill or by natural language — every skill still
auto-triggers from its `description`.
