---
type: Reference
title: "Build — Maestro flow (.flow) via uipath-maestro-flow"
description: "How wi:rpa builds when Framework = maestro: delegate flow generation to the uipath-maestro-flow skill, validate with uip maestro flow."
timestamp: 2026-06-16
tags: [rpa, maestro, reference]
---

# Build — Maestro flow (`.flow`)

Used when **`Framework: maestro`** (the REFramework path is `build-uipath.md`). wi owns the method, the gate,
and the artifacts; **`uipath-maestro-flow` owns the build** — borrow, don't reinvent.

Precondition: the design gate passed (recorded in `progress.md`) and the worktree exists with the
run dossier committed in-tree — rpa §6's framework-neutral isolate, same as the REFramework path.
First act: append `rpa build engaged (wi <version>)` to the log.

## 1. Execute the build DAG in waves (from `tasks.md`)

The DAG is: **shared components → per-flow scaffolds → subflows → wire-up** (see `maestro-architecture.md`).
Run it as wide as the DAG allows.

1. **Reuse first.** Before generating anything, check `.wi/components.md`; reuse a shared flow/subflow or a
   Library before building new.
2. **Generate the flow.** Delegate each flow/subflow to **`uipath-maestro-flow`** in parallel waves. **State
   the node plan from the SDD in every delegation prompt** — the trigger, each node (connector / approval /
   script / subflow / agent / ixp) with its inputs/outputs, the connections/agents it uses, and the
   approval/branch logic. Scaffold each unit as a Maestro flow per the SDD, never blank.
3. **Per-unit verify.** After each unit, the work isn't done until it at least validates —
   `uip maestro flow validate` (see the verification gate); a generated `.flow` must reflect the SDD's nodes.
4. **Commit small + record tokens.** One flow/subflow per focused commit (`feat(<flow>): ...`); tick
   `progress.md`. **Append each delegated unit's token count to `tokens.md`** the moment that subagent
   reports completion (the only point the count exists) — `tokens.md` is **mandatory**; initialize it on the
   first delegation if absent
   (`python ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/check_tokens.py --init .wi/features/<run-slug>/tokens.md` —
   python fallback: `skills/research/references/workflow.md` §Script invocation), and ship finalizes it
   (`token_report.py --write`) under a `check_tokens.py` close-out gate.
5. **Register new components.** If the build created something reusable (a shared subflow, a notifier flow),
   add it to `.wi/components.md` so the next flow inherits it.

## 2. Wire-up (if in scope)

For connections / triggers / agent registrations, delegate to `uipath-platform` (it owns the `uip` CLI +
Orchestrator side). Connection and asset **names** come from `.wi/orchestrator.md`; values live in
Orchestrator, never in the flow.
