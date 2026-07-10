---
type: Skill
name: ship
user-invocable: false
description: >
  Take a built feature through the verification gate and out as a clean, reviewed pull request. Use this
  skill when the user says "/wi:ship", "ship it", "open the PR", "wrap this up", "finish the branch", or as
  the final phase of the loop (autonomous).
---

# ship — verify, review, PR

The whole loop has been building toward a change that's safe to merge. Ship's job is to *prove* it and
package it — never to rubber-stamp. Nothing here weakens to make the gate pass; if the gate is red, the
feature isn't done.

Inputs: the feature branch/worktree, `spec.md` (acceptance criteria), `pitfalls.md`, `constitution.md`,
`repo-map.md`.

Hold exactly that (workflow.md's **context budget** — `spec.md` + `pitfalls.md` are this phase's
artifacts, read by section where possible): the diff enters as `--stat` + hunks (§2), command output
as exit code + tail (§1/§8), and the checker — not you — re-reads the repo.

First act once engaged: append `- <ts> **Update** phase = ship (ship engine engaged (wi <version>))` to
progress.md's Log — full ISO-8601 stamp from the OS clock (`date -Iseconds` /
`python ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/now.py`), <version> read from
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` — so the invocation is auditable and the
build→ship transition is timed like every other phase flip.

## 1 · Verification gate (must be green)

Run the full gate from `${CLAUDE_PLUGIN_ROOT}/skills/ship/references/verification-gate.md`: the complete
test suite, lint, format check, typecheck, and any CI-equivalent command from `repo-map.md`. Run every
gate command per workflow.md's **output house rule** — redirected to
`.wi/features/<slug>/.logs/gate-<step>.txt`, verdict from the exit code + `tail -n 30`, failures pulled
by grep. The log file is the evidence and stays on disk; the transcript keeps only the verdict. Every
acceptance criterion in `spec.md` must map to something that actually passed. If
`superpowers:verification-before-completion` is in your available skills you MUST run it too (log it) —
a delegation point; see the precedence rule in `skills/research/references/integrations.md`. A red gate
stops the ship — fix the code (loop back to build), don't lower the bar.

## 2 · Review against intent

Self-review the diff with fresh eyes — overview via `git diff --stat`, then open only the hunks a
criterion or finding needs (workflow.md's output house rule: never a whole-diff read) — specifically
against:
- **Acceptance criteria** in `spec.md` — each one met and demonstrably so.
- **Pitfalls** in `pitfalls.md` — each applicable one actually handled (and covered by a test where it
  matters).
- **Constitution** — style, boundaries, no secrets, no stray scope.

**Review dispatch (wi-code-checker · result mode) — always runs; one dispatch, two passes.** Before
dispatching, resolve the line-review source: if `superpowers:requesting-code-review` is in your available
skills, locate its reviewer template — the `code-reviewer.md` inside that skill's installed directory
(Glob the plugin roots, e.g. `~/.claude/plugins/**/requesting-code-review/**/code-reviewer.md`) — and
pass its absolute path in the checker dispatch as `Line review template: <path>`. If it is absent, pass
`Line review template: none`. Log `review via wi-code-checker + superpowers:requesting-code-review[inline]`
or `review via wi-code-checker (wi line review; superpowers absent)`.

Then dispatch **wi-code-checker** (`agents/wi-code-checker.md`) in `result` mode. The dispatch prompt asks
for both passes: the **feature-level result check** — `spec.md`'s acceptance criteria + locked decisions
(ADRs, constitution), each confirmed delivered and **wired**, not just present (the checker reads the
actual repo) — and the **line-level review** of the branch diff, run from the template path above or the
checker's built-in review when `none`. Findings from both passes land in `verification.md` in the
BLOCKER/WARNING/INFO taxonomy. This dispatch is unconditional (on the `checker` tier from
`progress.md`'s resolved-routing block — models.md's resolve-once rule — else inherit); no
cross-provider configuration demotes or replaces it.

**Mixture of Agents layer (only when configured).** If the resolved-routing block's MoA row includes
`review` in its `points` (see `${CLAUDE_PLUGIN_ROOT}/references/moa.md`; the block mirrors
`.wi/models.md`'s `## Mixture of Agents` section), dispatch N
proposer checkers (one per listed `proposers` tier) in parallel, same turn, instead of the one dispatch
above — IDENTICAL prompts (result mode, both passes, the same `Line review template:` line) plus the
marker `MoA role: proposer <i>/<N>`.
Proposers RETURN findings only; they never write `verification.md`. If `layers: 2`, run a second parallel
round: each proposer receives the union of round-1 findings and returns a refinement (may change position;
must say why). Then dispatch one aggregator checker (`MoA role: aggregator`, at the `aggregator` tier): it
receives all findings, dedupes, keeps the MAX severity any proposer assigned, verifies against the repo
before dropping anything as a false positive, and alone writes `verification.md` (both passes' sections,
one verdict marker). Append `+ MoA (<N> proposers, <L> layers, aggregator <tier>)` to the review log line
above (e.g. `review via wi-code-checker + superpowers:requesting-code-review[inline] + MoA (3 proposers, 1 layer, aggregator opus)`);
every proposer and aggregator dispatch appends its own `tokens.md` row (with its `Duration` cell) on
completion. The cross-provider
layer below and the max-2-rounds loop are unchanged — a full MoA pass counts as one round. MoA row
`none`, or `review` not in its `points` → the single dispatch above runs unchanged.

