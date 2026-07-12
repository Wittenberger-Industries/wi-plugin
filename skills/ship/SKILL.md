---
type: Skill
name: ship
user-invocable: false
description: >
  Take a built feature through the verification gate and out as a clean, reviewed pull request. Use this
  skill when the user says "/wit:ship", "ship it", "open the PR", "wrap this up", "finish the branch", or as
  the final phase of the loop (autonomous).
---

# ship: verify, review, PR

Prove the change is safe to merge and package it; never rubber-stamp. If the gate is red the feature
isn't done; nothing here weakens to make it pass.

Inputs: the feature branch/worktree, `spec.md` (acceptance criteria), `pitfalls.md`, `constitution.md`,
`repo-map.md`. Hold exactly that (workflow.md's **context budget**; read artifacts by section): the diff
enters as `--stat` + hunks (ship:2), command output as exit code + tail (ship:1/ship:8), and the
checker (not you) re-reads the repo.

First act once engaged: append `- <ts> **Update** phase = ship (ship engine engaged (wit <version>))` to
progress.md's Log: full ISO-8601 stamp from the OS clock (`date -Iseconds` /
`python ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/now.py`), <version> read from
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`.

Design rationale for this skill lives in the wit repo's `docs/design-notes/ship.md` (maintainer doc,
never loaded at runtime).

## 1 · Verification gate (must be green)

Run the full gate from `${CLAUDE_PLUGIN_ROOT}/skills/ship/references/verification-gate.md`: the complete
test suite, lint, format check, typecheck, and any CI-equivalent command from `repo-map.md`. Every gate
command runs per workflow.md's **output house rule**: redirected to
`.wit/features/<slug>/.logs/gate-<step>.txt`, verdict from the exit code + `tail -n 30`, failures pulled
by grep. Every acceptance criterion in `spec.md` must map to something that actually passed. If
`superpowers:verification-before-completion` is in your available skills you MUST run it too (log it):
a delegation point; precedence: `skills/research/references/integrations.md`. Red → fix the code (loop
back to build), never lower the bar.

## 2 · Review against intent

Self-review the diff with fresh eyes, `git diff --stat`, then open only the hunks a criterion or
finding needs (the output house rule: never a whole-diff read), against:
- **Acceptance criteria** in `spec.md`: each one met and demonstrably so.
- **Pitfalls** in `pitfalls.md`: each applicable one actually handled (tested where it matters).
- **Constitution**: style, boundaries, no secrets, no stray scope.

**Review dispatch (wit-code-checker · result mode): always runs; one dispatch, two passes.** First
resolve the line-review source: if `superpowers:requesting-code-review` is in your available skills,
locate its reviewer template, the `code-reviewer.md` inside that skill's installed directory (Glob the
plugin roots, e.g. `~/.claude/plugins/**/requesting-code-review/**/code-reviewer.md`), and pass its
absolute path in the checker dispatch as `Line review template: <path>`; absent → `Line review
template: none`. Log `review via wit-code-checker + superpowers:requesting-code-review[inline]` or
`review via wit-code-checker (wit line review; superpowers absent)`.

Then dispatch **wit-code-checker** (`agents/wit-code-checker.md`) in `result` mode, asking for both
passes: the **feature-level result check**, every `spec.md` acceptance criterion + locked decision
(ADRs, constitution) confirmed delivered and **wired**, not just present (the checker reads the actual
repo), and the **line-level review** of the branch diff, from the template path above or the checker's
built-in review when `none`. Findings from both passes land in `verification.md` in the
BLOCKER/WARNING/INFO taxonomy. This dispatch is unconditional (on the `checker` tier from
`progress.md`'s resolved-routing block; models.md's resolve-once rule; else inherit); no
cross-provider configuration demotes or replaces it.

**Mixture of Agents layer (only when configured).** If the resolved-routing block's MoA row includes
`review` in its `points`, run the result-mode review as an MoA proposer/aggregator pass instead of the
single dispatch above: N proposer checkers return findings, an optional second layer refines, and one
aggregator checker alone writes `verification.md` and counts as one review round (the cross-provider layer
below and the max-2-rounds loop unchanged). Append `+ MoA (<N> proposers, <L> layers, aggregator <tier>)`
to the review log line above. Full contract (identical proposer prompts, markers, layer semantics, the
aggregator's dedupe/max-severity/verify-before-drop rule, `tokens.md` rows):
`${CLAUDE_PLUGIN_ROOT}/references/moa.md`. MoA row `none`, or `review` not in its `points` → the single
dispatch above runs unchanged.

**Cross-provider layer (only when configured).** If the resolved-routing block's cross-provider row
names a provider (≠ `none`) and its API key is present, **additionally** run the independent
cross-provider diff review (`${CLAUDE_PLUGIN_ROOT}/references/models.md`: the `cross_review.py`
mechanics, inputs, and exit codes): a second opinion layered on top of the checker dispatch, it never
writes `verification.md` and never replaces the checker. When it cannot run (unconfigured, or the script
signals a config/API error or a missing key), log `cross-provider layer skipped (<reason>)` and continue;
the checker dispatch above ran regardless.

Findings from all layers feed the same loop: a BLOCKER (an unmet criterion, a decision silently
reduced to a stub, a correctness bug in the diff) sends the feature **back to build**,
**max 2 review→fix rounds** shared across all of it; whatever remains goes with its severity into `PR.md`'s
Verification. A BLOCKER from any layer blocks the PR; ship never opens the PR on a feature
wit-code-checker says isn't delivered. `cross-review.md` is ephemeral (pruned in ship:6, after ship:5
distills it into `PR.md`). Address findings before proceeding; note anything deliberately deferred.

## 3 · Sync docs & architecture

Make the docs match reality before the PR: update what this change *actually* affected, never a
blanket re-document.
- **Architecture diagram:** a change that added or removed a module, dependency, layer, or external
  service updates `.wit/architecture.md` (mermaid graph + legend). Absent (a greenfield project's first
  feature) → create it from scan's template (scan's docs are committed where written,
  wit-directory.md's project-level rule, so absence really means greenfield). Then validate it:
  `python ${CLAUDE_PLUGIN_ROOT}/skills/scan/scripts/check_mermaid.py .wit/architecture.md`; fix every
  error it reports. (python fallback: workflow.md "Script invocation"; holds for every script in this
  SKILL.)
- **Project overview & commands:** organization/stack/run-step changes → `.wit/overview.md`; command
  changes → `.wit/repo-map.md`.
- **Repo docs the change staled:** READMEs, `docs/`, public-surface docstrings/examples now wrong;
  strictly this change's staleness, not the whole tree.
- **Glossary:** fold in any new domain term the build introduced.

Commit the doc updates with the feature (`docs(<slug>): …`) so the PR carries current docs.

## 4 · Compound: capture what's worth remembering

Harvest the **non-obvious** knowledge from this run: **now, before the PR**, so the learnings ride the
branch and reach the team through review. The bar is strict: only things that would have *saved real
time if known up front*:
- a constraint or dependency that wasn't in any doc and bit the run;
- an approach that looked right but failed, and why;
- a non-obvious, reusable pattern or gotcha (stack quirk, CI surprise, test-harness trap).

Do **not** record what's already obvious from the code, the constitution, or the PR ("we added X").

Two tiers, one index:
1. **Substantial learnings** get their own file `.wit/learnings/<slug>.md` (create the dir lazily):

   ```markdown
   ---
   type: Learning
   title: <feature title> (learnings)
   description: <one-line hook; the gotcha/pattern worth recalling next feature>
   feature: <slug>
   timestamp: <YYYY-MM-DD>
   tags: [<area>, ...]
   ---
   # <feature title> (learnings)
   ## What didn't work
   ## Non-obvious decisions
   ## Gotchas / patterns to reuse
   ```

2. **The index `.wit/learnings.md`** (create lazily) is updated **every feature**: it is how later
   phases recall learnings without opening every file. One line per learning, hook included:

   ```markdown
   ---
   type: Learnings Index
   title: Learnings index (<project>)
   description: One line + hook per feature; phases read this, then open a detail file only when its hook fits.
   timestamp: <YYYY-MM-DD>
   ---

   # Learnings index

   - [<feature title>](learnings/<slug>.md): <one-line hook, the gotcha/pattern in ~10 words>
   - <slug> (<YYYY-MM-DD>): nothing above the bar
   ```

   A feature with no substantial learnings gets the one-liner directly in the index and **no** detail
   file.

**Feed it back.** A learning that contradicts or extends a project file updates the source of truth,
not just the note: a confirmed new rule → `constitution.md`; a corrected stack fact → `repo-map.md`; a
resolved term → `.wit/glossary.md`.

Commit: `docs(<slug>): learnings` (or fold into the docs-sync commit).

## 5 · PR description: write `.wit/features/<slug>/PR.md`

Write it from the feature's own artifacts. It is a **committed file, never console output**
(`docs(<slug>): PR description`), part of the dossier in both flows, and it exists **whether or not** a
PR can be opened this run: it is what `gh pr create --body-file` consumes, and what a human uses to
create the PR by hand. Its OKF frontmatter (`type: PR Description`) is dossier metadata, not PR text:
the PR **body** is everything *below* the frontmatter, stripped before feeding `gh` (ship:7). Template:

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
findings with severity. Distilled from verification.md; the dossier tidy (ship:6) then prunes it.>

### Risk & rollout
<feature flag? migration order? back-out plan. From spec.md Rollout.>

### Decisions
<link any ADRs: .wit/adr/ADR-NNNN-*.md>
```

