---
type: Skill
name: wit-dev
description: >
  Alias of wit's dev skill for flat-skill installs (Copilot CLI /wit-dev, Codex CLI $wit-dev, Grok Build
  /wit-dev); forwards to the wit plugin's dev entry point: brainstorm a feature, design it, confirm at the
  design gate, then build and ship hands-off to an open PR. Supports "--auto" to auto-approve the gate.
---

# /wit-dev: alias of wit's `dev` skill

A forwarding alias, installed flat (`~/.agents/skills/`) so the command reads `/wit-dev` on Copilot CLI
and Grok Build, and `$wit-dev` on Codex CLI, without the plugin-namespace prefix. The real skill ships
inside the wit plugin; this file contains no loop logic of its own.

1. Locate the **wit plugin root**: the installed plugin directory (or clone) holding `skills/`,
   `agents/`, and `.claude-plugin/` (Copilot: under `~/.copilot/installed-plugins/…`; Grok: the active
   wit entry's installPath in `~/.claude/plugins/installed_plugins.json`).
2. Read `AGENTS.md` at that root (the cross-platform bootstrap), then follow `skills/dev/SKILL.md` with
   the user's arguments as the feature idea, passing `--auto` through if given.

If no wit plugin root exists, say so and point the user at
`https://github.com/Wittenberger-Industries/witloop`; do not improvise the loop from this alias.