**Cross-provider layer (only when configured).** If the resolved-routing block's cross-provider row
names a provider (≠ `none`) and its API key is present, **additionally** run an independent **cross-provider
diff review** — a second opinion from another model family, a separate optional layer on top of the
checker dispatch — per `${CLAUDE_PLUGIN_ROOT}/references/models.md`: full feature diff + `spec.md` through
`skills/ship/scripts/cross_review.py` → `.wi/features/<slug>/cross-review.md`. The script only receives the
diff + spec text — no Read/Grep/Bash against the repo — so it cannot verify anything is actually wired, and
it never writes `verification.md`: the cross-provider path is a layer on top of checker, never a replacement.
Unconfigured, exit 2 (config/API error), or exit 3 (missing API key) governs only whether this layer runs
— log `cross-provider layer skipped (<reason>)` and continue; the checker dispatch above ran regardless.

Findings from both checker passes and the cross-provider layer feed the same loop: a BLOCKER — an unmet
criterion, a decision silently reduced to a stub, a correctness bug in the diff — sends the feature
**back to build**, **max 2 review→fix rounds** shared across all of it; whatever remains goes with its
severity into `PR.md`'s Verification. A BLOCKER from any layer blocks the PR. `cross-review.md` is
ephemeral (pruned in §6, after §5 distills it into `PR.md`). Ship never opens the PR on a feature
wi-code-checker says isn't delivered.

Address findings before proceeding; note anything deliberately deferred.

## 3 · Sync docs & architecture

