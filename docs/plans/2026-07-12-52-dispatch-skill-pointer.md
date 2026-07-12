---
type: Plan
title: "#52 dispatch-time skill pointer: pinned runners reach skills via a resolved SKILL.md path, not the Skill tool"
description: "The orchestrator resolves a capability-tagged skill's SKILL.md path once per run into progress.md and the task dispatch hands it to the pinned runner (which has no Skill tool); the runner Reads it and works through its guidance. General protocol: capability tag -> integrations.md registry -> resolved path. Frontend is the first instance; log strings and the checker contract stay byte-identical."
feature: 52-dispatch-skill-pointer
timestamp: 2026-07-12
tags: [plan, agents, orchestration, cross-platform]
---

# #52 dispatch-time skill pointer

## Problem (from the issue AC)

`wi-task-runner`'s `tools:` pin (`Read, Write, Edit, Bash, Grep, Glob`) has no `Skill` tool, so a pinned
runner can neither invoke a skill nor see the skills catalog. The `[frontend]` rule tells the runner to
"check your skills list", which the pin guarantees is empty, so every `[frontend]` task reports the
fallback even when `frontend-design` is installed, and ship's checker raises its delegation WARNING every
time (a permanent false alarm). Owner decision (2026-07-11): fix with a general dispatch-time pointer, not
a `Skill`-bearing variant agent.

## Design (owner-locked): capability tag -> registry -> resolved path -> dispatch

The orchestrator (the session, which DOES see the catalog and the plugin layout) resolves the mapped
skill's `SKILL.md` absolute path once per run and passes it in the task dispatch. The pinned runner Reads
that file (and any references it cites; they are plain files) and does that aspect of the task through the
guidance. No tool-list change, identical on all three platforms, and every future skill-mediated
capability rides the same rails (new capability = registry row + plan tag, zero protocol change).

## Tasks (one focused diff each; no runner-behavior change beyond the pointer)

1. **Charter clause swap** `agents/wi-task-runner.md` (the one sanctioned charter diff): replace the
   "a design skill available in your skills ... check your skills list" clause with the dispatch-pointer
   contract ("your dispatch names the design skill and hands you the absolute path to its `SKILL.md`;
   you have no Skill tool, so Read that file and build through its guidance"). Fallback + log strings
   (`frontend via frontend-design` / `frontend via wi fallback (frontend-design absent)`) byte-identical.
   Nothing else in the charter changes (caps, markers, contracts, tool list untouched).
2. **Build dispatch + resolve-once** `skills/build/SKILL.md` build:2 frontend paragraph: for a
   `[frontend]` task, resolve the mapped skill's `SKILL.md` path once per run into progress.md's new
   `## Skill paths (resolved)` block (same staleness rule as `## Model routing (resolved)`; lazy: runs
   with no tagged task resolve nothing), then the dispatch names the skill and hands the runner that
   absolute path.
3. **Registry role + Frontend wording** `skills/research/references/integrations.md`: state explicitly
   that integrations.md is the canonical capability -> skill registry and that a new skill-mediated
   capability is a registry row + a plan tag with zero protocol change (the generality claim in shipped
   text); update "Frontend work" Operationally wording to the pointer mechanism (pinned runners have no
   Skill tool -> build resolves the path -> dispatch hands it over -> runner Reads it).
4. **progress.md template** `skills/research/references/wi-directory.md`: add the lazy
   `## Skill paths (resolved)` block after `## Model routing (resolved)` (skill -> abs SKILL.md path or
   `absent`; comment notes lazy write + same staleness rule).
5. **Per-platform find rule** `references/codex-tools.md` + `references/copilot-tools.md`: one line each on
   where an external skill's `SKILL.md` absolute path is found for the pointer (Codex: the native
   skills/plugin install dir; Copilot: `~/.copilot/installed-plugins/...` or the clone). Claude's is the
   version-keyed plugin cache (default, no separate file).
6. **Audit only** `skills/scan/references/plugin-bootstrap.md`: install-table row for `frontend-design`
   ("building/refining UI for `[frontend]` tasks") still true -> no change.

## What stays byte-identical (binding)

- No `Skill` in any charter `tools:`; no new agent type.
- Checker rule (`wi-code-checker.md` frontend delegation, result mode), the two frontend log strings,
  report caps, output markers, verification-gate contracts.
- rpa/uipath delegation (orchestrator-mediated) unchanged.

## Verification

- `python scripts/validate.py` + `pytest tests/` green (this is protocol/prose; no new Python surface).
- Load-alone check: each touched file makes correct decisions read in isolation (the standing test).
- **Generality proof (PR body, on paper):** adding a hypothetical second capability (e.g. `[a11y-audit]`
  -> some `a11y` skill) needs only an integrations.md registry row + a plan tag; no charter, plan-format,
  build-protocol, or progress-template change. Demonstrated, not shipped.
- Behavior with the skill absent / path unresolvable is byte-identical to today's fallback.

## Out of scope

- No speculative second capability wired in (generality is proven on paper).
- No escalation to a `Skill`-bearing variant (documented as a future routing-cell upgrade, not built).
