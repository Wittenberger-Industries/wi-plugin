# Copilot CLI — tool & capability mapping for wi

wi's skills are written with Claude Code names. On Copilot CLI, use these equivalents.

## ${CLAUDE_PLUGIN_ROOT}
Copilot has no plugin-root variable. `${CLAUDE_PLUGIN_ROOT}` means the **wi plugin root** — the directory
holding `skills/`, `agents/`, and `.claude-plugin/` (i.e. the cloned wi repo). Install wi **whole** (clone +
`/skills add <repo>/skills`) so that root exists, then resolve every `${CLAUDE_PLUGIN_ROOT}` path against it.
This is why per-skill `gh skill install` is discouraged: cross-skill refs such as `ship` reading
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
| invoke a wi skill | skills load natively — `/<skill-name>` or auto-trigger by description |

## /goal keep-alive
Copilot has no predicate `/goal`. Use **Autopilot**: relaunch with the completion condition in the prompt —
`copilot --autopilot --max-autopilot-continues <N> --no-ask-user -p "<prompt incl. done-condition>"`.
Completion is model-judged and continuation-capped, not a hard predicate.

## Command namespace
`/wi:dev` etc. do not exist (Copilot has no custom slash commands). Invoke the skill as `/<skill-name>`
(e.g. `/dev`, `/scan`) or let it auto-trigger from its `description`.
