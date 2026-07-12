---
type: Skill
name: wit-rpa
description: >
  Alias of wit's rpa skill for flat-skill installs (Copilot CLI /wit-rpa, Codex CLI $wit-rpa, Grok Build
  /wit-rpa); forwards to the wit plugin's rpa entry point: turn a UiPath PDD into a built REFramework or
  Maestro solution through the wit loop to a PR. Supports "--auto" for a hands-off run.
---

# /wit-rpa: alias of wit's `rpa` skill

A forwarding alias, installed flat (`~/.agents/skills/`) so the command reads `/wit-rpa` on Copilot CLI
and Grok Build, and `$wit-rpa` on Codex CLI, without the plugin-namespace prefix. The real skill ships
inside the wit plugin; this file contains no RPA logic of its own.

1. Locate the **wit plugin root**: the installed plugin directory (or clone) holding `skills/`,
   `agents/`, and `.claude-plugin/` (Copilot: under `~/.copilot/installed-plugins/…`; Grok: the active
   wit entry's installPath in `~/.claude/plugins/installed_plugins.json`).
2. Read `AGENTS.md` at that root (the cross-platform bootstrap), then follow `skills/rpa/SKILL.md` with
   the user's arguments (the PDD path or reference), passing `--auto` through if given.

If no wit plugin root exists, say so and point the user at
`https://github.com/Wittenberger-Industries/witloop`; do not improvise the build from this alias.
