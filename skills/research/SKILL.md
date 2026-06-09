---
name: research
description: >
  The design half of a wi goal: research the approach, plan the work, then present architecture + design
  at the design gate for the user's confirmation. Use this skill when dev hands off after brainstorming,
  when the user types "/wi:research", "research the approach", "design this feature", or when resuming a
  goal whose progress.md Phase is research, plan, or design-gate. It dispatches parallel researcher
  agents, writes ADR/spec/tasks/pitfalls into .wi/, and on approval — or auto-approval via
  "/wi:dev --auto" — hands off to implementation (the build and ship skills), with a keep-alive loop (Claude/Codex /goal, or Copilot Autopilot) as the recommended persistence wrapper.
---

# research — design it, prove it, get the nod

`dev` captured the WHAT; you decide the HOW and get it confirmed. You own three phases — research →
plan → **design gate** — and then implementation proceeds (build → ship) to the PR, kept alive by the
built-in `/goal` if the user armed it.

## Operating principles

- **Autonomous until the gate.** No questions during research or planning. When a decision arises, pick
  the best option given `brief.md` + `constitution.md`, record it, continue.
- **State on disk.** Layout: `${CLAUDE_PLUGIN_ROOT}/skills/research/references/wi-directory.md`. Never
  re-derive what a file records.
- **Delegate, summarize, discard.** Researchers run in parallel subagents and return short reports; log
  each one's token count to `tokens.md` the moment its completion notification arrives.
- **Borrow.** Detect installed skills and hand off:
  `${CLAUDE_PLUGIN_ROOT}/skills/research/references/integrations.md`.

## Pipeline

### 0 - Engage & resume
First act, always: append a Log line to `progress.md` — `research engine engaged (wi <version>)`, reading
<version> from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` (don't guess) — so it's auditable on disk. Then re-enter the phase it names (research | plan | design-gate).

### 1 - Research -> pick the approach
Dispatch **researcher** agents (`agents/researcher.md`) with `brief.md` + constitution + repo-map — in
parallel, in the same turn, when there are independent questions (typically one surveying prior art in
the repo, another evaluating external options). Reconcile their reports into one recommended approach and
adopt it; for a small question one researcher is enough. If the decision is **hard to reverse**, record it as
the next **ADR-NNNN** in the project-wide `.wi/adr/` log (global numbering + an index.md row, per the
plan skill's ADR template). Set Phase = `plan`.

### 2 - Plan
Run **plan** (`wi:plan`): brief + research -> `spec.md` (testable acceptance criteria), `tasks.md` (small
ordered tasks with files + verify, plus the Waves section), `pitfalls.md`. Phase = `design-gate`.

### 3 - Design gate
The user decides **from the console**. Render the summary inline in your response — never just point at
the `.wi/` files; they are the appendix, not the message. Use exactly this shape (~25-40 lines, content
inlined from the ADR/spec/tasks you just wrote):

```
## Design gate: <goal title>

**Approach (ADR-NNNN):** <the decision, one line>
**Why:** <2-3 lines — the decisive reasons>
**Rejected:** <alternative — why not> · <alternative — why not>

**Acceptance criteria (what "done" means):**
1. <criterion>  -> verified by <test/command>
2. ...

**The work:** <N> tasks in <M> waves
- Wave 1: <task titles>
- Wave 2: <task titles>

**Top risks being handled:** <2-3 pitfalls, one line each>
**Touches:** <n> files — <key paths>

Full detail: .wi/goals/<slug>/ (spec.md, tasks.md, pitfalls.md) and .wi/adr/ADR-NNNN-*.md
```

Then check **Gate mode** in `progress.md`:
- **interactive** (default): ask with AskUserQuestion: **approve** / **amend the approach** (loop to
  research with the feedback) / **amend scope or spec** (loop to plan) / **stop**. Record the outcome.
- **auto-approve** (`/wi:dev --auto`): skip the question; write the same rendered summary into
  `progress.md` and log "design gate auto-approved (--auto)" — the user reads it after the fact.

Only an explicit approve (or auto-approve) advances to goal.

### 4 - Hand off to implementation
If persistence wasn't armed at handoff, print the ready-made keep-alive again (the user is present —
they just approved) for the current platform:

- **Claude Code / Codex CLI** (built-in `/goal`):

  ```
  /goal The <slug> PR is open and its branch passes <lint + test commands from repo-map.md>;
  .wi/goals/<slug>/progress.md Phase is done. Constraints: only files named in tasks.md change;
  never force-push; tests are never weakened to pass.
  ```

- **GitHub Copilot CLI** (Autopilot — condition in the prompt):

  ```
  copilot --autopilot --max-autopilot-continues <N> --no-ask-user -p "Drive the <slug> goal to done:
  build then ship until the <slug> PR is open, its branch passes <lint + test commands>, and
  .wi/goals/<slug>/progress.md Phase is done. Only files named in tasks.md change; never force-push;
  never weaken tests."
  ```

Then proceed: **build** (`wi:build`) — worktree + parallel waves — then **ship** (`wi:ship`), which ends
with the PR and the final report (token table included). The keep-alive loop (/goal or Autopilot) is the
persistence wrapper; build/ship are the method. No questions from here on.

Phase contracts & resumability: `${CLAUDE_PLUGIN_ROOT}/skills/research/references/workflow.md`.
