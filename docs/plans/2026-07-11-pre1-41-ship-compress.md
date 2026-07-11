---
type: Implementation Plan
title: "PR E1 — #41 pass 1: compress skills/ship/SKILL.md (v1.9.1)"
description: Rules-first rewrite of the largest loaded skill (423 lines) — imperative rules and exact contract strings stay byte-meaningful, inline rationale moves to docs/wi-design-notes/ship.md (not loaded at runtime); ship:N numbering and every cross-file-cited string preserved; verified by rules inventory, load-alone Q&A, and a removed-behavior audit.
timestamp: 2026-07-11
tags: [context-budget, careful-refactor, docs, plan]
---

# PR E1 — #41 pass 1: ship (v1.9.1)

> **For agentic workers:** judgment-heavy prose surgery on one file. "Tests" are the rules
> inventory below (before == after), `scripts/validate.py`, `pytest tests/`, grep assertions on
> contract strings, load-alone Q&A subagents, a removed-behavior audit, and file-tail checks.

**Goal:** first #41 pass — `skills/ship/SKILL.md` (423 lines, the heaviest loaded skill; re-read
~75×/run). Tighten to imperative rules; relocate the "why" to `docs/wi-design-notes/ship.md`
(repo doc, not loaded at runtime), linked by one line. Baseline: `main@a83af88` (v1.9.0).

**Why patch:** pure compression/relocation, zero behavior change → **v1.9.1**, three manifests.

## Hard constraints (what must survive byte-meaningful)

1. **`ship:N` numbering** — inbound citations exist for ship:1,2,4,5,6,7,8 (and in-file
   self-cites); all eight `## N ·` headings keep their numbers and order; ship:6's numbered
   sub-list (1–5) keeps its numbering.
2. **Parsed/logged contract strings, verbatim:** the engage Log line
   `- <ts> **Update** phase = ship (ship engine engaged (wi <version>))`; the PR Log line
   `- <ts> **Update** PR opened: <url>` (token_report.py reads this exact wording as a span
   boundary); `- <ts> **Update** phase = done`; review-log strings
   (`review via wi-code-checker + superpowers:requesting-code-review[inline]`,
   `review via wi-code-checker (wi line review; superpowers absent)`,
   `+ MoA (<N> proposers, <L> layers, aggregator <tier>)`,
   `cross-provider layer skipped (<reason>)`); dispatch markers (`Line review template: <path>`/
   `none`, `MoA role: proposer <i>/<N>`, `MoA role: aggregator`); remote-checks evidence strings
   (`remote checks: N/N green`, `remote checks: none configured`,
   `remote checks: red — accepted by user (<reason>)`,
   `remote checks: pending after <timeout> (<names>)`); `Close-out: local (no remote)`.
3. **Commands + code blocks, verbatim:** now.py, check_mermaid.py, token_report.py `--write`,
   check_tokens.py, both mktemp+awk frontmatter-strip pipelines, the `.logs` re-create line
   (`mkdir -p … && printf '*\n' > ….gitignore`), `gh pr checks … --watch --fail-fast`,
   `gh run view <run-id> --log-failed`, `git push -u origin wi/<slug>`.
4. **Templates, verbatim:** Learning file, Learnings index, PR.md, the timing table block.
5. **Commit formats:** `docs(<slug>): …` / `docs(<slug>): learnings` / `docs(<slug>): PR
   description` / `chore(<slug>): tidy feature dossier`.
6. **Numbers:** max 2 review→fix rounds (shared), max 2 remote-fix rounds, ~15 min checks
   timeout (constitution may override), ~2 min no-checks window, close-out checklist = 7 boxes.
7. Frontmatter (trigger description) unchanged.

## Rules inventory (before — each must hold after; the after-column rides in the PR body)

Intro: I1 never weaken the gate to pass / red gate = not done; I2 inputs = branch/worktree +
spec + pitfalls + constitution + repo-map; I3 context budget: artifacts by section, diff as
--stat+hunks, command output as exit code+tail, checker re-reads the repo — not the orchestrator;
I4 first act = engage Log line (exact format, OS-clock ISO stamp, version from plugin.json).

ship:1: G1 run the full gate per references/verification-gate.md (suite, lint, format, typecheck,
CI-equivalent from repo-map); G2 every gate command redirected per the output house rule to
`.logs/gate-<step>.txt`, verdict = exit code + tail, failures by grep; G3 every spec.md AC maps
to something that passed; G4 superpowers:verification-before-completion MUST run if available
(logged; delegation point, integrations.md precedence); G5 red → back to build, never lower the bar.

