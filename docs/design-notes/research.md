---
type: Design Notes
title: "research - design rationale (maintainer notes)"
description: The "why" behind research/SKILL.md's rules, relocated out of the loaded skill by #41 pass 2; the runtime never reads this file, and each entry is anchored to the section it explains.
timestamp: 2026-07-11
tags: [research, design-notes, context-budget]
---

# research - design rationale (maintainer notes)

`skills/research/SKILL.md` is loaded wholesale and re-read ~75x per run, so it carries rules only. The
rationale lives here, anchored by section. When editing the skill, keep this file in sync: a rule whose
"why" is deleted instead of relocated loses its guard against future "simplification".

## Intro

- **Mission.** `dev` captured the WHAT; research owns the HOW and its confirmation: design it (the
  researcher fan-out), prove it (the plan-mode checker pass), get the nod (the design gate). Everything
  after the gate is implementation; nothing after the gate asks the user anything.

## Operating principles

- **Why a ledger row lands the moment the completion notification arrives:** the token figure exists
  only in that notification (wit-directory.md's `tokens.md` section is the canonical statement); a row
  written later can only be reconstructed or estimated, and the ledger rule forbids both. ship
  finalizes the totals at its dossier tidy, and the `check_tokens.py` gate at ship's close-out blocks
  the PR if the ledger was skipped, so a missed row surfaces as a blocked run, not a quiet gap.
- **Why researchers return short reports:** workflow.md's context budget is the canonical rule; the
  skill keeps only the research-specific application (which artifact is active in which phase, and
  that researcher source material never enters the orchestrator's context).

## research:0 - engage & resume

- **Why the engage stamp exists:** the invocation is auditable on disk, and `token_report.py` computes
  the run's phase spans from progress.md's stamped Log lines, so transitions must be stamped, never
  narrated only in the console.
- **Why the version is read, never guessed:** a wrong version poisons the audit trail; on a per-skill
  Copilot install the plugin manifest isn't reachable, and an omitted version is honest where an
  invented one is not.

## research:1 - research

- **Why an existing ADR settles its question (1a):** re-evaluating a settled decision (say, the
  background-job library ADR-0007 already chose) burns researcher budget to produce either the same
  answer or a silent contradiction; a genuine conflict with the brief is a deliberate supersede (a new
  ADR citing the old one) so the decision trail stays linear.
- **Why learnings recall goes through the index (1a):** past runs' gotchas are the cheapest research
  there is; the one-line-plus-hook index keeps that recall inside the context budget, and a detail
  file opens only when its hook fits the current feature.
- **Why the tech-choice web contract lives in the agent (1b/1c):** the mode tag is the dispatch
  signal; the full survey contract (state of the art, the mandatory best-practices pass on the winner,
  evidence and provenance rules) is `agents/wit-researcher.md`, so the skill states the tag and points
  at the agent instead of restating the contract.
- **Why the ADR is committed immediately:** research runs on main before build branches, so an ADR +
  index row committed now rides the branch and the PR (wit-directory.md's project-level rule:
  committed where written). Deferring the commit would strand the decision outside the branch the
  build worktree is cut from.

## research:1 - Mixture of Agents

- **Why the orchestrator still decides:** the aggregator recommends; ownership of the ADR and of the
  Phase flip never moves (moa.md's research-point contract). Dissent is preserved because it feeds the
  ADR's rejected-alternatives and the gate's **Rejected:** line, where the user can see it.
- **Where the shared MoA mechanics live:** the dispatch markers, layer-2 semantics ("may change
  position; must say why"), who-writes-what, ledger convention, and the `.wit/models.md` config section
  the routing block mirrors are canonical in `references/moa.md`; the skill keeps only the
  research-point specifics (gating, charter contents, file names, the log line).

## research:2 - plan & pre-gate check

- **Why leftovers are carried into the gate summary:** whatever the checker loop couldn't resolve in
  its two rounds goes to the gate with its severity so the user decides with eyes open; a gate that
  hides an unresolved WARNING is a rubber stamp.
- **Why the stamp wording is exact:** `token_report.py` reads `design gate opened` as the end of the
  first autonomous span; the gate wait that follows is manual time and never counts toward the
  autonomous wall-clock. A paraphrased stamp makes the timing report `unavailable`.
- **Why the flip is research's alone:** plan ends with Phase still `plan`, so an interrupted run can
  never resume into the gate without this checker pass having run; the research:0 re-entry guard is
  the other half of the same protection.

## research:3 - design gate

- **Why the dossier commit comes first:** the gate decision is made against committed artifacts, and
  the build worktree (branched from main) starts with them; like the ADR, the dossier rides the branch
  and the PR.
- **Why the summary renders inline:** the `.wit/` files are the appendix, not the message; a gate that
  points at files makes the user assemble their own summary, which defeats the gate.
- **Why the approve stamps restart the clock:** the wait at the gate is manual time;
  `token_report.py`'s second autonomous span starts at `design gate approved` /
  `design gate auto-approved`, so the exact wording is load-bearing.
- **Why auto-approve still writes the summary into progress.md:** nobody is at the console, so the
  recorded summary is how the user reads the gate after the fact.

## research:4 - handoff

- **Why the keep-alive re-print happens only at the interactive gate:** the user is present (they just
  approved), so the paste can actually happen. Under auto-approve nobody is at the console (the gate
  was recorded, not asked) and the handoff already recorded the line; re-printing would suggest wit can
  arm persistence itself, and arming is the user's act, never wit's.
- **Framing that moved out of the skill:** the keep-alive loop (`/goal` or Autopilot) is the
  persistence wrapper; build/ship are the method. The skill keeps only the operative sequence.
