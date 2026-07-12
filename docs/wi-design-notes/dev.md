---
type: Design Notes
title: "dev: design rationale (maintainer notes)"
description: "The \"why\" behind dev/SKILL.md's rules, relocated out of the loaded skill by #41 (v1.9.1); the runtime never reads this file; each entry is anchored to the step it explains."
timestamp: 2026-07-11
tags: [dev, design-notes, context-budget]
---

# dev: design rationale (maintainer notes)

`skills/dev/SKILL.md` is loaded wholesale and stays in the orchestrator's context for the whole run
(every retained token is re-read on every later turn, ~75× measured on a real run; workflow.md "Token
budget"), so it carries rules only. The rationale lives here, anchored by step. When editing the
skill, keep this file in sync: a rule whose "why" is deleted instead of relocated loses its guard
against future "simplification".

## Intro

- **Mission.** "This is how a feature starts": dev is the narrative spine of the loop, two
  conversations (brainstorm and the design gate) around an otherwise autonomous run. The intro used
  to enumerate the interactive moments; the Boundaries "by mode" bullet is the canonical statement,
  so the intro now carries only the contract.
- **Why the keep-alive pairing is stated up front:** wi provides the method (skills, artifacts,
  gates); the loop provides persistence and keeps the run going until done. The platform split
  (Claude Code and Codex have a built-in `/goal`; Copilot relaunches under Autopilot) matters at
  dev:4, where the templates print verbatim from keep-alive.md, the single source. `validate.py`
  checks that dev/SKILL.md still contains "autopilot" (the cross-platform handoff branch), so never
  trim the platform names out of the skill.

## dev:1 (scan and model routing)

- **Why scan-first is a hard precondition:** every later phase builds on `repo-map.md` and
  `constitution.md`, and the dev:4 preflight checks the gate commands against the map; a missing or
  stale map means arming a keep-alive condition on wrong commands.
- **What `--refresh` buys:** the drift pass is cheap; it updates facts and consolidates learnings.
  That is why staleness tells trigger a refresh rather than a full re-scan.
- **Why routing is resolved once and recorded:** models.md owns the resolve-once rule. The
  `## Model routing (resolved)` block in progress.md exists so every later dispatch reads a recorded
  decision instead of re-deriving it, and so a resumed run inherits identical routing; that is also
  why a resumed feature missing the block gets it written on re-entry.

## dev:2 (feature folder)

- **Why classification precedes creation:** the expensive failure is seeding a duplicate folder for
  an idea already in flight. The five classes' handling is factored verbatim into
  `references/feature-folder-cases.md` so the rare branches load only when a tell fires; the class
  list in the skill and that file's sections change together.
- **Why every Log line opens with a full OS-clock ISO-8601 stamp:** ship's `token_report.py`
  computes the run's phase spans and the autonomous wall-clock from these stamps; a date-only or
  guessed stamp silently corrupts the timing table. That is the "why" behind "never a date-only or
  guessed stamp".

## dev:4 (handoff preflight and keep-alive)

- **Why the preflight exists:** an armed loop with a broken condition is guaranteed waste; the
  condition would name commands no checker can verify, or a PR that can never open. All checks
  resolve inside the brainstorm stop precisely so the preflight never grows into a third gate.
- **Count drift note:** the skill used to open with "check two things"; the no-remote check was
  added later (the 2026-07-03 dry run), so the lead-in is now count-free ("resolve every check") and
  the close reads "All green" instead of "Both green". Behavior is unchanged.
- **Why `n/a - not configured` passes but `UNKNOWN - ask` blocks:** verified absence is information;
  the keep-alive condition simply renders without that clause (keep-alive.md's fill rule). UNKNOWN
  means nothing can verify the condition yet. Both are exact machine-read tokens shared with scan's
  repo-map template, stack-detection.md, and keep-alive.md; their em-dashes became plain hyphens
  under the em-dash mandate and must stay identical across all files (see the pass's lockstep
  record).
- **Why a no-remote repo never arms the keep-alive:** the PR-open condition can never hold, so an
  armed loop would spin forever; ship closes out locally instead (ship:7). keep-alive.md restates
  the refusal and credits dev's preflight, so the guard must stay in dev.
- **Why `--auto` must not pause at the handoff:** the user already chose hands-off by passing the
  flag; brainstorm was the only stop, and pausing for a "say go" is the bug the flag exists to
  avoid.
- **Why the interactive path continues in the same turn once the goal registers:** ending the turn
  after the recap or the "Goal set" acknowledgment stalls the run waiting for another prompt; that
  stall is the failure mode the "never end the turn" rule prevents. The stamped phase-flip Log line
  starts the autonomous clock, so the flip and the continuation belong in the same turn on both
  paths.
- **Trimmed restatement:** "armed, the run continues across turns until the condition holds" is
  keep-alive.md's own intro; the skill cites the file instead of repeating it.

## dev:6 (implement)

- **Why "no questions anywhere in this stretch" is a citation:** the no-questions rule is canonical
  in workflow.md's Rules list; the old tail "decisions get made, recorded, and moved past" restated
  that rule and was trimmed.

## Boundaries

- **Why the context budget is instantiated, not just cited:** workflow.md owns the umbrella rule;
  dev's bullet pins the dev-specific reads (resume detection touches each in-flight `progress.md`
  and nothing else; the preflight reads `brief.md` exactly once) so resume detection never becomes a
  crawl of the whole `.wi/` tree.
- **Why mid-run input is routed:** the run never derails on input, and input never vanishes. The
  three routes keep the design gate the only re-opening point: in-scope work joins `tasks.md`,
  out-of-scope work becomes a roadmap row, and only a contradiction of the approved design re-opens
  the gate.
- **Why "keep dev thin":** dev stays loaded for the entire run, so logic concentrated here is paid
  for on every turn; sequencing lives in dev, work lives in the phase skills, and persistence lives
  in the keep-alive loop.
