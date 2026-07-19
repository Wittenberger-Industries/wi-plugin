---
type: Report
title: "Dry-run: learnings lifecycle (#78-#82) on wit 1.13.3"
description: "Post-#82 full dry-run of /wit:dev --auto; deferred #78/#79/#81/#82 ACs verified PASS; Phase=done held by token-gate blocker (orthogonal)."
timestamp: 2026-07-19
tags: [testing, dry-run, learnings, reflection, process-drift]
---

# Dry-run: learnings lifecycle (#78-#82) on wit 1.13.3

- **Verdict:** **PARTIAL**
  - Target learnings ACs (**#78, #79, #81, #82**) **PASS**; **#80 = N/A** (first feature).
  - Full loop reached ship close-out; `Phase = done` held by the `tokens.md` structural gate
    (orthogonal to learnings features).
- **Plugin under test:** wit **1.13.3**
- **Sandbox:** `tmp/dryrun-2026-07-19-learnings/notes-cli` (notes CLI + unittest; no remote)
- **Feature:** `.wit/features/0001-search-command/` on branch `wit/0001-search-command`
- **Host:** Cursor; no `wit-*` subagent types, so researcher / task-runner / checker ran inline

## Deferred-AC checklist

### #78 applicable learnings stamp - **PASS**
`progress.md`:
`- 2026-07-19T23:25:06+03:00 **Update** applicable learnings: none`

### #79 causal WHEN -> DO/AVOID -> BECAUSE - **PASS**
`learnings/0001-search-command.md` uses causal triples; compressed index hook:
`WHEN case-insensitive matching -> lowercase BOTH sides (query + field)`

### #81 Reflection before fix - **PASS** (planted ship-gate red)
`progress.md`:
`- ... **Reflection** case-insensitive search matched raw text: cmd_search dropped .lower(), so AC1 went red at the ship gate - earlier catch: build`
Next Log line is the fix (restore `.lower()`; gate green).

### #82 process: suffix - **PASS**
`learnings.md` index line ends with:
`· process: ship-gate red->fix 1 (planted dry-run #81 check)`

### #80 counters - **N/A**
First feature; reinforce/`seen:` path not exercised. Format guidance present in ship:4.

## Blockers (orthogonal) — fixed in **v1.13.4**

1. `check_tokens.py` failed with `no subagent row with an integer token count` on an honest
   zero-dispatch / all-`unavailable` ledger, so `Phase = done` was held rather than fabricating tokens.
2. `token_report.py --write` auto-bound a foreign Claude Code transcript; corrected to `unavailable`.

## Spec findings — fixed in **v1.13.4**

1. Token gate allows finalized all-`unavailable` ledgers (Codex/Copilot / inline-role hosts).
2. `token_report.py` auto-detect scopes to the encoded cwd project dir (no foreign-session bind).
3. ship:1 local-gate red explicitly requires a Reflection line before the fix loop.

## Boundaries honored

B1 no push / no `gh`; B3 no installs; B4 no `/goal`; B5 worktree under sandbox; B7 <=3 tasks.
Plugin repo was not modified by the dry-run agent.

Full sandbox artifacts remain under `tmp/dryrun-2026-07-19-learnings/` (gitignored / outside the plugin tree).