## 6 · Tidy the history & the feature dossier

- Each commit coherent (`<type>: <subject>`). Squash only if the project prefers a single commit per PR
  (check the constitution).
- No generated files, large blobs, or secrets slipped in.
- **Repo tree clean:** `git status` must show only the changes you mean to ship. Delete any
  verification scratch: one-off sanity scripts, probe files, generated artifacts. Throwaway probes
  belong in a temp dir outside the repo; a stray scratch file in the diff is a defect.
- **Tidy the dossier** (BEFORE cutting the PR, so the PR carries a clean `.wit/`). Read the **`Flow:`**
  line from the feature's `progress.md` (`dev` | `rpa`; a **missing line means `dev`**). It keys the
  directory reference that defines the sweep whitelist, the ephemera list, and the dossier manifest:
  `dev` → `${CLAUDE_PLUGIN_ROOT}/skills/research/references/wit-directory.md`, `rpa` →
  `${CLAUDE_PLUGIN_ROOT}/skills/rpa/references/rpa-directory.md`. **RPA runs: see rpa:7** for how
  ship's dev-named artifacts (spec.md, pitfalls.md, brief.md) map to the RPA ones. Then:
  1. *Sweep strays:* every feature-specific file lives under `.wit/features/<slug>/`: anything this run
     left loose in `.wit/` or elsewhere moves into the slug folder, or is deleted if worthless.
     Project-level files stay where they are: the whitelist is the flow reference's project-level list
     (dev: wit-directory.md's "Project-level memory" bullet; rpa: rpa-directory.md's "Project-level
     files" bullet. The RPA registries `rpa-constitution.md`, `sdd-template.md`, `inputs.md`,
     `components.md`, `orchestrator.md` are project files, never strays). When in doubt the directory
     reference wins; never sweep a file it marks project-level.
  2. *Prune the ephemera*: exactly the flow reference's list (dev: wit-directory.md's ephemera bullet;
     rpa: rpa-directory.md's run-dossier bullet), nothing more. Their value must already be distilled:
     ship:5 folded the review verdicts into `PR.md`'s Verification; research notes live on in the ADR
     and `spec.md`; anything still load-bearing is folded in first. Tracked ephemera: `git rm -f` (a
     plain `git rm` refuses: the ship:2 checker refreshed `verification.md` after its last commit).
     Never-committed ones are untracked: plain-delete them (`cross-review.md`; `.logs/` likewise,
     self-gitignored). Skip pruning if the constitution says to keep them.
  3. *Finalize `tokens.md`: NOW, inside the dossier commit*, or it never rides the PR:
     `python ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/token_report.py --write .wit/features/<slug>/tokens.md`
     (auto-detects the active session transcript; `--transcript <path>` / `--progress <path>` to
     override). That is the Claude Code finalizer; a **non-Claude host runs the one its platform tool
     map names** (Grok Build: `grok_token_report.py --write`, same flags;
     `${CLAUDE_PLUGIN_ROOT}/references/grok-tools.md`). It rewrites the `## Orchestrator` section in place, recomputes the **Subagents
     (exact)** sum from the ledger rows, fills the **duration totals** (Σ compute from the rows'
     Duration cells; wall-clock from `progress.md`'s stamped phase spans), and on Claude Code appends
     the per-dispatch **`## Subagent detail`** split, writing the honest `unavailable` wherever a
     parse fails (wit-directory.md's **ledger rule**: never a substitute, estimate, or fabricated
     figure). The **file** is the deliverable, not the console output.
  4. *What remains is the fixed dossier for this flow*: take the manifest from the flow's directory
     reference, not from memory: `dev` → wit-directory.md's seven-file dossier (progress, brief, spec,
     tasks, pitfalls, tokens, PR); `rpa` → rpa-directory.md's run dossier (the SDD pack plus
     per-process `tobe.md`).
  5. Commit it: `chore(<slug>): tidy feature dossier`.

