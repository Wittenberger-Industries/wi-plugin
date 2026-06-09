# Phase contracts & resumability

The loop is one interactive phase (**brainstorm**, run by `dev`) followed by an autonomous pipeline
(**research -> plan -> build -> ship**, run by `goal`). The handoff after brainstorm is the single human
checkpoint; after it, `goal` makes and records decisions on its own.

## State machine

```
scan (once, project-level)
        |
  /wi:dev --> brainstorm --(handoff)--> research -> plan -> [DESIGN GATE] -> build -> ship -> done
(interactive)                          |_ research skill _|  (interactive*)  |_ build+ship, kept alive
                                                                              by /goal or Autopilot _|

* the design gate is interactive by default; `/wi:dev --auto` auto-approves it (the same summary is
  still recorded in progress.md).
```

`progress.md`'s Phase field names the state. Resume = read it and re-enter that phase. After the
handoff, the only user interaction is the design gate.

## Contracts

| Phase | Run by | Mode | Reads | Writes | May skip when |
|-------|--------|------|-------|--------|----------------|
| scan | scan | one-time | the repo | repo-map, overview, constitution | repo-map exists & current |
| brainstorm | dev | interactive | request, repo-map, constitution | brief.md | brief exists & intent unchanged |
| research | research | autonomous | brief, repo-map, constitution | research/*, .wi/adr/ADR-* (if hard-to-reverse) | approach already chosen & recorded |
| plan | research | autonomous | brief, research, repo-map, constitution | spec, tasks, pitfalls | never |
| design-gate | research | interactive* | adr, spec, tasks | gate outcome in progress.md | never — it is the second human gate |
| build | post-gate loop (/goal or Autopilot keeps it alive) | autonomous | tasks, spec, constitution | source, ticked tasks | tasks already all ticked |
| ship | post-gate loop | autonomous | the diff, spec, constitution | commits, PR | never |

## Rules

1. **Inputs before phase.** No research without a brief; no build without tasks. `dev`/`goal` enforce order.
2. **Two gates, both deliberate.** The brainstorm handoff sets scope; the design gate confirms the
   architecture + design before any code (auto-approvable via `/wi:dev --auto`, always recorded).
   There is no third checkpoint.
3. **No questions outside the gates.** Between handoff and design gate, and after design-ok, decisions
   are made on best evidence and recorded (ADR / spec / progress.md), never deferred to the user.
4. **Write decisions immediately.** The chosen approach lives in `research/` + (if notable) an ADR; scope
   lives in `spec.md`. Later phases and a resumed session read these instead of re-deciding.
5. **Amend deliberately.** If build shows the plan is wrong, update `spec.md`/`tasks.md` and note it in
   `progress.md` — don't let code and plan diverge.
6. **Each phase ends by updating `progress.md`** (Phase + a Log line). Resumability depends on it.
7. **Surface failures, don't hide them.** If the engine can't finish (gate won't go green after bounded
   attempts; contradictory brief), stop, record the blocker + a clean partial state, open a draft PR or
   leave a tidy branch, and report. Hands-off is not silent.

## Skipping & re-running

- A phase whose outputs exist and whose inputs are unchanged is a no-op — read its output.
- `scan` is project-level; re-run only when the stack/layout changed or a recorded command proved wrong.

## Parallelism

Parallel is the default at every level: research fans out multiple researcher subagents in one turn; build
dispatches each wave of unblocked tasks concurrently (file-disjoint tasks share the goal worktree,
colliding ones escalate to per-task worktrees); and independent *goals* from `roadmap.md` can run at the
same time in separate sessions, since each owns its worktree. The serialization points are few and
deliberate: real DAG dependencies, shared files, tests that aren't parallel-safe, and the orchestrator
being the only committer.

## Token budget

`research` and the post-gate loop should hold at most: `constitution.md`, `repo-map.md`, the goal's `progress.md`, and the one
artifact for the active phase. Research and build tasks run in subagents that return summaries; their
transcripts never enter `goal`'s context. That is what makes a hands-off, multi-file feature affordable.
The cost is also *measured* where it can be: `tokens.md` records each subagent's **exact** usage (from its
completion notification). The main thread can't read its own usage *mid-turn*, but the harness
records it: ship runs `token_report.py` to sum the session transcript's per-turn `usage` for a real
orchestrator total. If that parse fails it's reported **unavailable** — never a fabricated number or a
fraction of subagent work.
