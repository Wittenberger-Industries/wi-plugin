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

# research — design it, prove it, get the nod

`dev` captured the WHAT; you decide the HOW and get it confirmed. You own three phases — research →
plan → **design gate** — and then implementation proceeds (build → ship) to the PR, kept alive by the
keep-alive loop (`/goal` or Autopilot) if the user armed it.

## Operating principles

- **Autonomous until the gate.** No questions during research or planning. When a decision arises, pick
  the best option given `brief.md` + `constitution.md`, record it, continue.
- **State on disk.** Layout: `${CLAUDE_PLUGIN_ROOT}/skills/research/references/wi-directory.md`. Never
  re-derive what a file records.
- **Hold the budget.** workflow.md's **context budget** is a hard rule: `constitution.md`,
  `repo-map.md`, `progress.md`, plus the one active artifact (`brief.md` while researching;
  `spec.md`/`tasks.md` while planning). Researchers read sources and return short reports — never
  pull their material into this context. Re-entry (§0) reads `progress.md` + the active artifact,
  not prior-phase files.
- **Delegate, summarize, discard.** Researchers run in parallel subagents and return short reports; append
  each one's token count as a row to `tokens.md` the moment its completion notification arrives (the figure
  exists only there — NOT retrievable later), with its `Duration` cell (the notification's elapsed time, or
  your dispatch→arrival delta from the OS clock; `unavailable` if neither exists). ship finalizes the
  orchestrator total + duration totals and a `check_tokens.py` gate blocks the PR if the ledger was skipped.
- **Borrow.** Detect installed skills and hand off:
  `${CLAUDE_PLUGIN_ROOT}/skills/research/references/integrations.md`.

## Pipeline

### 0 - Engage & resume
First act, always: append a Log line to `progress.md` — `research engine engaged (wi <version>)`, reading
<version> from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` (don't guess; if that file isn't reachable — e.g. a per-skill Copilot install — omit the version rather than inventing one) — so it's auditable on disk. Then scaffold the token ledger (idempotent — no-op if it exists): `python ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/check_tokens.py --init .wi/features/<slug>/tokens.md` (`python` assumed on PATH; where it does not resolve, fall back to `py -3` on Windows or `python3` on Linux/macOS). Then re-enter the phase it names (research | plan | design-gate). **Design-gate re-entry
guard:** resuming at `design-gate` requires a fresh plan-mode `verification.md` (`type: Verification`) in
the feature folder; if it is missing or predates the current `spec.md`/`tasks.md`, run the §2 pre-gate checker
pass first, then present the gate.

### 1 - Research -> pick the approach

**a · Check what's already settled.** `.wi/adr/index.md` first: an existing ADR **settles its question** —
don't re-evaluate the background-job library ADR-0007 already chose. If the brief genuinely contradicts a
standing ADR, that's a deliberate **supersede** (a new ADR citing the old one), never a silent
re-litigation. Then `.wi/learnings.md` (the index): open a `learnings/<slug>.md` detail file only when its
hook is relevant — past runs' gotchas are the cheapest research there is.

**b · Decompose into load-bearing unknowns.** From `brief.md`, list the questions whose answer would
change the design: the integration seam, a library/technique choice, the data shape, a migration/compat
risk. Most features have 1-3; **cap at 4**; anything settled in (a) drops off the list. Tag each question
with its mode — **`[repo-question]`** (the repo should answer it: prior art, existing seam, conventions)
or **`[tech-choice]`** (new capability / greenfield / the existing pattern looks legacy — the researcher
must survey the current state of the art + best practices on the web, not answer from priors). Write them
to `research/questions.md`, one line each — that's the dispatch plan, and plan checks leftovers against it.

**c · Dispatch with disjoint charters.** One **researcher** (`agents/wi-researcher.md`) per unknown — in
parallel, in the same turn. Each charter names: its single question **and mode** (the mode sets how hard
the researcher hits the web — see the agent), what is OUT of scope (the sibling charters, by name), and
any standing ADR it must respect. Ship each researcher `brief.md` + the relevant constitution rules +
`repo-map.md` + any relevant learning. One small question = one researcher; never fan out for the sake
of it. Dispatch each researcher on the `researcher` tier from `progress.md`'s resolved-routing block
(absent, or `.wi/models.md` changed after its stamp → resolve once and rewrite the block;
`${CLAUDE_PLUGIN_ROOT}/references/models.md`'s resolve-once rule).

**d · Reconcile -> decide.** Merge the reports into one recommended approach and adopt it. A report that
returns empty, blows its budget, or wanders off-charter gets **one** narrower re-dispatch; after that,
proceed on the best evidence available and log the gap in `progress.md`. Carry every report's
`Risks / unknowns` line forward to plan — each must end up resolved, spiked, or in `pitfalls.md`;
dropping one silently is a defect.

**Mixture of Agents (optional).** When the resolved-routing block's MoA row includes `research` in its
`points` (mirroring `.wi/models.md`'s `## Mixture of Agents` section): dispatch N proposer researchers
(`agents/wi-researcher.md`, one per listed `proposers` tier)
in parallel, same turn, each with the SAME charter — `brief.md` + all researcher reports + the relevant
constitution rules + standing ADRs + the marker `MoA role: proposer <i>/<N>`; each commits to ONE
approach in `research/proposal-<i>.md`. `layers: 2` → a second parallel round: each proposer reads ALL
round-1 proposals and returns a refinement in `research/proposal-<i>-r2.md` (may change position; must
say why). Then one aggregator dispatch (`MoA role: aggregator`, at the `aggregator` tier) reads all
proposals, writes `research/proposal-synthesis.md`, and returns the single recommendation with dissent
noted. Adopt it as the recommended approach — the orchestrator still decides and writes the ADR; dissent
feeds the ADR's rejected-alternatives and the gate's **Rejected:** line. Log
`approach via MoA (<N> proposers, <L> layers, aggregator <tier>)`; each dispatch appends its own
`tokens.md` row on completion. MoA row `none`, or `research` not in its `points` → skip this branch
entirely; the reconcile above is the unchanged default.