The feature is built and verified — make the docs match reality before the PR. Update what this change
*actually* affected; don't blanket re-document.
- **Architecture diagram:** if the change added or removed a module, dependency, layer, or external
  service, update `.wi/architecture.md` (the mermaid graph + legend) to match. If it doesn't exist yet
  (e.g. a greenfield project's first feature), create it now from the new structure using scan's template.
  (Scan's docs are committed where written — `wi-directory.md`'s project-level rule — so a scanned repo's
  worktree already carries them; absence really does mean greenfield.)
  Then validate it for real before committing:
  `python ${CLAUDE_PLUGIN_ROOT}/skills/scan/scripts/check_mermaid.py .wi/architecture.md` — the bundled
  checker catches reserved-word node IDs, unquoted labels, and unbalanced `subgraph`/`end` (and renders
  via `mmdc` when available). Fix every error it reports. (`python` assumed on PATH; where it does not
  resolve, fall back to `py -3` on Windows or `python3` on Linux/macOS — this holds for every script in
  this SKILL.)
- **Project overview & commands:** if organization, stack, or run steps changed, update `.wi/overview.md`;
  if the command list changed, update `.wi/repo-map.md`.
- **Repo docs the change touched or staled:** READMEs, `docs/`, public-surface docstrings/examples that
  are now wrong. Scope strictly to docs made stale *by this change*, not the whole tree.
- **Glossary:** fold in any new domain term the build introduced.

Commit the doc updates with the feature (`docs(<slug>): …`) so the PR carries current docs. Honest docs
are cheap to keep now and expensive to reconstruct later.

## 4 · Compound — capture what's worth remembering

Harvest the **non-obvious** knowledge from this run while context is fresh — this is the one thing that
compounds wi across features. Do it **now, before the PR**, so the learnings ride the branch and reach the
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
   title: <feature title> — learnings
   description: <one-line hook — the gotcha/pattern worth recalling next feature>
   feature: <slug>
   timestamp: <YYYY-MM-DD>
   tags: [<area>, ...]
   ---
   # <feature title> — learnings
   ## What didn't work
   ## Non-obvious decisions
   ## Gotchas / patterns to reuse
   ```

2. **The index `.wi/learnings.md`** (create lazily) is updated **every feature** — it is how later phases
   recall learnings without opening every file. One line per learning, hook included:

   ```markdown
   ---
   type: Learnings Index
   title: Learnings index — <project>
   description: One line + hook per feature; phases read this, then open a detail file only when its hook fits.
   timestamp: <YYYY-MM-DD>
   ---

   # Learnings index

   - [<feature title>](learnings/<slug>.md) — <one-line hook: the gotcha/pattern in ~10 words>
   - <slug> (<YYYY-MM-DD>) — nothing above the bar
   ```

   A feature with no substantial learnings gets the one-liner directly in the index and **no** detail file.

**Feed it back.** If a learning contradicts or extends a project file, update the source of truth, not
just the note: a confirmed new rule → `constitution.md`; a corrected stack fact → `repo-map.md`; a
resolved term → `.wi/glossary.md`. That is how the next feature starts smarter.

Commit: `docs(<slug>): learnings` (or fold into the docs-sync commit).

## 5 · PR description — write `.wi/features/<slug>/PR.md`

Write it from the feature's own artifacts — they were made for exactly this. The description is a **file,
not console output**: save it as `.wi/features/<slug>/PR.md` and commit it (`docs(<slug>): PR description`).
It is part of the dossier in both flows and exists **whether or not** a PR can be opened this run — it is
what `gh pr create --body-file` consumes, and what a human uses if they must create the PR by hand. It
opens with OKF frontmatter (`type: PR Description`); the PR **body** is everything *below* that
frontmatter, so the frontmatter is stripped before feeding `gh` (§7) — it's dossier metadata, not PR text.
Template:

```markdown
---
type: PR Description
title: <feature title>
description: <2-4 word summary of the change>
feature: <slug>
timestamp: <YYYY-MM-DD>
---

## <type>: <feature title>

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
findings with severity. Distilled from verification.md; the dossier tidy (§6) then prunes it.>

### Risk & rollout
<feature flag? migration order? back-out plan. From spec.md Rollout.>

### Decisions
<link any ADRs: .wi/adr/ADR-NNNN-*.md>
```

## 6 · Tidy the history & the feature dossier

- Ensure each commit is coherent (`<type>: <subject>`). Squash only if the project prefers a single commit
  per PR (check the constitution).
- Confirm no generated files, large blobs, or secrets slipped in.
- **Repo tree clean:** `git status` must show only the changes you mean to ship. Delete any verification
  scratch — one-off sanity scripts, probe files, generated artifacts (e.g. a `_sanity_export.py` written
  to run an export check). Throwaway probes belong in a temp dir outside the repo, or get removed before
  the PR. A stray scratch file in the diff is a defect.
- **Tidy the dossier** (do this BEFORE cutting the PR, so the PR carries a clean `.wi/`). Ship serves two
  flows: first read the **`Flow:`** line from the feature's `progress.md` (`dev` | `rpa`; a **missing line
  means `dev`** — features created before the line existed are dev). It keys which directory reference
  defines the sweep whitelist, the ephemera list, and the dossier manifest below: `dev` →
  `${CLAUDE_PLUGIN_ROOT}/skills/research/references/wi-directory.md`, `rpa` →
  `${CLAUDE_PLUGIN_ROOT}/skills/rpa/references/rpa-directory.md`. **RPA runs: see rpa/SKILL §7** for how
  ship's dev-named artifacts (spec.md, pitfalls.md, brief.md) map to the RPA ones. Then:
  1. *Sweep strays:* every feature-specific file must live under `.wi/features/<slug>/`. Anything this run left
     loose in `.wi/` or elsewhere (scratch notes, drafts, working files) moves into the slug folder or is
     deleted if worthless. Project-level files stay where they are — the whitelist is the flow's directory
     reference's project-level list (dev: wi-directory.md's "Project-level memory" bullet; rpa:
     rpa-directory.md's "Project-level files" bullet — the RPA registries `rpa-constitution.md`,
     `sdd-template.md`, `inputs.md`, `components.md`, `orchestrator.md` are project files, never strays).
     When in doubt the directory reference wins; never sweep a file it marks project-level.
  2. *Prune the ephemera* — the flow's directory reference names them (dev: wi-directory.md's ephemera
     bullet; rpa: rpa-directory.md's run-dossier bullet); prune exactly that list, nothing more. Their
     value must already be distilled — §5 folded the checker/diff-review verdicts into `PR.md`'s
     Verification; research notes live on in the ADR and `spec.md`. If something is still load-bearing,
     fold it in first. Prune tracked ephemera with `git rm -f` (the §2 result-mode checker refreshed
     `verification.md` *after* the commit that last touched it, so a plain `git rm` refuses on the local
     modifications); a never-committed one (`cross-review.md` is written at §2 and typically never
     committed) is untracked — plain-delete it, `git rm` has no pathspec to match (prune a review file
     left under its pre-1.3 legacy name too; `.logs/` is likewise never tracked (self-gitignored) —
     plain-delete the directory).
     (Skip pruning if the constitution says to keep them.)
  3. *Finalize `tokens.md` — NOW, not at close-out.* The file must be complete **inside the dossier
     commit**, or it never rides the PR. The ledger was scaffolded at research/build start and its
     subagent rows appended live; finalize with one command:
     `python ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/token_report.py --write .wi/features/<slug>/tokens.md`
     (auto-detects the active session transcript under `~/.claude/projects/`; add
     `--transcript <path>` if you know it). It replaces the `## Orchestrator` section in place,
     recomputes the **Subagents (exact)** sum from the ledger rows, fills the **duration totals**
     (Σ compute from the rows' Duration cells; the autonomous wall-clock from the sibling
     `progress.md`'s stamped phase spans — `--progress <path>` to override), and on Claude Code appends
     the **`## Subagent detail`** section: each dispatch's exact input/output/cache split, model,
     transcript-stamped duration, and estimated cost, read from the session's
     `subagents/agent-*.jsonl` sidecar transcripts — no manual stdout-copy anywhere. On a parse
     failure it writes `Orchestrator: unavailable for this run` (never a substitute, estimate, or
     fabricated figure); a missing stamp likewise yields `unavailable` timing, not a guess. The
     **file** is the deliverable, not the console output.
  4. *What remains is the fixed dossier for this flow* — take the manifest from the flow's directory
     reference, not from memory: `dev` → wi-directory.md's seven-file dossier (progress, brief, spec,
     tasks, pitfalls, tokens, PR); `rpa` → rpa-directory.md's run dossier (the SDD pack plus per-process
     `tobe.md`). Either way it is the durable record of the feature (`PR.md` was written in §5, so this
     tidy commit carries the complete dossier).
  5. Commit it: `chore(<slug>): tidy feature dossier`.

