---
type: Skill
name: wi-scan
description: >
  Alias of wi's scan skill for flat-skill installs (Copilot CLI /wi-scan, Codex CLI $wi-scan, Grok Build
  /wi-scan); forwards to the wi plugin's scan entry point: document a project folder and bootstrap wi in
  it. Supports "--refresh" to drift-check an existing scan and consolidate learnings.
---

# /wi-scan: alias of wi's `scan` skill

A forwarding alias, installed flat (`~/.agents/skills/`) so the command reads `/wi-scan` on Copilot CLI
and Grok Build, and `$wi-scan` on Codex CLI, without the plugin-namespace prefix. The real skill ships
inside the wi plugin; this file contains no scan logic of its own.

1. Locate the **wi plugin root**: the installed plugin directory (or clone) holding `skills/`,
   `agents/`, and `.claude-plugin/` (Copilot: under `~/.copilot/installed-plugins/…`; Grok: the active
   wi entry's installPath in `~/.claude/plugins/installed_plugins.json`).
2. Read `AGENTS.md` at that root (the cross-platform bootstrap), then follow `skills/scan/SKILL.md` with
   the user's arguments, passing `--refresh` through if given.

If no wi plugin root exists, say so and point the user at
`https://github.com/Wittenberger-Industries/wi-plugin`; do not improvise the scan from this alias.