If the decision is **hard to reverse**, record it as the next
**ADR-NNNN** in the project-wide `.wi/adr/` log (global numbering + an index.md row, per the plan skill's
ADR template). Commit the ADR + its index row now (`docs(wi): ADR-NNNN <title>`) — research runs on main
before build branches, so the committed ADR rides the branch and the PR (the project-level rule in
`wi-directory.md`). Set Phase = `plan` (stamped Log line: `- <ts> **Update** phase = plan`).

### 2 - Plan
Run **plan** (`wi:plan`): brief + research -> `spec.md` (testable acceptance criteria), `tasks.md` (small
ordered tasks with files + verify, plus the Waves section), `pitfalls.md`.

**Pre-gate check (checker · plan mode).** Before the gate, dispatch the **checker** (`agents/wi-code-checker.md`)
in `plan` mode over `spec.md` + `tasks.md` + `pitfalls.md` + `constitution.md` + the relevant ADRs (and any
**Runtime State Inventory** rows). It builds a feature-backward coverage matrix and returns
BLOCKER/WARNING/INFO findings, writing `verification.md`. Feed them back: a BLOCKER — an unmapped
acceptance criterion, a silently down-scoped decision — loops to plan to fix, then the checker re-checks
(**max 2 rounds**; each round appends its own `tokens.md` row — a re-check round that returns without a
completion notification records `unavailable`, never an estimate). Whatever remains is **carried into the
gate summary** with its severity, so the user
decides with eyes open. Then Phase = `design-gate`, stamped as `- <ts> **Update** design gate opened` —
the exact wording matters: `token_report.py` reads this stamp as the end of the first autonomous span
(the gate wait that follows is manual time and never counts). This flip is **research's alone**: plan
ends with Phase still `plan`, so an interrupted run can never resume into the gate without this checker
pass having run.

### 3 - Design gate
**Commit the dossier first.** Commit the feature dossier on main now — `docs(<slug>): feature dossier
(design gate)` — everything under `.wi/features/<slug>/`. The gate decision is made against committed
artifacts, and the build worktree (branched from main) starts with them; like the ADR, the dossier rides
the branch and the PR. On a **mid-build reopen** skip this main commit — the worktree branch already
carries the amendments and merges them back (the reopen rule below governs which copy you render).

The user decides **from the console**. Render the summary inline in your response — never just point at
the `.wi/` files; they are the appendix, not the message. Use exactly this shape (~25-40 lines, content
inlined from the ADR/spec/tasks you just wrote):

```
## Design gate: <feature title>

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

Full detail: .wi/features/<slug>/ (spec.md, tasks.md, pitfalls.md, verification.md — committed on main as of this gate) and .wi/adr/ADR-NNNN-*.md
```

No ADR (nothing hard to reverse)? Render the line as **Approach:** <the decision> *(no ADR — nothing hard
to reverse)* and drop the ADR path from the footer line.

Then check **Gate mode** in `progress.md`:
- **interactive** (default): ask with AskUserQuestion: **approve** / **amend the approach** (loop to
  research with the feedback) / **amend scope or spec** (loop to plan) / **stop**. Record the outcome —
  an approve is stamped `- <ts> **Update** design gate approved, phase = build` (this wording restarts
  the autonomous clock after the manual gate wait).
- **auto-approve** (`/wi:dev --auto`): skip the question; write the same rendered summary into
  `progress.md` and log `- <ts> **Update** design gate auto-approved (--auto), phase = build` — the user
  reads it after the fact.

**Re-opened mid-build** (a post-gate amend loops back here while the feature worktree exists): the
worktree's `.wi/features/<slug>/` is canonical — read and render the summary from that copy, not main's,
and say in the summary which copy it was rendered from.

Only an explicit approve (or auto-approve) advances to implementation.

### 4 - Hand off to implementation
**Interactive gate only:** if persistence wasn't armed at handoff, print the ready-made keep-alive again
(the user is present — they just approved) for the current platform: Claude Code & Codex CLI arm their
built-in `/goal` with the PR-open condition; Copilot CLI relaunches under Autopilot. The exact command
templates — and the unattended-run warning that must accompany the Copilot one — live in
`${CLAUDE_PLUGIN_ROOT}/references/keep-alive.md`; print them from there verbatim. Pasting the `/goal`
line is the go: when it registers, continue into build **in the same turn** — don't end the turn waiting
for another prompt. Under **auto-approve**
skip the re-print — nobody is at the console (the gate was recorded, not asked), the handoff already
recorded the line, and arming is the user's act, never wi's.

Then proceed: **build** (`wi:build`) — worktree + parallel waves — then **ship** (`wi:ship`), which ends
with the PR and the final report (token table included). The keep-alive loop (/goal or Autopilot) is the
persistence wrapper; build/ship are the method. No questions from here on.

Phase contracts & resumability: `${CLAUDE_PLUGIN_ROOT}/skills/research/references/workflow.md`.
