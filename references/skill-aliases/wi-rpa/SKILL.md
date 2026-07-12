---
type: Skill
name: wi-rpa
description: >
  Alias of wi's rpa skill for flat-skill installs (Copilot CLI /wi-rpa, Codex CLI $wi-rpa, Grok Build
  /wi-rpa); forwards to the wi plugin's rpa entry point: turn a UiPath PDD into a built REFramework or
  Maestro solution through the wi loop to a PR. Supports "--auto" for a hands-off run.
---

# /wi-rpa: alias of wi's `rpa` skill

A forwarding alias, installed flat (`~/.agents/skills/`) so the command reads `/wi-rpa` on Copilot CLI
and Grok Build, and `$wi-rpa` on Codex CLI, without the plugin-namespace prefix. The real skill ships
inside the wi plugin; this file contains no RPA logic of its own.

1. Locate the **wi plugin root**: the installed plugin directory (or clone) holding `skills/`,
   `agents/`, and `.claude-plugin/` (Copilot: under `~/.copilot/installed-plugins/…`; Grok: the active
   wi entry's installPath in `~/.claude/plugins/installed_plugins.json`).
2. Read `AGENTS.md` at that root (the cross-platform bootstrap), then follow `skills/rpa/SKILL.md` with
   the user's arguments (the PDD path or reference), passing `--auto` through if given.

If no wi plugin root exists, say so and point the user at
`https://github.com/Wittenberger-Industries/wi-plugin`; do not improvise the build from this alias.
