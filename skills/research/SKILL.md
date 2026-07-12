---
type: Skill
name: research
user-invocable: false
description: >
  The design half of a wi feature: decide the HOW and get it confirmed at the design gate. Use this skill
  when dev hands off after brainstorming, when the user types "/wi:research", "research the approach",
  "design this feature", or when resuming a feature whose progress.md Phase is research, plan, or
  design-gate.
---

# research: design it, prove it, get the nod

`dev` captured the WHAT; you decide the HOW and get it confirmed. You own three phases (research →
plan → **design gate**), then implementation proceeds (build → ship) to the PR, kept alive by the
keep-alive loop (`/goal` or Autopilot) if the user armed it.

Design rationale for this skill lives in the wi repo's `docs/wi-design-notes/research.md` (maintainer
doc, never loaded at runtime).

## Operating principles

- **Autonomous until the gate** (workflow.md's no-questions rule). No questions during research or
  planning. When a decision arises, pick the best option given `brief.md` + `constitution.md`, record
  it, continue.
- **State on disk.** Layout: `${CLAUDE_PLUGIN_ROOT}/skills/research/references/wi-directory.md`. Never
  re-derive what a file records.
- **Hold the budget.** workflow.md's **context budget** is a hard rule: `constitution.md`,
  `repo-map.md`, `progress.md`, plus the one active artifact (`brief.md` while researching;
  `spec.md`/`tasks.md` while planning). Researchers read sources and return short reports, never
  pulling their material into this context. Re-entry (research:0) reads `progress.md` + the active
  artifact, not prior-phase files.
- **Delegate, summarize, discard.** Append each researcher's `tokens.md` row the moment its completion
  notification arrives, per wi-directory.md's **ledger rule**: exact tokens + `Duration`,
  `unavailable` when unobservable, never an estimate.
- **Borrow.** Detect installed skills and hand off:
  `${CLAUDE_PLUGIN_ROOT}/skills/research/references/integrations.md`.

## Pipeline

### 0 - Engage & resume
First act, always: append a Log line to `progress.md`: `research engine engaged (wi <version>)`,
reading <version> from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` (don't guess; if that file
isn't reachable, e.g. a per-skill Copilot install, omit the version rather than inventing one). Then
scaffold the token ledger (idempotent; no-op if it exists):
`python ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/check_tokens.py --init .wi/features/<slug>/tokens.md`
(python fallback: workflow.md "Script invocation"). Then re-enter the phase it names
(research | plan | design-gate). **Design-gate re-entry guard:** resuming at `design-gate` requires a
fresh plan-mode `verification.md` (`type: Verification`) in the feature folder; missing, or predating
the current `spec.md`/`tasks.md`, means the research:2 pre-gate checker pass runs first, then the gate
renders.

### 1 - Research -> pick the approach

**a · Check what's already settled.** `.wi/adr/index.md` first: an existing ADR **settles its
question**. If the brief genuinely contradicts a standing ADR, that's a deliberate **supersede** (a new
ADR citing the old one), never a silent re-litigation. Then `.wi/learnings.md` (the index): open a
`learnings/<slug>.md` detail file only when its hook is relevant.

**b · Decompose into load-bearing unknowns.** From `brief.md`, list the questions whose answer would
change the design: the integration seam, a library/technique choice, the data shape, a migration/compat
risk. Most features have 1-3; **cap at 4**; anything settled in (a) drops off the list. Tag each
question with its mode: **`[repo-question]`** (the repo should answer it: prior art, existing seam,
conventions) or **`[tech-choice]`** (new capability / greenfield / the existing pattern looks legacy;
the researcher must survey the current state of the art on the web, not answer from priors). Write them
to `research/questions.md`, one line each; that is the dispatch plan, and plan checks leftovers against
it.

**c · Dispatch with disjoint charters.** One **researcher** (`agents/wi-researcher.md`) per unknown, in
parallel, in the same turn. Each charter names: its single question **and mode** (the mode sets how
hard the researcher hits the web; see the agent), what is OUT of scope (the sibling charters, by name),
and any standing ADR it must respect. Ship each researcher `brief.md` + the relevant constitution rules
+ `repo-map.md` + any relevant learning. One small question = one researcher; never fan out for the
sake of it. Dispatch on the `researcher` tier from `progress.md`'s resolved-routing block (resolve or
refresh it per `${CLAUDE_PLUGIN_ROOT}/references/models.md`'s resolve-once rule).

**d · Reconcile -> decide.** Merge the reports into one recommended approach and adopt it. A report
that returns empty, blows its budget, or wanders off-charter gets **one** narrower re-dispatch; after
that, proceed on the best evidence available and log the gap in `progress.md`. Carry every report's
`Risks / unknowns` line forward to plan: each must end up resolved, spiked, or in `pitfalls.md`;
dropping one silently is a defect.

**Mixture of Agents (optional).** When the resolved-routing block's MoA row includes `research` in its
`points`, run this approach decision as an MoA proposer/aggregator pass instead of the single reconcile
above: N proposer researchers answer in parallel, an optional second layer refines, and one aggregator
synthesizes `research/proposal-synthesis.md`; you still adopt the recommendation and write the ADR. Full
contract (proposer charters, layer semantics, who-writes-what, the dissent-to-ADR/gate wiring, the
`approach via MoA (...)` log line, `tokens.md` rows): `${CLAUDE_PLUGIN_ROOT}/references/moa.md`. MoA row
`none`, or `research` not in its `points` → skip this branch; the reconcile above is the unchanged default.

If the decision is **hard to reverse**, record it as the next **ADR-NNNN** in the project-wide
`.wi/adr/` log (global numbering + an index.md row, per the plan skill's ADR template). Commit the ADR
+ its index row now, `docs(wi): ADR-NNNN <title>` (the project-level rule in `wi-directory.md`). Set
Phase = `plan` (stamped Log line: `- <ts> **Update** phase = plan`).

### 2 - Plan
Run **plan** (`wi:plan`): brief + research -> `spec.md` (testable acceptance criteria), `tasks.md`
(small ordered tasks with files + verify, plus the Waves section), `pitfalls.md`.

**Pre-gate check (checker · plan mode).** Before the gate, dispatch the **checker**
(`agents/wi-code-checker.md`) in `plan` mode over `spec.md` + `tasks.md` + `pitfalls.md` +
`constitution.md` + the relevant ADRs (and any **Runtime State Inventory** rows). It builds a
feature-backward coverage matrix and returns BLOCKER/WARNING/INFO findings, writing `verification.md`.
Feed them back: a BLOCKER (an unmapped acceptance criterion, a silently down-scoped decision) loops to
plan to fix, then the checker re-checks (**max 2 rounds**; each round appends its own `tokens.md` row
per the **ledger rule**). Whatever remains is **carried into the gate summary** with its severity. Then
Phase = `design-gate`, stamped as `- <ts> **Update** design gate opened`; the exact wording matters:
`token_report.py` reads this stamp as the end of the first autonomous span. This flip is **research's
alone**: plan ends with Phase still `plan`.

### 3 - Design gate
**Commit the dossier first.** Commit the feature dossier on main now, `docs(<slug>): feature dossier (design gate)`:
everything under `.wi/features/<slug>/`. The gate decides against committed artifacts. On a
**mid-build reopen** skip this main commit; the worktree branch already carries the amendments and
merges them back (the reopen rule below governs which copy you render).

The user decides **from the console**. Render the summary inline in your response; never just point at
the `.wi/` files. Use exactly this shape (~25-40 lines, content inlined from the ADR/spec/tasks you
just wrote):

```
## Design gate: <feature title>

**Approach (ADR-NNNN):** <the decision, one line>
**Why:** <2-3 lines: the decisive reasons>
**Rejected:** <alternative: why not> · <alternative: why not>
**Leaner path:** <the simplest version that meets the brief, and why anything beyond it is justified>

**Acceptance criteria (what "done" means):**
1. <criterion>  -> verified by <test/command>
2. ...

**The work:** <N> tasks in <M> waves
- Wave 1: <task titles>
- Wave 2: <task titles>

**Top risks being handled:** <2-3 pitfalls, one line each>
**Touches:** <n> files (<key paths>)
**Checker (plan mode):** <PASS, or N findings; list any unresolved BLOCKER/WARNING the user must weigh>

Full detail: .wi/features/<slug>/ (spec.md, tasks.md, pitfalls.md, verification.md; committed on main as of this gate) and .wi/adr/ADR-NNNN-*.md
```

No ADR (nothing hard to reverse)? Render the line as **Approach:** <the decision>
*(no ADR: nothing hard to reverse)* and drop the ADR path from the footer line.

Then check **Gate mode** in `progress.md`:
- **interactive** (default): ask with AskUserQuestion: **approve** / **amend the approach** (loop to
  research with the feedback) / **amend scope or spec** (loop to plan) / **stop**. Record the outcome;
  an approve is stamped `- <ts> **Update** design gate approved, phase = build` (this wording restarts
  the autonomous clock).
- **auto-approve** (`/wi:dev --auto`): skip the question; write the same rendered summary into
  `progress.md` and log `- <ts> **Update** design gate auto-approved (--auto), phase = build`.

**Re-opened mid-build** (a post-gate amend loops back here while the feature worktree exists): the
worktree's `.wi/features/<slug>/` is canonical: read and render the summary from that copy, not
main's, and say in the summary which copy it was rendered from.

Only an explicit approve (or auto-approve) advances to implementation.

### 4 - Hand off to implementation
**Interactive gate only:** if persistence wasn't armed at handoff, print the ready-made keep-alive
again (the user is present; they just approved), **verbatim from
`${CLAUDE_PLUGIN_ROOT}/references/keep-alive.md`**, the single source of the platform templates
(`/goal` on Claude Code & Codex, Grok Build's model-judged `/goal`, the Autopilot relaunch +
unattended-run warning on Copilot). Pasting
the `/goal` line is the go: when it registers, continue into build **in the same turn**; don't end the
turn waiting for another prompt. Under **auto-approve** skip the re-print: arming is the user's act,
never wi's.

Then proceed: **build** (`wi:build`), worktree + parallel waves, then **ship** (`wi:ship`), which ends
with the PR and the final report (token table included). No questions from here on.

Phase contracts & resumability: `${CLAUDE_PLUGIN_ROOT}/references/workflow.md`.