## 7 · Open the PR (autonomous)

The user chose hands-off-to-PR, so open it without asking. Push the branch
(`git push -u origin wit/<slug>`), strip PR.md's OKF frontmatter into a throwaway body file (outside the
repo, so the dossier stays clean), then open the PR from it:

```bash
body=$(mktemp)
awk '{sub(/\r$/,"")} NR==1&&$0=="---"{f=1;next} f&&$0=="---"{f=0;next} !f' .wit/features/<slug>/PR.md > "$body"
gh pr create --title "<…>" --body-file "$body"   # add --draft if the run ended blocked or partial
rm -f "$body"
```

Log the PR URL in `progress.md` as `- <ts> **Update** PR opened: <url>` (full OS-clock stamp); this
exact wording is the stamp `token_report.py` reads as the end of the second autonomous span. ship:8
verifies the PR's remote checks before any cleanup.

**A pushed branch is not a shipped feature.** If `gh` is unavailable or `pr create` fails, the run is
**not done**: record in `progress.md`'s Decisions/blockers the exact recovery command
(frontmatter-stripped, as above):
`body=$(mktemp); awk '{sub(/\r$/,"")} NR==1&&$0=="---"{f=1;next} f&&$0=="---"{f=0;next} !f' .wit/features/<slug>/PR.md > "$body"; gh pr create --title "<…>" --body-file "$body"`,
plus the failure reason, and tell the user in the final report that the PR still needs creating.
Never silently stop at the push. **Never force-push.** If
`superpowers:finishing-a-development-branch` is installed, consult it only for the close-out
**decision** (merge / PR / keep) in interactive runs; an autonomous run already decided (the PR). The
worktree and branch **mechanics stay wit's own (ship:8)**: never delegate the removal itself. (A
delegation point; precedence: `skills/research/references/integrations.md`.)