## 7 · Open the PR (autonomous)

The user chose hands-off-to-PR, so open it without asking. Push the branch
(`git push -u origin wi/<slug>`), strip PR.md's OKF frontmatter into a throwaway body file (outside the
repo, so the dossier stays clean), then open the PR from it:

```bash
body=$(mktemp)
awk '{sub(/\r$/,"")} NR==1&&$0=="---"{f=1;next} f&&$0=="---"{f=0;next} !f' .wi/features/<slug>/PR.md > "$body"
gh pr create --title "<…>" --body-file "$body"   # add --draft if the run ended blocked or partial
rm -f "$body"
```

(The `mktemp` + `awk` pipeline assumes a POSIX shell — Git Bash on Windows, which Claude Code provides; it
is not guaranteed under Copilot CLI. The leading `{sub(/\r$/,"")}` keeps the frontmatter strip CRLF-safe on
a `core.autocrlf=true` checkout, where the `---` delimiters arrive as `---\r` and a bare line compare would
miss them.)

Log the PR URL in `progress.md` as `- <ts> **Update** PR opened: <url>` — full OS-clock stamp; this
exact wording is the stamp `token_report.py` reads as the end of the second autonomous span. §8
verifies the PR's remote checks before any cleanup.

**A pushed branch is not a shipped feature.** If `gh` is unavailable or `pr create` fails, the run is **not
done**: record in `progress.md`'s Decisions/blockers the exact recovery command (frontmatter-stripped, as
above) —
`body=$(mktemp); awk '{sub(/\r$/,"")} NR==1&&$0=="---"{f=1;next} f&&$0=="---"{f=0;next} !f' .wi/features/<slug>/PR.md > "$body"; gh pr create --title "<…>" --body-file "$body"`
— plus the failure reason, and tell the user in the final report that the PR still needs creating. Never silently stop at the push. **Never
force-push.** If `superpowers:finishing-a-development-branch` is installed, consult it for the close-out
**decision** (merge / PR / keep) in interactive runs — in an autonomous run that decision is already made
(the PR). The worktree and branch **mechanics stay wi's own (§8)**: wi's sibling-dir worktrees fail that
skill's `.worktrees/`-only provenance rule, so never delegate the removal itself. (A delegation point —
see the precedence rule in `skills/research/references/integrations.md`.)

