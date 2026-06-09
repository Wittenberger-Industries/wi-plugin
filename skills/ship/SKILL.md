---
name: ship
description: >
  Take a built goal through the verification gate and out as a clean, reviewed pull request. Use this
  skill when the user says "/wi:ship", "ship it", "open the PR", "wrap this up", "finish the branch", or as
  the final phase of the loop (autonomous). It runs the repo's real test/lint/typecheck gate, self-reviews against the
  spec's acceptance criteria and pitfalls, writes the PR description, opens the PR autonomously,
  and cleans up the worktree. Soft-integrates superpowers' verification-before-completion,
  requesting-code-review, and finishing-a-development-branch when installed.
---

# ship — verify, review, PR

The whole loop has been building toward a change that's safe to merge. Ship's job is to *prove* it and
package it — never to rubber-stamp. Nothing here weakens to make the gate pass; if the gate is red, the
goal isn't done.

Inputs: the goal branch/worktree, `spec.md` (acceptance criteria), `pitfalls.md`, `constitution.md`,
`repo-map.md`.

## 1 · Verification gate (must be green)

Run the full gate from `${CLAUDE_PLUGIN_ROOT}/skills/ship/references/verification-gate.md`: the complete
test suite, lint, format check, typecheck, and any CI-equivalent command from `repo-map.md`. Every
acceptance criterion in `spec.md` must map to something that actually passed. If `superpowers:verification-before-completion`
is in your available skills you MUST run it too (log it). A red gate stops the ship — fix the code (loop
back to build), don't lower the bar.

## 2 · Review against intent

Self-review the diff with fresh eyes, specifically against:
- **Acceptance criteria** in `spec.md` — each one met and demonstrably so.
- **Pitfalls** in `pitfalls.md` — each applicable one actually handled (and covered by a test where it
  matters).
- **Constitution** — style, boundaries, no secrets, no stray scope.

**Delegation check:** if `superpowers:requesting-code-review` is in your available skills you MUST run
the review through it (log `review via superpowers:requesting-code-review`); unaided self-review is the
fallback only when it's absent.
Address findings before proceeding; note anything deliberately deferred.

## 3 · Sync docs & architecture