**No remote at all** (`git remote` prints nothing: a local-only repo): pushing and `gh pr create` are
*impossible*, not failed; don't loop on them. Record `Close-out: local (no remote)` in
`progress.md`'s Decisions/blockers together with the recovery pair to run once a remote exists, the
`git push -u origin wit/<slug>` and the frontmatter-stripped `gh pr create` command above, then proceed
to ship:8: its PR checkbox passes on that recorded substitute, and with no remote there are no remote
checks: log `remote checks: none configured` and that box passes under the recorded local close-out.
Everything else in ship (gate, docs-sync, dossier, tokens) already ran for real, so the branch is
merge-ready the moment a remote appears.

## 8 · Remote checks, then close out: checklist, then the report

**The remote-checks gate: before any cleanup.** The ship:1 gate was local; the PR's checks, CI runs
and deployment checks (e.g. Vercel), are the authoritative signal, and they run remotely *after* the
push. The PR must be green, not just the worktree. Re-create the log dir first if the ship:6 tidy
pruned it: `mkdir -p .wit/features/<slug>/.logs && printf '*\n' > .wit/features/<slug>/.logs/.gitignore`
(idempotent; self-gitignored so a red-path fix commit can never stage CI logs: workflow.md's output
house rule). Give the checks a
moment to register, then watch them to completion: `gh pr checks <pr-url-or-number> --watch
--fail-fast`, bounded by a sane timeout (default ~15 minutes; the constitution may override),
redirected to `.wit/features/<slug>/.logs/pr-checks.txt`; the final table (its tail) is the evidence you
log to `progress.md`. If no checks register after ~2 minutes AND the repo has no CI config (no
`.github/workflows/`, nothing in `repo-map.md`), log `remote checks: none configured` in `progress.md`
and proceed to cleanup; the remote-checks box below passes on that recorded substitute.

- **Green**: every reported check (or every **required** check, where branch protection defines them)
  concluded successfully. Log the evidence in `progress.md`: `remote checks: N/N green` plus the check
  names, conclusions, and run URLs; `progress.md` is the one file that can carry post-push evidence
  (`verification.md` was pruned at ship:6, `PR.md` pre-dates the push); the final report repeats it.