**No remote at all** (`git remote` prints nothing — a local-only repo): pushing and `gh pr create` are
*impossible*, not failed — don't loop on them. Record `Close-out: local (no remote)` in `progress.md`'s
Decisions/blockers together with the recovery pair to run once a remote exists — the
`git push -u origin wi/<slug>` and the frontmatter-stripped `gh pr create` command above — then proceed
to §8; its PR checkbox passes on that recorded substitute, and with no remote there are no remote checks:
log `remote checks: none configured` and the remote-checks box passes on it under the recorded local
close-out. Everything else in ship (gate, docs-sync, dossier, tokens) already ran for real, so the branch
is merge-ready the moment a remote appears.

## 8 · Remote checks, then close out — checklist, then the report

**The remote-checks gate — before any cleanup.** The §1 gate was local; the PR's checks — CI runs and
deployment checks (e.g. Vercel) — are the authoritative signal, and they run remotely *after* the push.
The PR must be green, not just the worktree. Give the checks a moment to register, then watch them to
completion: `gh pr checks <pr-url-or-number> --watch --fail-fast`, bounded by a sane timeout —
redirected to `.wi/features/<slug>/.logs/pr-checks.txt`; the final table (its tail) is the evidence
you log to `progress.md` (default ~15 minutes; the constitution may override). If no checks register
after ~2 minutes AND the repo has no
CI config (no `.github/workflows/`, nothing in `repo-map.md`), log `remote checks: none configured` in
`progress.md` and proceed to cleanup — the remote-checks box below passes on that recorded substitute.

- **Green** — every reported check (or every **required** check, where branch protection defines them)
  concluded successfully. Log the evidence in `progress.md`: `remote checks: N/N green` plus the check
  names, conclusions, and run URLs. It lives there by design: `verification.md` was pruned at §6 and
  `PR.md` was committed before the push, so neither can carry evidence that only exists after the PR
  opens — `progress.md` carries it, and the final report repeats it.
- **Red** — **the run is not done and the keep-alive condition is not satisfied.** Pull the failing logs
  to a file, not into context (`gh run view <run-id> --log-failed >
  .wi/features/<slug>/.logs/ci-<run-id>.txt 2>&1`; an external check via its details URL), read the
  failing lines by grep/tail, and diagnose. The worktree still exists — cleanup hasn't run — so fix
  there, commit, push, re-watch. **Max 2 remote-fix rounds**;
  a genuine flake (runner died, transient network, timeout with no log) may be re-run without consuming
  a round. Budget exhausted: interactive → present the concrete failures and let the user decide (keep
  fixing, or accept red → record `remote checks: red — accepted by user (<reason>)` in `progress.md`'s
  Decisions); `--auto` → hold the run open: log the failures, Phase stays `ship`, keep the worktree —
  the keep-alive loop re-enters ship and resumes at this gate. Never accept red autonomously. Accepted
  red leaves an armed keep-alive condition unsatisfiable — its predicate names green checks — so when
  the user accepts red, tell them to clear the `/goal` (or stop the Autopilot loop) themselves.
