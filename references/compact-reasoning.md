---
type: Reference
title: "The compact-reasoning rule"
description: "Runtime norm for the orchestrator and every dispatched subagent: essential, decision-bearing reasoning only, with named hard-step carve-outs (tech-choice, adversarial verification, plan decomposition, design gates) that keep full depth."
timestamp: 2026-07-11
tags: [context-budget, agents, runtime, reference]
---

# The compact-reasoning rule

Generated reasoning is the run's third token stream, beside loaded prose and retained tool output
(workflow.md "Token budget" owns those two): the monologue the orchestrator and each subagent produce
before every compact output. A subagent's transcript is discarded — only the short report survives —
and the orchestrator's own monologue stays in its transcript, re-read on every later turn (~75×
measured on a real run). Verbose deliberation is pure overhead, multiplied hardest in build's
parallel task-runner waves and the checker's multi-round / MoA passes.

**The rule — essential, decision-bearing thoughts only.** Reason enough to make the decision
correctly, then act:

- No meta-narration ("let me think about…", "now I need to…"), no restating the dispatch, task
  block, or plan you were handed, and no re-deriving what an artifact already settles
  (`progress.md`, `tasks.md`, the ADR — read the line, don't reconstruct it).
- Depth that must survive goes in the artifact — notes file, spec, report — never in monologue.
  This extends the standing norm "depth goes in the notes file; the report is the decision" from
  reports to the reasoning before them.

**Carve-outs — hard steps keep full reasoning depth.** Terse by default, deliberate where it
matters; over-compression that dulls these is the failure mode this list exists to prevent:

- the researcher's tech-choice work — the outward survey, the comparison, the decision;
- the checker's adversarial verification — coverage tracing, refutation, evidence-hunting;
- plan decomposition — spec/tasks design, and the SDD on an rpa run;
- the design gates — assembling and weighing what is rendered to the user.

**Boundary.** The rule trims narration, never behavior: every report format and cap, output marker,
gate, verification contract, budget, and behavioral rule stays exactly as written. Artifact quality
is the invariant; the saving shows up in the token ledger (`tokens.md`), validated against a real
run, never a dry-run.
