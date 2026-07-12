---
type: Design Notes
title: "ship: design rationale (maintainer notes)"
description: The "why" behind ship/SKILL.md's rules, relocated out of the loaded skill by #41 pass 1 (v1.9.1); the runtime never reads this file; each entry is anchored to the step it explains.
timestamp: 2026-07-11
tags: [ship, design-notes, context-budget]
---

# ship: design rationale (maintainer notes)

`skills/ship/SKILL.md` is loaded wholesale and re-read ~75× per run, so it carries rules only. The
rationale lives here, anchored by step. When editing the skill, keep this file in sync: a rule whose
"why" is deleted instead of relocated loses its guard against future "simplification".

## Intro

- **Mission.** The whole loop has been building toward a change that's safe to merge; ship's job is to
  *prove* it and package it. That's why nothing in the skill may weaken to make a gate pass: a gate
  that bends is not a gate.
- **The engage stamp** exists so the invocation is auditable and the build→ship transition is timed
  like every other phase flip: `token_report.py` computes phase spans from these Log stamps, which is
  also why every stamp must be full ISO-8601 from the OS clock, never date-only or guessed.

## ship:1 (verification gate)

- **Why logs stay on disk:** the log file is the evidence and stays re-openable; the transcript keeps
  only the verdict (exit code + tail). This is workflow.md's output house rule applied: restating it
  in full inside ship was belt-and-suspenders and was trimmed; the citation is the rule.

## ship:2 (review)

- **Why the cross-provider script can't replace the checker:** `cross_review.py` only receives the
  diff + spec text (no Read/Grep/Bash against the repo) so it cannot verify anything is actually
  *wired*. That asymmetry is why it never writes `verification.md` and is a layer on top of the
  checker, never a replacement, and why its exit codes govern only whether the layer runs.
- **Why the checker dispatch is unconditional:** the temptation under cross-provider or MoA
  configuration is to treat the extra reviews as substitutes; they are opinions, not repo-verified
  results.

## ship:3 (docs sync)

- **Why now:** honest docs are cheap to keep current at ship time and expensive to reconstruct later;
  syncing pre-PR means the PR carries the update and review sees it.
- **What check_mermaid.py catches:** reserved-word node IDs, unquoted labels, unbalanced
  `subgraph`/`end`; renders via `mmdc` when available. The skill only mandates "run it, fix every
  error"; the catch-list lives here.

## ship:4 (compound)

- **Why this step exists:** harvesting non-obvious learnings is the one thing that compounds wit across
  features, and feeding a learning back into constitution/repo-map/glossary (not just the note) is
  how the next feature starts smarter. Done before the PR so the knowledge rides the branch and
  reaches the team through review.

## ship:5 (PR description)

- **Why a file, not console output:** the feature's artifacts were made for exactly this; a committed
  `PR.md` survives the run, is consumable by `gh pr create --body-file`, and lets a human open the PR
  by hand if the run couldn't. The dossier is the durable record of the feature.

## ship:6 (tidy)

- **Why `git rm -f` for tracked ephemera:** the ship:2 result-mode checker refreshed
  `verification.md` *after* the commit that last touched it, so a plain `git rm` refuses on the local
  modifications.
- **Why `cross-review.md` is plain-deleted:** it is written at ship:2 and typically never committed:
  untracked, so `git rm` has no pathspec to match. Same for `.logs/` (self-gitignored by design).
- **Why the manifest is read from the directory reference, not memory:** the dossier is the durable
  record; `PR.md` was written in ship:5, so the tidy commit is the one that carries the complete
  dossier into the PR.

## ship:7 (open the PR)

- **Why the awk pipeline is written the way it is:** `mktemp` + `awk` assumes a POSIX shell: Git Bash
  on Windows, which Claude Code provides; it is not guaranteed under Copilot CLI. The leading
  `{sub(/\r$/,"")}` keeps the frontmatter strip CRLF-safe on a `core.autocrlf=true` checkout, where
  the `---` delimiters arrive as `---\r` and a bare line compare would miss them.
- **Why worktree/branch mechanics are never delegated:** wit's sibling-dir worktrees
  (`../<repo>-wit-<slug>`) fail `superpowers:finishing-a-development-branch`'s `.worktrees/`-only
  provenance rule; that skill is consulted only for the close-out *decision* in interactive runs.
- **Why "impossible ≠ failed" for no-remote repos:** looping on `git push`/`gh pr create` in a
  local-only repo burns the run on an unsatisfiable step; the recorded recovery pair makes the branch
  merge-ready the moment a remote appears.

## ship:8 (remote checks & close-out)

- **Why the evidence lands in `progress.md`:** `verification.md` was pruned at ship:6 and `PR.md` was
  committed before the push, so neither can carry evidence that only exists after the PR opens.
- **Why cleanup follows the remote gate:** a red-check fix loop needs its workspace; removing the
  worktree first would strand the fix rounds.
- **Why the `.logs` re-create is self-gitignored:** a red-path fix commit must never be able to stage
  CI logs (the output house rule's no-logs-in-history contract).
- **Why accepted red must be surfaced to the user:** the keep-alive condition's predicate names green
  checks, so accepting red leaves it permanently unsatisfiable; only the user can clear the `/goal`
  or stop the Autopilot loop.
- **Why the checklist earns Phase = done:** the console narrative routinely runs ahead of repo state;
  each box is checked against the repo, and the check_tokens.py exit code (not eyeballing the file) is
  the machine-checkable close-out condition the keep-alive loop waits on.
- **Why local and remote status are reported separately:** one undifferentiated "green" hides which
  gate actually ran; the two trusted token numbers (subagent-exact, orchestrator-from-transcript) are
  kept distinct for the same reason.
