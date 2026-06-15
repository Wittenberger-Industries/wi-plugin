---
type: Skill
name: ship
description: >
  Take a built goal through the verification gate and out as a clean, reviewed pull request. Use this
  skill when the user says "/wi:ship", "ship it", "open the PR", "wrap this up", "finish the branch", or as
  the final phase of the loop (autonomous). It runs the repo's real test/lint/typecheck gate, self-reviews against the
  spec's acceptance criteria and pitfalls, harvests learnings into the .wi/learnings.md index, finalizes
  the tokens.md ledger before the dossier commit, writes the PR description to the goal's PR.md, opens the
  PR autonomously, and closes out against a hard checklist. Soft-integrates superpowers' verification-before-completion,
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

**Goal-level check (checker · result mode).** Dispatch the **checker** (`agents/checker.md`) in `result`
mode against `spec.md`'s acceptance criteria + locked decisions (ADRs, constitution); it confirms each is
delivered and **wired**, not just present, refreshing `verification.md`. This is goal/coverage-level,
distinct from the line-level review above. A result-mode **BLOCKER** — an unmet criterion, or a decision
silently reduced to a stub — sends the goal **back to build**; ship never opens the PR on a goal the
checker says isn't met.

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

## 4 · Compound — capture what's worth remembering

Harvest the **non-obvious** knowledge from this run while context is fresh — this is the one thing that
compounds wi across goals. Do it **now, before the PR**, so the learnings ride the branch and reach the
team through review. The bar is strict: only things that would have *saved real time if known up front*:
- a constraint or dependency that wasn't in any doc and bit the run;
- an approach that looked right but failed, and why;
- a non-obvious, reusable pattern or gotcha (stack quirk, CI surprise, test-harness trap).

Do **not** record what's already obvious from the code, the constitution, or the PR ("we added X").

Two tiers, one index:
1. **Substantial learnings** get their own file `.wi/learnings/<slug>.md` (create the dir lazily):

   ```markdown
   ---
   type: Learning
   title: <goal title> — learnings
   description: <one-line hook — the gotcha/pattern worth recalling next goal>
   goal: <slug>
   timestamp: <YYYY-MM-DD>
   tags: [<area>, ...]
   ---
   # <goal title> — learnings
   ## What didn't work
   ## Non-obvious decisions
   ## Gotchas / patterns to reuse
   ```

2. **The index `.wi/learnings.md`** (create lazily) is updated **every goal** — it is how later phases
   recall learnings without opening every file. One line per learning, hook included:

   ```markdown
   ---
   type: Learnings Index
   title: Learnings index — <project>
   description: One line + hook per goal; phases read this, then open a detail file only when its hook fits.
   timestamp: <YYYY-MM-DD>
   ---

   # Learnings index

   - [<goal title>](learnings/<slug>.md) — <one-line hook: the gotcha/pattern in ~10 words>
   - <slug> (<YYYY-MM-DD>) — nothing above the bar
   ```

   A goal with no substantial learnings gets the one-liner directly in the index and **no** detail file.

**Feed it back.** If a learning contradicts or extends a project file, update the source of truth, not
just the note: a confirmed new rule → `constitution.md`; a corrected stack fact → `repo-map.md`; a
resolved term → `.wi/glossary.md`. That is how the next goal starts smarter.

Commit: `docs(<slug>): learnings` (or fold into the docs-sync commit).

## 5 · Tidy the history & the goal dossier

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
     `overview.md`, `architecture.md`, `glossary.md`, `roadmap.md`, `adr/`, `learnings.md`, `learnings/`.
  2. *Prune the ephemera:* delete `research/` working notes **and the checker's `verification.md`** —
     their value must already be distilled (research → the ADR and `spec.md`; the verification verdict →
     the `### Verification` block in `PR.md`). If something in them is still load-bearing, fold it in
     first. (Skip pruning if the constitution says to keep them.)
  3. *Finalize `tokens.md` — NOW, not at close-out.* The file must be complete **inside the dossier
     commit**, or it never rides the PR. Run the bundled transcript parser — the model can't read its own
     running total mid-turn, but the harness records per-turn `usage` in the session transcript:
     `python3 ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/token_report.py` (auto-detects the active session
     transcript under `~/.claude/projects/`; pass the path if you know it). **Write its output into
     `tokens.md`**, replacing the `## Orchestrator` placeholder — the parsed transcript is the only
     reliable orchestrator measure. Then write the **Subagents (exact)** sum line from the ledger rows.
     **If the script fails** (no transcript or no `usage`), write `Orchestrator: unavailable for this run`
     in that section — never substitute, estimate, or fabricate. Printing the report to the console does
     **not** count as done: the file is the deliverable; the console report at close-out is read *from* it.
  4. *What remains is the fixed dossier:* `progress.md`, `brief.md`, `spec.md`, `tasks.md`,
     `pitfalls.md`, `tokens.md`, `PR.md` — seven small files, the durable record of the goal (`PR.md` is
     written in the next step, before this commit is pushed).
  5. Commit it: `chore(<slug>): tidy goal dossier`.

