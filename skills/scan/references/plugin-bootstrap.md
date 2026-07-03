---
type: Reference
title: "Plugin bootstrap — the skills wi works best with"
description: "wi runs standalone, but it's deliberately thin and gets much stronger when it can delegate to a few existing skills."
timestamp: 2026-06-07
tags: [scan, reference]
---

# Plugin bootstrap — the skills wi works best with

wi runs standalone, but it's deliberately thin and gets much stronger when it can delegate to a few
existing skills. On first scan, check what's installed and **offer** to add the rest. Never install
without asking; never block if the user declines.

## How to check availability

A skill/plugin is available if it appears in this session's skills list, or its directory exists under a
known plugins path. If unsure, treat it as missing and offer it.

## Recommended set

| Plugin / skills | Why wi wants it | Install (official source) |
|-----------------|-----------------|---------------------------|
| **obra/superpowers** | brainstorming, writing-plans, subagent-driven-development, using-git-worktrees, TDD, code-review, verification, finishing-a-branch — wi delegates the heavy loop to these | `/plugin marketplace add obra/superpowers-marketplace` then `/plugin install superpowers@superpowers-marketplace` |
| **anthropics/skills:frontend-design** | building/refining UI for `[frontend]` tasks | `npx skills add anthropics/skills` (via skills.sh) |
| **vercel-labs/skills:find-skills** (optional) | lets wi pull a missing skill mid-run | `npx skills add vercel-labs/skills` |

If you can't verify an exact marketplace slug, don't fabricate one — give the user the command shape and
ask them to confirm the source, or point them at https://skills.sh to find it.

## Entry-command aliases (Copilot / Codex only)

On Claude Code the plugin namespace already gives `/wi:scan`, `/wi:dev`, `/wi:rpa` — skip this section.
On Copilot CLI the plugin prefix renders the entry points as `/wi scan`, `/wi dev`, `/wi rpa`, and on
Codex they invoke as `$scan`, `$dev`, `$rpa`. wi ships flat **forwarding aliases** that read as one
token: `/wi-scan`, `/wi-dev`, `/wi-rpa` (Copilot) and `$wi-scan`, `$wi-dev`, `$wi-rpa` (Codex).

As part of the same offer below, ask once whether to install them: copy each directory under
`${CLAUDE_PLUGIN_ROOT}/references/skill-aliases/` (i.e. `wi-scan/`, `wi-dev/`, `wi-rpa/`) into
`~/.agents/skills/` — the flat skills directory both harnesses read (create it if absent; overwriting an
existing `wi-*` alias there is fine, they are wi's own forwarders). The aliases are version-independent —
they forward to whatever wi plugin is installed — so this is a one-time copy per machine, not a
per-update chore. Declining costs nothing: the plugin forms keep working.

## The offer

After detecting what's missing, ask once with AskUserQuestion, e.g.:

- "superpowers isn't installed — it powers wi's brainstorm/build/ship. Install it now?" → on yes, output
  (or run, if the environment allows) the two `/plugin` commands above and confirm they registered.
- Group the offer: list everything missing and let the user pick which to add (multi-select).

Record the outcome in your scan report ("installed: superpowers; skipped: find-skills"). wi's phase skills
each detect availability again at run time and fall back gracefully, so a "skip now" is never fatal — the
user can re-run `/wi:scan` or install later.