- **Red**: **the run is not done and the keep-alive condition is not satisfied.** Pull the failing
  logs to a file, not into context (`gh run view <run-id> --log-failed >
  .wit/features/<slug>/.logs/ci-<run-id>.txt 2>&1`; an external check via its details URL), read the
  failing lines by grep/tail, and diagnose. The worktree still exists (cleanup hasn't run) so fix
  there, commit, push, re-watch. **Max 2 remote-fix rounds**; a genuine flake (runner died, transient
  network, timeout with no log) may be re-run without consuming a round. Budget exhausted:
  interactive → present the concrete failures and let the user decide (keep fixing, or accept red →
  record `remote checks: red - accepted by user (<reason>)` in `progress.md`'s Decisions); `--auto` →
  hold the run open: log the failures, Phase stays `ship`, keep the worktree; the keep-alive loop
  re-enters ship and resumes at this gate. Never accept red autonomously. Accepted red leaves the
  armed keep-alive condition unsatisfiable (its predicate names green checks): tell the user to clear
  the `/goal` (or stop the Autopilot loop) themselves.
- **Timeout / a check that never reports**: not green. Log
  `remote checks: pending after <timeout> (<names>)` and hold like red minus the fix loop; the next
  re-entry re-checks cheaply.

**Cleanup runs only after the remote gate lands** (green / none configured / user-accepted red: a fix
loop needs its workspace). Then: remove the worktree (safe once the branch is pushed; or, under a
no-remote close-out, once the dossier commit is on the local branch); delete the **local** branch only
if it is fully merged (`git branch -d`, which refuses otherwise; see the worktree reference); the
remote branch and an open PR are never deleted. Then run the **close-out checklist**: every box,
against the actual repo state, not memory. `progress.md` Phase = `done` is **earned by this
checklist**; an unticked box means ship is not finished, no matter what the console already said:

- [ ] PR is **open** and its URL is logged in `progress.md` (two substitutes, ship:7: branch pushed +
      failure reason + the frontmatter-stripped `gh pr create …` recovery command recorded as a
      blocker; or, no remote exists, `Close-out: local (no remote)` + the push/PR recovery pair
      recorded)
- [ ] Remote checks: `N/N green` logged with run URLs, or `none configured` logged, or
      `red - accepted by user (<reason>)` recorded in Decisions (`--auto` never accepts red)
- [ ] `.wit/features/<slug>/PR.md` exists and is committed on the branch
- [ ] `tokens.md` passes the structural gate: run
      `python ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/check_tokens.py .wit/features/<slug>/tokens.md`;
      a **non-zero exit blocks `Phase = done`**; an honest `unavailable` (for the orchestrator, a
      duration, or a total) always passes. The exit code *replaces* reading the file by eye: it is
      the close-out condition the keep-alive loop waits on.
- [ ] `.wit/learnings.md` index has this feature's line (and the detail file exists if one was
      warranted)
- [ ] dossier = exactly the flow's manifest (per progress.md `Flow:`, missing = dev; dev: the
      seven-file dossier in wit-directory.md; rpa: the run dossier in rpa-directory.md; **RPA runs: see
      the rpa:7 mapping**); ephemera pruned (the flow's directory reference names them); no strays
      anywhere in `.wit/`
- [ ] worktree removed; local branch deleted only if fully merged (`git branch -d` refuses otherwise);
      the remote branch / open PR never deleted

All green: set Phase = `done`, add a final stamped Log line (`- <ts> **Update** phase = done` + the PR
link), and if `roadmap.md` exists mark this feature done and surface the next one.

Then deliver the **final run report** in the console: the approach (cite ADR-NNNN), what was built, the
gate results with local and remote status reported **separately**
(`local gate: green · PR checks: N/N green · deployment: ready`, never one undifferentiated "green"),
the PR URL, and the **token table read from the finalized `tokens.md`** (completed in the dossier tidy;
never recomputed here). **Subagent rows are exact** (from completion notifications): report that sum
as the headline, with the orchestrator figure (or `unavailable`) alongside, and the cost estimate +
per-agent split when the finalize produced them. The two numbers wit trusts: **subagent-exact**
(completion notifications) and **orchestrator-from-transcript** (`token_report.py`). Beside the token
table, print the **timing table**, read from the same finalized files (`unavailable` rows print
as-is):

```
Timing (autonomous, manual waits excluded)
  research + plan (gate 1 → gate 2):  <span from progress.md stamps>
  build + ship (gate 2 → PR):         <span from progress.md stamps>
  autonomous total:                   <tokens.md wall-clock line>
  Σ subagent compute:                 <tokens.md Σ-compute line>
```

If a keep-alive loop is armed (Claude/Codex `/goal` or Copilot Autopilot), its condition holds only
when the checklist **including the remote-checks box** passes: that is the state in which the loop
clears. Exception: user-accepted red. The condition names green checks and stays unsatisfiable; the
loop ends only when the user clears it (told at the gate above).

## Offer

If the change is the kind that recurs (a release, a periodic check), mention that wit's loop can be
re-run per feature, and that the user can keep `.wit/roadmap.md` as the running backlog.
