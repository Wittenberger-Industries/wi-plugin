---
type: Skill
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
keep-alive loop (`/goal` or Autopilot) if the user armed it.

## Operating principles

- **Autonomous until the gate.** No questions during research or planning. When a decision arises, pick
  the best option given `brief.md` + `constitution.md`, record it, continue.
- **State on disk.** Layout: `${CLAUDE_PLUGIN_ROOT}/skills/research/references/wi-directory.md`. Never
  re-derive what a file records.
- **Delegate, summarize, discard.** Researchers run in parallel subagents and return short reports; append
  each one's token count as a row to `tokens.md` the moment its completion notification arrives (the figure
  exists only there — NOT retrievable later). ship finalizes the orchestrator total and a `check_tokens.py`
  gate blocks the PR if the ledger was skipped.
- **Borrow.** Detect installed skills and hand off:
  `${CLAUDE_PLUGIN_ROOT}/skills/research/references/integrations.md`.

## Pipeline

### 0 - Engage & resume
First act, always: append a Log line to `progress.md` — `research engine engaged (wi <version>)`, reading
<version> from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` (don't guess; if that file isn't reachable — e.g. a per-skill Copilot install — omit the version rather than inventing one) — so it's auditable on disk. Then scaffold the token ledger (idempotent — no-op if it exists): `python ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/check_tokens.py --init .wi/goals/<slug>/tokens.md` (`python` assumed on PATH; where it does not resolve, fall back to `py -3` on Windows or `python3` on Linux/macOS). Then re-enter the phase it names (research | plan | design-gate). **Design-gate re-entry
guard:** resuming at `design-gate` requires a fresh plan-mode `verification.md` (`type: Verification`) in
the goal folder; if it is missing or predates the current `spec.md`/`tasks.md`, run the §2 pre-gate checker
pass first, then present the gate.

### 1 - Research -> pick the approach

**a · Check what's already settled.** `.wi/adr/index.md` first: an existing ADR **settles its question** —
don't re-evaluate the background-job library ADR-0007 already chose. If the brief genuinely contradicts a
standing ADR, that's a deliberate **supersede** (a new ADR citing the old one), never a silent
re-litigation. Then `.wi/learnings.md` (the index): open a `learnings/<slug>.md` detail file only when its
hook is relevant — past runs' gotchas are the cheapest research there is.

**b · Decompose into load-bearing unknowns.** From `brief.md`, list the questions whose answer would
change the design: the integration seam, a library/technique choice, the data shape, a migration/compat
risk. Most goals have 1-3; **cap at 4**; anything settled in (a) drops off the list. Tag each question
with its mode — **`[repo-question]`** (the repo should answer it: prior art, existing seam, conventions)
or **`[tech-choice]`** (new capability / greenfield / the existing pattern looks legacy — the researcher
must survey the current state of the art + best practices on the web, not answer from priors). Write them
to `research/questions.md`, one line each — that's the dispatch plan, and plan checks leftovers against it.

**c · Dispatch with disjoint charters.** One **researcher** (`agents/wi-researcher.md`) per unknown — in
parallel, in the same turn. Each charter names: its single question **and mode** (the mode sets how hard
the researcher hits the web — see the agent), what is OUT of scope (the sibling charters, by name), and
any standing ADR it must respect. Ship each researcher `brief.md` + the relevant constitution rules +
`repo-map.md` + any relevant learning. One small question = one researcher; never fan out for the sake
of it. When `.wi/moa.md` exists, dispatch each researcher on its MoA model (override → `wi-researcher`
role → inherit; `${CLAUDE_PLUGIN_ROOT}/references/moa.md`).

**d · Reconcile -> decide.** Merge the reports into one recommended approach and adopt it. A report that
returns empty, blows its budget, or wanders off-charter gets **one** narrower re-dispatch; after that,
proceed on the best evidence available and log the gap in `progress.md`. Carry every report's
`Risks / unknowns` line forward to plan — each must end up resolved, spiked, or in `pitfalls.md`;
dropping one silently is a defect. If the decision is **hard to reverse**, record it as the next
**ADR-NNNN** in the project-wide `.wi/adr/` log (global numbering + an index.md row, per the plan skill's
ADR template). Set Phase = `plan`.

### 2 - Plan
Run **plan** (`wi:plan`): brief + research -> `spec.md` (testable acceptance criteria), `tasks.md` (small
ordered tasks with files + verify, plus the Waves section), `pitfalls.md`.

**Pre-gate check (checker · plan mode).** Before the gate, dispatch the **checker** (`agents/wi-code-checker.md`)
in `plan` mode over `spec.md` + `tasks.md` + `pitfalls.md` + `constitution.md` + the relevant ADRs (and any
**Runtime State Inventory** rows). It builds a goal-backward coverage matrix and returns
BLOCKER/WARNING/INFO findings, writing `verification.md`. Feed them back: a BLOCKER — an unmapped
acceptance criterion, a silently down-scoped decision — loops to plan to fix, then the checker re-checks
(**max 2 rounds**). Whatever remains is **carried into the gate summary** with its severity, so the user
decides with eyes open. Then Phase = `design-gate` — this flip is **research's alone**: plan ends with
Phase still `plan`, so an interrupted run can never resume into the gate without this checker pass having
run.

### 3 - Design gate
The user decides **from the console**. Render the summary inline in your response — never just point at
the `.wi/` files; they are the appendix, not the message. Use exactly this shape (~25-40 lines, content
inlined from the ADR/spec/tasks you just wrote):

```
## Design gate: <goal title>

**Approach (ADR-NNNN):** <the decision, one line>
**Why:** <2-3 lines — the decisive reasons>
**Rejected:** <alternative — why not> · <alternative — why not>
**Leaner path:** <the simplest version that meets the brief — and why anything beyond it is justified>

**Acceptance criteria (what "done" means):**
1. <criterion>  -> verified by <test/command>
2. ...

**The work:** <N> tasks in <M> waves
- Wave 1: <task titles>
- Wave 2: <task titles>

**Top risks being handled:** <2-3 pitfalls, one line each>
**Touches:** <n> files — <key paths>
**Checker (plan mode):** <PASS — or N findings; list any unresolved BLOCKER/WARNING the user must weigh>

Full detail: .wi/goals/<slug>/ (spec.md, tasks.md, pitfalls.md, verification.md) and .wi/adr/ADR-NNNN-*.md
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
  copilot --autopilot --max-autopilot-continues <N> --no-ask-user --allow-all -p "Drive the <slug> goal to done:
  build then ship until the <slug> PR is open, its branch passes <lint + test commands>, and
  .wi/goals/<slug>/progress.md Phase is done. Only files named in tasks.md change; never force-push;
  never weaken tests."
  ```

⚠️ `--no-ask-user --allow-all` runs Copilot fully unattended (prompts suppressed, all tools/paths granted)
— bounded only by `--max-autopilot-continues <N>` and the in-prompt constraints. Use it in repos you trust;
drop `--allow-all` if you want Copilot to still confirm risky actions.

Then proceed: **build** (`wi:build`) — worktree + parallel waves — then **ship** (`wi:ship`), which ends
with the PR and the final report (token table included). The keep-alive loop (/goal or Autopilot) is the
persistence wrapper; build/ship are the method. No questions from here on.

Phase contracts & resumability: `${CLAUDE_PLUGIN_ROOT}/skills/research/references/workflow.md`.
