---
type: Design Notes
title: "wit-task-runner: design rationale (maintainer notes)"
description: The "why" behind agents/wit-task-runner.md's rules, relocated out of the loaded charter by #41 (the runtime never reads this file); each entry is anchored to the charter section it explains.
timestamp: 2026-07-11
tags: [wit-task-runner, agents, design-notes, context-budget]
---

# wit-task-runner: design rationale (maintainer notes)

`agents/wit-task-runner.md` is an autonomous agent charter, loaded whole into every task-runner
dispatch (build sends a fresh runner per task, waves of them per build), so it carries rules only.
The rationale lives here, anchored to the section it explains. When editing the charter, keep this
file in sync; a rule whose "why" is deleted instead of relocated loses its guard against future
"simplification".

## Intro

- **Why the dispatch-contents sentence was relocated:** "You are dispatched with the task block, the
  relevant constitution rules, and the repo's commands" described what every dispatch already
  contains; the canonical statement of dispatch contents is build:2 and the task-runner prompt
  skeleton in `skills/build/references/worktrees-and-subagents.md`. At runtime the runner acts on
  the actual dispatch in its prompt, not on a description of it, and on platforms without named
  agents the charter is pasted directly above that same skeleton.
- **Why one task per runner:** a fresh runner per task keeps context from rotting across a long
  build (build:2); every scoping rule in the charter exists to keep parallel siblings safe and the
  report trustworthy.

## Your loop

- **Why lint/typecheck run scoped to the touched files (step 4):** a repo-wide sweep can trip over
  sibling runners' in-flight files; parallel runners share the feature worktree, so a full-tree
  lint fails on half-written files this task never touched. The orchestrator owns the full gate at
  the wave boundary (build:2's wave-end gate), so a runner-level sweep adds noise, not safety.
- **"Reading is not progress" (the 5+ reads stop):** exploration feels like work while producing
  nothing; the one-line say-why forces the runner to convert context into a change or an honest
  blocked report instead of another read.
- **Why the narration paragraph cites instead of restating:** the canonical statement is
  `references/compact-reasoning.md`, including the reason it matters for subagents: a runner's
  transcript is discarded, only the short report survives, so verbose monologue is pure overhead.

## Rules

- **Frontend bullet:** the canonical rule, with the alternate design skills and the install-id
  note, is integrations.md "Frontend work" (`skills/research/references/integrations.md`); the
  charter keeps only the runner's contract. Building "through the skill", not from memory, is the
  intent behind "never build UI blind": markup from memory defeats the installed design skill. The
  exact report strings matter because the orchestrator logs the line to `progress.md` (build:2;
  runners never write that file) and ship's checker greps that log for `frontend via
  frontend-design` vs `frontend via wit fallback` to flag UI built blind while the skill was
  installed.
- **Fix vs. escalate:** "don't quietly redesign" was folded into STOP-and-ask; it is the same
  prohibition stated twice. `references/models.md` cites this bullet as the escalation contract
  (architectural decisions stop and ask the orchestrator), deliberately independent of
  model-routing config, so keep the stop-and-ask wording recognizable.
- **Why every fix is flagged:** a silent fix is as bad as a silent skip; an unreported deviation
  escapes review exactly like unreported missing work. The orchestrator records flagged fixes under
  "Decisions / blockers" in `progress.md`, which is how deviations survive into ship's review.
- **Auto-fix cap (3):** bounded attempts stop a failure loop from burning the build's budget; when
  a task stays stuck, build:3 switches to a systematic debugging pass instead of more retries. The
  orchestrator mirrors reported "Deferred Issues" into `progress.md`, so a capped failure stays
  visible to ship's gate rather than being silently retried.
- **Other tasks are not your backlog:** a sibling runner may own the related work in the same wave;
  doing it here races that sibling on files the DAG deliberately kept disjoint.
- **Auth wall sets `auth-gate`, not `blocked`:** the distinct status exists so the keep-alive loop
  can pause cleanly and resume after the human acts; build:2 records the exact unblock steps in
  `progress.md` and does not retry the runner as a failure.
- **Shared-worktree landmines:** this list is the canonical statement. Both
  `skills/build/references/worktrees-and-subagents.md` ("pinned once", echoed by the prompt
  skeleton) and `skills/rpa/references/build-uipath.md` ("one statement, both flows") point here;
  edit the list in the charter, never fork it.

## Report

- **Why the self-check gates on file state, not console output:** the console narrative routinely
  runs ahead of repo state, so existence checks plus the exact Verify command are the evidence; wit
  gates on file state, not on what the console printed. build:2 applies the same principle from the
  orchestrator side ("no matter what the console printed") when it honors the `Self-Check` line.
- **Why the runner never touches `progress.md`:** the orchestrator is its single writer during
  build, so ticks and commits stay serialized across parallel runners. It also logs the report's
  notes when it ticks the checkbox, which is why the Notes field is worth filling honestly.
- **Why the report is the whole interface:** a tight, honest report is the whole point of the
  charter; the orchestrator acts on it without reading the runner's transcript, so anything not in
  the report never happened.
- **Why the last line is an ALL-CAPS marker:** the `## TASK COMPLETE` / `## TASK BLOCKED` /
  `## TASK AUTH-GATE` line is machine-detected by the orchestrator and the keep-alive loop; exactly
  one, matching the status line, or the outcome cannot be parsed (build:2 pauses cleanly on
  `## TASK AUTH-GATE` instead of retrying it as a failure).