The feature is built and verified — make the docs match reality before the PR. Update what this change
*actually* affected; don't blanket re-document.
- **Architecture diagram:** if the change added or removed a module, dependency, layer, or external
  service, update `.wi/architecture.md` (the mermaid graph + legend) to match. If it doesn't exist yet
  (e.g. a greenfield project's first feature), create it now from the new structure using scan's template.
  Then validate it for real before committing:
  `python3 ${CLAUDE_PLUGIN_ROOT}/skills/scan/scripts/check_mermaid.py .wi/architecture.md` — the bundled
  checker catches reserved-word node IDs, unquoted labels, and unbalanced `subgraph`/`end` (and renders
  via `mmdc` when available). Fix every error it reports.
- **Project overview & commands:** if organization, stack, or run steps changed, update `.wi/overview.md`;
  if the command list changed, update `.wi/repo-map.md`.
- **Repo docs the change touched or staled:** READMEs, `docs/`, public-surface docstrings/examples that
  are now wrong. Scope strictly to docs made stale *by this change*, not the whole tree.
- **Glossary:** fold in any new domain term the build introduced.

Commit the doc updates with the feature (`docs(<slug>): …`) so the PR carries current docs. Honest docs
are cheap to keep now and expensive to reconstruct later.

## 4 · Tidy the history & the goal dossier

- Ensure each commit is coherent (`<type>: <subject>`). Squash only if the project prefers a single commit
  per PR (check the constitution).
- Confirm no generated files, large blobs, or secrets slipped in.
- **Repo tree clean:** `git status` must show only the changes you mean to ship. Delete any verification
  scratch — one-off sanity scripts, probe files, generated artifacts (e.g. a `_sanity_export.py` written
  to run an export check). Throwaway probes belong in a temp dir outside the repo, or get removed before
  the PR. A stray scratch file in the diff is a defect.
- **Tidy the dossier** (do this BEFORE cutting the PR, so the PR carries a clean `.wi/`):
  1. *Sweep strays:* every goal-specific file must live under `.wi/goals/<slug>/`. Anything this run left
     loose in `.wi/` or elsewhere (scratch notes, drafts, working files) moves into the slug folder or is
     deleted if worthless. Project-level files stay where they are: `constitution.md`, `repo-map.md`,
     `overview.md`, `architecture.md`, `glossary.md`, `roadmap.md`, `adr/`, `learnings/`.
  2. *Prune the ephemera:* delete `research/` working notes — their value must already be distilled into
     the ADR and `spec.md`; if something in them is still load-bearing, that's a sign to fold it into the
     ADR first. (Skip pruning if the constitution says to keep research notes.)
  3. *What remains is the fixed dossier:* `progress.md`, `brief.md`, `spec.md`, `tasks.md`,
     `pitfalls.md`, `tokens.md`, `PR.md` — seven small files, the durable record of the goal.
  4. Commit it: `chore(<slug>): tidy goal dossier`.

## 5 · PR description

Write it from the goal's own artifacts — they were made for exactly this. Template:

```markdown
## <type>: <goal title>

### Summary
<2-4 sentences: what changed and why. Pulled from spec.md Summary.>

### Acceptance criteria
- [x] <criterion 1>  (verified by <test/command>)
- [x] <criterion 2>

### Changes
- <key change 1>
- <key change 2>

### Testing
<what was run and the result: test suite, lint, typecheck. Note new tests added.>

### Risk & rollout
<feature flag? migration order? back-out plan. From spec.md Rollout.>

### Decisions
<link any ADRs: .wi/adr/ADR-NNNN-*.md>
```

## 6 · Open the PR (autonomous)

The user chose hands-off-to-PR, so open it without asking. If `gh` is available:
`gh pr create --title "<…>" --body-file <description>` (add `--draft` if the run ended blocked or
partial). If `gh` isn't available, push the branch (`git push -u origin wi/<slug>`) and write the
PR-ready description plus a one-line create-PR command into `progress.md` for the user. **Never
force-push.** If `superpowers:finishing-a-development-branch` is installed, use it for the close-out.

## 7 · Close out

After the PR is open (or merged), clean up: remove the worktree and delete the merged branch (see the
worktree reference), set `progress.md` Phase = `done`, and add a final Log line with the PR link. If a
`roadmap.md` exists, mark this goal done and surface the next one.

Then deliver the **final run report** in the console: the approach (cite ADR-NNNN), what was built, the gate
results, the PR URL, and the **token table** compiled from `tokens.md`. **Subagent rows are exact** (from
completion notifications) — that sum is the real, measurable cost of the delegated work; report it as the
headline.

For the **orchestrator (main-thread)** total, run the bundled transcript parser — the model can't read its own
running total mid-turn, but the harness records per-turn `usage` in the session transcript:
`python3 ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/token_report.py` (auto-detects the active session transcript
under `~/.claude/projects/`; pass the path if you know it). Write its output into `tokens.md` as the
**Orchestrator** section (token consumption: output + fresh input + cache write/read) — **the parsed transcript is the
only reliable orchestrator measure.** **If the script fails** (no transcript or no `usage`), report the
orchestrator total as **unavailable for this run** and keep the **subagent-exact sum** as the headline. Do
**not** fall back to any unreliable substitute and do **not** fabricate an overhead figure. The two numbers wi
trusts: **subagent-exact** (completion notifications) and **orchestrator-from-transcript** (this script). If a keep-alive loop is armed (Claude/Codex `/goal` or Copilot Autopilot), this is the state in which its condition holds and the loop clears.

## 8 · Compound — capture what's worth remembering

Before the goal is truly done, harvest the **non-obvious** knowledge from this run while context is fresh
— this is the one thing that compounds wi across goals. Write project-level `.wi/learnings/<slug>.md`
(committed; create the dir lazily). The bar is strict: only things that would have *saved real time if
known up front*:
- a constraint or dependency that wasn't in any doc and bit the run;
- an approach that looked right but failed, and why;
- a non-obvious, reusable pattern or gotcha (stack quirk, CI surprise, test-harness trap).

Do **not** record what's already obvious from the code, the constitution, or the PR ("we added X"). If
nothing clears the bar, write one line saying so — most small goals won't have much.

**Feed it back.** If a learning contradicts or extends a project file, update the source of truth, not
just the note: a confirmed new rule → `constitution.md`; a corrected stack fact → `repo-map.md`; a
resolved term → `.wi/glossary.md`. That is how the next goal starts smarter.

```markdown
---
goal: <slug>
date: <YYYY-MM-DD>
tags: [<area>, ...]
---
# <goal title> — learnings
## What didn't work
## Non-obvious decisions
## Gotchas / patterns to reuse
```

## Offer

If the change is the kind that recurs (a release, a periodic check), mention that wi's loop can be
re-run per goal — and that the user can keep `.wi/roadmap.md` as the running backlog.
