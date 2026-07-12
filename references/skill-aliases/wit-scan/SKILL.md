---
type: Skill
name: wit-scan
description: >
  Alias of wit's scan skill for flat-skill installs (Copilot CLI /wit-scan, Codex CLI $wit-scan, Grok Build
  /wit-scan); forwards to the wit plugin's scan entry point: document a project folder and bootstrap wit in
  it. Supports "--refresh" to drift-check an existing scan and consolidate learnings.
---

# /wit-scan: alias of wit's `scan` skill

A forwarding alias, installed flat (`~/.agents/skills/`) so the command reads `/wit-scan` on Copilot CLI
and Grok Build, and `$wit-scan` on Codex CLI, without the plugin-namespace prefix. The real skill ships
inside the wit plugin; this file contains no scan logic of its own.

1. Locate the **wit plugin root**: the installed plugin directory (or clone) holding `skills/`,
   `agents/`, and `.claude-plugin/` (Copilot: under `~/.copilot/installed-plugins/…`; Grok: the active
   wit entry's installPath in `~/.claude/plugins/installed_plugins.json`).
2. Read `AGENTS.md` at that root (the cross-platform bootstrap), then follow `skills/scan/SKILL.md` with
   the user's arguments, passing `--refresh` through if given.

If no wit plugin root exists, say so and point the user at
`https://github.com/Wittenberger-Industries/witloop`; do not improvise the scan from this alias.