ship:2: R1 self-review diff (--stat, then only needed hunks; never whole-diff) against AC /
pitfalls / constitution; R2 resolve line-review source before dispatch (Glob the superpowers
reviewer template → absolute path, else `none`) + the two exact log strings; R3 dispatch
wi-code-checker result mode — always, one dispatch two passes (feature-level delivered-and-wired
+ line-level from template/built-in), findings → verification.md (BLOCKER/WARNING/INFO), checker
tier from the resolved-routing block else inherit, unconditional — nothing demotes/replaces it;
R4 MoA layer only when the block's MoA row has `review` in points: N proposers parallel,
IDENTICAL prompts + `MoA role: proposer <i>/<N>`, return-only (never write verification.md);
`layers: 2` → refinement round on the union (may change position, must say why); one aggregator
(`MoA role: aggregator`, aggregator tier) dedupes, keeps MAX severity, verifies against the repo
before dropping false positives, alone writes verification.md; append the `+ MoA (…)` log suffix;
every proposer/aggregator appends its own tokens.md row with Duration; a full MoA pass = one
round; row `none` / no `review` point → single dispatch; R5 cross-provider layer only when the
block names a provider ≠ none and the key exists: cross_review.py on diff+spec →
cross-review.md; never writes verification.md, layer never replacement; unconfigured/exit 2/
exit 3 → skip + log the exact string, checker ran regardless; R6 findings from all layers feed
one loop: BLOCKER → back to build, max 2 review→fix rounds shared, leftovers go with severity
into PR.md Verification, a BLOCKER from any layer blocks the PR, never open a PR on a feature
the checker says isn't delivered; cross-review.md is ephemeral (pruned ship:6 after ship:5
distills); R7 address findings before proceeding, note deliberate deferrals.

ship:3: D1 update only what the change affected (no blanket re-doc); D2 architecture.md updated
on module/dependency/layer/service change — create from scan's template if absent (absence =
greenfield; scan docs are committed where written); D3 validate with check_mermaid.py and fix
every error (python fallback: workflow.md "Script invocation" — holds for all SKILL scripts);
D4 overview.md on org/stack/run-step change, repo-map.md on command change; D5 repo docs staled
by this change only; D6 glossary gets new domain terms; D7 commit `docs(<slug>): …` so the PR
carries current docs.

ship:4: C1 harvest now, before the PR (learnings ride the branch); C2 strict bar — only
would-have-saved-time-up-front items (undocumented constraint that bit; failed approach + why;
non-obvious reusable gotcha); C3 never record the obvious; C4 substantial → learnings/<slug>.md
(exact template, dir lazily); C5 index .wi/learnings.md updated EVERY feature (exact template),
one line + hook; no-learnings feature = one-liner in index, no detail file; C6 feed back to the
source of truth (constitution / repo-map / glossary); C7 commit `docs(<slug>): learnings` or fold
into docs-sync.

ship:5: P1 PR.md written from the feature's artifacts; P2 a committed file, never console output
(`docs(<slug>): PR description`); P3 exists whether or not a PR can be opened — consumed by
`gh pr create --body-file`, or by a human; P4 OKF frontmatter is dossier metadata — the PR body
is everything below it, stripped before gh (ship:7); P5 the template (verbatim).

ship:6: T1 coherent commits (`<type>: <subject>`); squash only if the constitution prefers;
T2 no generated files / large blobs / secrets; T3 repo tree clean — delete verification scratch
(probes are defects in the diff; temp dir or removed); T4 tidy BEFORE the PR; read `Flow:` from
progress.md (missing = dev) → keys the directory reference (dev: wi-directory.md, rpa:
rpa-directory.md) for whitelist/ephemera/manifest; RPA artifact-name mapping: see rpa:7;
T5 sweep strays into the slug folder (or delete worthless); project-level files stay — whitelist
is the flow reference's project-level list (RPA registries are project files, never strays);
directory reference wins when in doubt; T6 prune exactly the reference's ephemera list, nothing
more; value must be distilled first (fold in if still load-bearing); tracked → `git rm -f`;
never-committed (cross-review.md, `.logs/`) → plain-delete; skip pruning if the constitution
says keep; T7 finalize tokens.md NOW, inside the dossier commit, with the exact token_report.py
--write command (auto-detects transcript, `--transcript`/`--progress` overrides); on parse
failure writes honest `unavailable` (the ledger rule — never substitute/estimate/fabricate);
the file is the deliverable; T8 remaining dossier = the flow's manifest read from the reference,
not memory (dev: seven files; rpa: run dossier + per-process tobe.md); T9 commit
`chore(<slug>): tidy feature dossier`.