## 6 · PR description — write `.wi/goals/<slug>/PR.md`

Write it from the goal's own artifacts — they were made for exactly this. The description is a **file,
not console output**: save it as `.wi/goals/<slug>/PR.md` and commit it (`docs(<slug>): PR description`).
It is part of the seven-file dossier and exists **whether or not** a PR can be opened this run — it is
what `gh pr create --body-file` consumes, and what a human uses if they must create the PR by hand. It
opens with OKF frontmatter (`type: PR Description`); the PR **body** is everything *below* that
frontmatter, so the frontmatter is stripped before feeding `gh` (§7) — it's dossier metadata, not PR text.
Template:

```markdown
---
type: PR Description
title: <goal title>
description: <2-4 word summary of the change>
goal: <slug>
timestamp: <YYYY-MM-DD>
---

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

### Verification
<checker result-mode verdict: every acceptance criterion + locked decision delivered and wired; any waived
findings with severity. Distilled from verification.md, which is pruned at close-out.>

### Risk & rollout
<feature flag? migration order? back-out plan. From spec.md Rollout.>

### Decisions
<link any ADRs: .wi/adr/ADR-NNNN-*.md>
```

## 7 · Open the PR (autonomous)

The user chose hands-off-to-PR, so open it without asking. Push the branch
(`git push -u origin wi/<slug>`), strip PR.md's OKF frontmatter into a throwaway body file (outside the
repo, so the dossier stays clean), then open the PR from it:

```bash
body=$(mktemp)
awk 'NR==1&&$0=="---"{f=1;next} f&&$0=="---"{f=0;next} !f' .wi/goals/<slug>/PR.md > "$body"
gh pr create --title "<…>" --body-file "$body"   # add --draft if the run ended blocked or partial
rm -f "$body"
```

Log the PR URL in `progress.md`.

**A pushed branch is not a shipped goal.** If `gh` is unavailable or `pr create` fails, the run is **not
done**: record in `progress.md`'s Decisions/blockers the exact recovery command (frontmatter-stripped, as
above) —
`body=$(mktemp); awk 'NR==1&&$0=="---"{f=1;next} f&&$0=="---"{f=0;next} !f' .wi/goals/<slug>/PR.md > "$body"; gh pr create --title "<…>" --body-file "$body"`
— plus the failure reason, and tell the user in the final report that the PR still needs creating. Never silently stop at the push. **Never
force-push.** If `superpowers:finishing-a-development-branch` is installed, use it for the close-out.

## 8 · Close out — checklist, then the report

After the PR is open (or merged), clean up: remove the worktree and delete the merged branch (see the
worktree reference). Then run the **close-out checklist** — every box, against the actual repo state, not
memory. `progress.md` Phase = `done` is **earned by this checklist**; an unticked box means ship is not
finished, no matter what the console already said:

- [ ] PR is **open** and its URL is logged in `progress.md` (sole substitute: branch pushed + failure
      reason + the frontmatter-stripped `gh pr create …` recovery command (§7) recorded as a blocker)
- [ ] `.wi/goals/<slug>/PR.md` exists and is committed on the branch
- [ ] `tokens.md` has the subagent ledger rows **and** a finalized `## Orchestrator` section (parsed
      figure or explicit `unavailable`) — verify by reading the **file**, not the console log
- [ ] `.wi/learnings.md` index has this goal's line (and the detail file exists if one was warranted)
- [ ] dossier = exactly the seven files; `research/` pruned; no strays anywhere in `.wi/`
- [ ] worktree removed; merged branch deleted

All green: set Phase = `done`, add a final Log line with the PR link, and if `roadmap.md` exists mark this
goal done and surface the next one.

Then deliver the **final run report** in the console: the approach (cite ADR-NNNN), what was built, the
gate results, the PR URL, and the **token table read from the finalized `tokens.md`** — the file was
completed back in the dossier tidy; do not recompute it here. **Subagent rows are exact** (from completion
notifications) — that sum is the real, measurable cost of the delegated work; report it as the headline,
with the orchestrator figure (or `unavailable`) alongside. The two numbers wi trusts: **subagent-exact**
(completion notifications) and **orchestrator-from-transcript** (`token_report.py`). If a keep-alive loop
is armed (Claude/Codex `/goal` or Copilot Autopilot), the checklist passing is the state in which its
condition holds and the loop clears.

## Offer

If the change is the kind that recurs (a release, a periodic check), mention that wi's loop can be
re-run per goal — and that the user can keep `.wi/roadmap.md` as the running backlog.