- **Timeout / a check that never reports** — not green. Log
  `remote checks: pending after <timeout> (<names>)` and hold like red minus the fix loop; the next
  re-entry re-checks cheaply.

**Cleanup runs only after the remote gate lands** (green / none configured / user-accepted red) —
worktree removal comes after remote verification by design: a fix loop needs its workspace.
After the PR is open (or merged, or the §7 no-remote close-out is recorded), clean up: remove the
worktree (safe once the branch is pushed — or, under a no-remote close-out, once the dossier commit is on
the local branch), and
delete the **local** branch only if it is fully merged (`git branch -d`, which refuses otherwise — see
the worktree reference); the remote branch and an open PR are never deleted. Then run the
**close-out checklist** — every box, against the actual repo state, not memory. `progress.md` Phase =
`done` is **earned by this checklist**; an unticked box means ship is not finished, no matter what the
console already said:

- [ ] PR is **open** and its URL is logged in `progress.md` (two substitutes, §7: branch pushed + failure
      reason + the frontmatter-stripped `gh pr create …` recovery command recorded as a blocker; or — no
      remote exists — `Close-out: local (no remote)` + the push/PR recovery pair recorded)
- [ ] Remote checks: N/N green logged with run URLs — or none configured logged, or red — accepted by
      user (<reason>) recorded in Decisions (--auto never accepts red)
- [ ] `.wi/features/<slug>/PR.md` exists and is committed on the branch
- [ ] `tokens.md` passes the structural gate — run
      `python ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/check_tokens.py .wi/features/<slug>/tokens.md`; a
      **non-zero exit blocks `Phase = done`** (file missing / no subagent row / unfilled sum / a row's
      Duration cell empty / duration totals unfilled / `## Orchestrator` still PENDING). An honest
      `unavailable` — for the orchestrator, a duration, or a total — always passes. This *replaces*
      reading the file by eye — the exit code is the close-out condition the keep-alive loop waits on.
- [ ] `.wi/learnings.md` index has this feature's line (and the detail file exists if one was warranted)
- [ ] dossier = exactly the flow's manifest (per progress.md `Flow:`, missing = dev — dev: the seven-file
      dossier in wi-directory.md; rpa: the run dossier in rpa-directory.md; **RPA runs: see rpa/SKILL §7
      mapping**); ephemera pruned (the flow's directory reference names them); no strays anywhere
      in `.wi/`
- [ ] worktree removed; local branch deleted only if fully merged (`git branch -d` refuses otherwise) —
      the remote branch / open PR never deleted

All green: set Phase = `done`, add a final stamped Log line (`- <ts> **Update** phase = done` + the PR
link), and if `roadmap.md` exists mark this feature done and surface the next one.

Then deliver the **final run report** in the console: the approach (cite ADR-NNNN), what was built, the
gate results with local and remote status reported **separately** —
`local gate: green · PR checks: N/N green · deployment: ready` — never one undifferentiated "green",
the PR URL, and the **token table read from the finalized `tokens.md`** — the file was completed back in
the dossier tidy; do not recompute it here. **Subagent rows are exact** (from completion
notifications) — that sum is the real, measurable cost of the delegated work; report it as the headline,
with the orchestrator figure (or `unavailable`) alongside, and the cost estimate + per-agent split when
the finalize produced them. The two numbers wi trusts: **subagent-exact**
(completion notifications) and **orchestrator-from-transcript** (`token_report.py`). Beside the token
table, print the **timing table**, read from the same finalized files (`unavailable` rows print as-is):

```
Timing (autonomous, manual waits excluded)
  research + plan (gate 1 → gate 2):  <span from progress.md stamps>
  build + ship (gate 2 → PR):         <span from progress.md stamps>
  autonomous total:                   <tokens.md wall-clock line>
  Σ subagent compute:                 <tokens.md Σ-compute line>
``` If a keep-alive loop
is armed (Claude/Codex `/goal` or Copilot Autopilot), its condition holds only when the checklist
**including the remote-checks box** passes — that is the state in which the loop clears. Exception:
user-accepted red — the condition names green checks and stays unsatisfiable; the loop ends only when
the user clears it (told at the gate above).

## Offer

If the change is the kind that recurs (a release, a periodic check), mention that wi's loop can be
re-run per feature — and that the user can keep `.wi/roadmap.md` as the running backlog.