ship:7: O1 open the PR without asking (autonomous); push `git push -u origin wi/<slug>`; strip
frontmatter to a throwaway body file OUTSIDE the repo (exact pipeline); `--draft` if blocked/
partial; O2 log the PR URL as the exact `**Update** PR opened: <url>` line (token_report span
boundary); ship:8 verifies remote checks before any cleanup; O3 pushed ≠ shipped: on gh absence
or create failure the run is NOT done — record the exact recovery command + failure reason in
progress.md Decisions/blockers, tell the user, never silently stop at the push; O4 never
force-push; O5 finishing-a-development-branch consulted only for the interactive close-out
decision; autonomous decision is already made (the PR); worktree/branch mechanics stay wi's own
(ship:8) — never delegate the removal (delegation point, integrations.md); O6 no remote at all:
impossible ≠ failed — don't loop; record `Close-out: local (no remote)` + the push/PR recovery
pair, proceed to ship:8 (its PR box passes on the substitute; remote checks: none configured).

ship:8: X1 remote gate before any cleanup — PR checks are the authoritative signal, not the
local gate; X2 re-create the `.logs` dir first if pruned (exact idempotent command; self-
gitignored so a red-path fix commit can never stage CI logs); X3 watch to completion with
`gh pr checks … --watch --fail-fast`, ~15 min default timeout (constitution may override),
redirected to `.logs/pr-checks.txt`, tail = evidence logged to progress.md; X4 no checks after
~2 min AND no CI config anywhere → log `remote checks: none configured` and proceed; X5 green =
every (or every required) check concluded successfully → log `remote checks: N/N green` + names/
conclusions/run URLs in progress.md (the only file that can carry post-push evidence; the report
repeats it); X6 red = run not done, keep-alive unsatisfied: pull failing logs to a FILE
(`gh run view <run-id> --log-failed > ….logs/ci-<run-id>.txt 2>&1`; external check via details
URL), read by grep/tail, fix in the still-present worktree, commit, push, re-watch; max 2
remote-fix rounds; a genuine flake re-runs without consuming a round; budget exhausted:
interactive → user decides (keep fixing / accept red, recorded with the exact string); `--auto`
→ hold the run open (Phase stays ship, keep the worktree, loop re-enters at this gate); NEVER
accept red autonomously; accepted red → the armed keep-alive condition is unsatisfiable — tell
the user to clear the `/goal`/Autopilot themselves; X7 timeout / never-reports = not green: log
the exact pending string, hold like red minus the fix loop, re-entry re-checks cheaply;
X8 cleanup only after the gate lands (green / none / accepted red): remove the worktree (safe
once pushed, or once the dossier commit is on the local branch under no-remote), delete the
LOCAL branch only if fully merged (`git branch -d` refuses otherwise), never delete the remote
branch or an open PR; X9 the 7-box close-out checklist EARNS Phase = done — checked against
repo state, not memory; every box as written (PR open+URL or the two substitutes; remote-checks
evidence; PR.md committed; check_tokens.py exit 0 blocks done — honest `unavailable` passes,
exit code replaces reading by eye; learnings index line; dossier = the flow's manifest, ephemera
pruned, no strays; worktree removed + branch rule); X10 all green → Phase = done + stamped final
Log line + PR link; mark `.wi/roadmap.md` row done and surface the next when it exists;
X11 final run report: approach (cite ADR-NNNN), what was built, local and remote status
SEPARATELY (never one undifferentiated green), PR URL, token table read from the finalized
tokens.md (never recomputed) — subagent-exact headline + orchestrator alongside + cost/split
when present (the two trusted numbers), timing table (verbatim block, `unavailable` prints
as-is); X12 keep-alive condition holds only when the checklist incl. the remote-checks box
passes; exception: user-accepted red stays unsatisfiable, user clears it.

Offer: F1 recurring change → mention the loop re-runs per feature; `.wi/roadmap.md` as backlog.

## What moves to docs/wi-design-notes/ship.md (the "why", by anchor)

Mission prose; audit rationale for the engage stamp; house-rule re-explanations (canonical in
workflow.md); why cross_review.py can't verify wiring; why docs are synced pre-PR; why compound
is the compounding step + feed-back rationale; why PR.md is a file; why `git rm -f` is needed on
verification.md; the POSIX/CRLF explanation of the awk pipeline; why worktree mechanics are
never delegated (sibling-dir vs `.worktrees/` provenance); why progress.md carries remote-check
evidence; why cleanup follows the remote gate; why accepted red wedges the keep-alive predicate.

## Tasks

- [ ] Commit 1: this plan doc.
- [ ] Commit 2: rewritten `skills/ship/SKILL.md` + new `docs/wi-design-notes/ship.md` (+ the
  one-line link) — every inventory rule + hard-constraint string intact.
- [ ] Verify: validate.py + pytest; contract-string grep; inbound `ship:N` grep; tails;
  loaded-token delta (lines/words/chars, ≈tokens); load-alone Q&A subagents ×2; removed-behavior
  audit vs main.
- [ ] Commit 3: bump v1.9.1 (three manifests). Push, PR `Fixes` nothing (pass 1 of #41 — refs
  #41), body carries this inventory + delta + verification results.
