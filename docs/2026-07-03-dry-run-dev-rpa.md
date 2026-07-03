---
type: Report
title: Dry run — /wi:dev and /wi:rpa exercised in subagents
description: Testing procedure and results of a sandboxed dry run of the two entry flows on branch review-fixes-2026-07-p2 (4e79cd0) — fixtures, boundaries, per-phase verdicts, and spec findings.
timestamp: 2026-07-03
tags: [testing, dry-run, dev, rpa]
---

# Dry run — /wi:dev and /wi:rpa (2026-07-03)

**System under test:** branch `review-fixes-2026-07-p2` @ `4e79cd0`, read straight from the working
tree (`${CLAUDE_PLUGIN_ROOT}` ≡ repo root) — i.e. the post-review-fix skill text, not the installed
plugin cache. **Verdict up front: both flows work as intended within their written contracts.**
`/wi:dev --auto` ran the full loop end-to-end (scan → brainstorm → research → plan → auto-gate →
TDD build with real parallel task-runners → ship with a green verification gate), stopping only at
the imposed no-push boundary; `/wi:rpa --auto` ran cleanly through ingest → TO-BE → SDD → checker →
auto-gate → worktree handoff to the build-delegation edge. Zero hard failures, zero boundary
violations. The runs surfaced **24 spec findings** (12 per flow, §4) — text-level ambiguities and
contract collisions, none of which broke either run. **All 24 were fixed the same day and re-verified
against the edited text (§6), plus 11 second-order findings the re-verification itself surfaced.**

## 1 · Procedure

### 1.1 Shape of the test

Each entry flow ran inside its **own dedicated subagent** (one `general-purpose` agent per flow,
dispatched in parallel), against a **disposable sandbox project** outside the plugin repo. The
plugin repo itself was declared read-only to both agents. Two harness substitutions were designed
in; only the first turned out to be needed:

- **Skill loading** (by design, held) — the agent reads each wi `SKILL.md` / reference file
  directly from the working tree at the moment the flow reaches it, substituting
  `${CLAUDE_PLUGIN_ROOT}` with the repo root. This is what makes the run test *this branch* rather
  than the marketplace cache. External delegations (superpowers skills, the reviewer template)
  resolved through the installed plugins, as they would in production.
- **Named-agent dispatch** (anticipated fallback, **never fired**) — the design assumed a subagent
  would have no `Agent` tool and would have to perform `wi-researcher` / `wi-task-runner` /
  `wi-code-checker` roles inline from their `agents/` definitions. In practice the Agent tool *and*
  the registered wi agent types were available one level down, so **every named-agent dispatch in
  both runs was real**, with MoA tiers applied (checker on opus, researcher/task-runners on
  sonnet). Nested dispatch from inside a subagent is a confirmed-working configuration.

Both flows ran with `--auto`. Since no user exists inside a subagent, the one remaining interactive
moment (brainstorm) was self-run: every would-be question resolved with the smallest reasonable
choice and logged as an assumption — which doubles as a robustness test of the flows' written
`--auto` semantics.

### 1.2 Dry-run boundaries (imposed deviations)

| # | Boundary | Reason |
|---|----------|--------|
| B1 | No `git push`, no `gh pr create` / `gh` writes; ship writes `PR.md` and records the command it *would* run | sandboxes have no remote; nothing may publish |
| B2 | No `uip cloud login`, no `uip` command touching a tenant; `Publish: none` | dry run must not reach any Orchestrator |
| B3 | No installs/uninstalls (markitdown, `uip`, .NET 8, python, gh were all verified present beforehand) | bootstrap steps become detect-and-record |
| B4 | No keep-alive arming — the `/goal` handoff line is recorded verbatim, not armed | no cron/goal loops from a QA run |
| B5 | Worktrees must stay under the sandbox root | containment |
| B6 | `/wi:rpa` stops at the build-delegation edge (step 6 after worktree + dossier move + `tokens.md --init`); records the delegation prompts it *would* send; step 7 verdicted as would-run list | the back half is UiPath's plugin doing hours of XAML work — out of scope for a dry run of *wi's* machinery |
| B7 | Feature/process kept minimal (≤3 tasks target for dev; single process for rpa) | test the machine, not the payload |

Everything else — `.wi/` seeding, ordinals, MoA first-run setup, brief/spec/tasks/SDD artifacts,
mermaid validation via `check_mermaid.py`, checker plan/result modes, the auto-approved gate,
worktree + TDD build, verification gate, learnings, `tokens.md` — was executed for real.

### 1.3 Fixtures

**dev sandbox** — `…\tmp\dryrun-dev\notes-cli\`: stdlib-only Python CLI (argparse, JSON store),
3 green `unittest` tests, git repo on `main` (2 commits), no remote, no linter configured (that gap
is deliberate — it exercises dev step 4's preflight rule about `UNKNOWN` gate commands).
Feature idea given to the flow:

> `/wi:dev "add a `search <term>` command that lists notes containing the term (case-insensitive)" --auto`

**rpa sandbox** — `…\tmp\dryrun-rpa\invoice-intake\`: `PDD.md` (single process, *Vendor Invoice
Intake*: CSV row validation → payables ledger append, exceptions report with reason codes BE-1..4,
archival, run summary; file-system only, no credentialed systems), `data/invoices_sample.csv`
(5 rows: 2 valid + missing-vendor + negative-amount + duplicate-id), git repo on `main`, no remote.
Invocation:

> `/wi:rpa "PDD.md" --auto`

The PDD was written to be *slightly* incomplete on purpose (no queue names, no agent names, no
framework named) so brainstorm/orchestrator elicitation has real gaps to fill and log.

### 1.4 What each agent had to return

A fixed report schema: per-step verdict table (`PASS / PASS-WITH-DEVIATION / FAIL / SKIPPED` + one-line
evidence), full `.wi/` + dossier file tree, the rendered gate transcript, verbatim errors,
numbered deviations & assumptions, **spec findings** (ambiguous/contradictory/uninstructable skill
text, with file + line), and the stop point. The orchestrating session then independently
spot-checked the artifacts on disk before writing the results below.

## 2 · Results — /wi:dev

**Outcome: the full loop works end-to-end.** Every phase executed for real; the only unexecuted
actions are `git push` + `gh pr create` (boundary B1), recorded verbatim in progress.md as recovery
commands. Run time ~38 min; ~217k tokens in the orchestrating agent + 236,566 exact nested-subagent
tokens per the finalized ledger.

| step | Verdict | Evidence |
|---|---|---|
| dev 1 · scan + MoA setup | PASS | `repo-map.md` + 3 docs committed; `moa.md` simple preset written on `--auto` and logged |
| dev 2 · feature folder + ordinal | PASS | `.wi/features/0001-search-command/` seeded, ordinal `0001`, `Gate mode: auto-approve` recorded |
| dev 3 · brainstorm | PASS-WITH-DEVIATION | `brief.md` + `glossary.md`; dialogue self-resolved in one pass (headless), assumptions logged |
| dev 4 · handoff + keep-alive | PASS-WITH-DEVIATION | preflight green; `/goal` line recorded verbatim, not armed (B4); auto → Phase=research same turn |
| dev 5 · design (research→plan→gate) | PASS | researcher dispatched for real (sonnet, 50,228 tok); `spec.md` (5 ACs) + `tasks.md` (2 tasks/1 wave) + `pitfalls.md`; checker plan-mode **CHECK PASSED** (opus, 36,007 tok, 0 findings); gate rendered + auto-approved |
| dev 6 · implement (build→ship) | PASS-WITH-DEVIATION | worktree + 2 **parallel** task-runners (both Self-Check PASS); wave-end gate 7/7 tests; ship gate green; PR step at boundary B1 |

Ship's verification gate, as run: named AC tests 4/4 → full suite 7/7 (exit 0, re-run after
docs-sync and at close-out) → e2e CLI smoke → checker result-mode **CHECK PASSED** (0 BLOCKER / 0
WARNING / 1 INFO, fixed) → reviewer "Ready to merge: Yes" (6 Minor: 2 fixed, 4 waived with reasons
in PR.md) → `check_tokens.py` OK exit 0. Lint/typecheck/CI honestly recorded n/a (none configured).

**Independent spot-check (orchestrator):** feature branch checked out into a throwaway worktree —
full suite **7/7 OK exit 0** reproduced; CLI smoke reproduced AC1/AC3 by hand (`search MILK`
matches `Buy Milk` case-insensitively; `search zzz` silent with rc 0); dossier is **exactly the
seven-file manifest** (brief, spec, tasks, pitfalls, progress, tokens, PR) after the tidy pruned
research notes + verification.md; `check_tokens.py` exits 0 on the finalized ledger; the run's own
worktree was removed at close-out and the branch kept unmerged, both as ship §8 specifies; 12-commit
history matches the agent's report exactly (3 `.wi` commits on main, 7 on the branch).

**Notable observations**

- **The MoA config drove real model routing**: checker ran twice on opus (plan + result mode),
  researcher and both task-runners on sonnet — exactly the simple preset's table.
- **The superpowers integrations were genuinely exercised** — brainstorming, writing-plans,
  using-git-worktrees, verification-before-completion, requesting-code-review,
  finishing-a-development-branch all invoked where wi's text mandates delegation. This is also
  where most of the friction lives: the delegate skills carry their own contracts (spec files,
  user gates, menu choices, worktree-provenance rules) that wi supersedes without saying so —
  findings V2, V6, V7, V8.
- **All four runtime errors were benign or by-design**: two self-inflicted tool fumbles by the
  agent, `git branch -d` refusing the unmerged branch (designed §8 behavior), and one real edge —
  pruning a checker-refreshed `verification.md` needs `git rm -f` (finding V9).
- **Honest bookkeeping held under `--auto`**: Phase=done was granted under an explicitly-logged
  substitute for the "PR open" checklist box (impossible with no remote), rather than silently or
  not at all — though the skill text itself has no such clause (finding V5).

## 3 · Results — /wi:rpa

**Outcome: works as intended through the front half and the build-handoff edge.** Steps 1–5 executed
fully, step 6 up to the dry-run boundary, zero errors, plugin repo untouched, no tenant contact at
any point. Run time ~28 min, ~196k agent tokens (+57.9k for the real checker dispatch).

| rpa step | Verdict | Evidence |
|---|---|---|
| 1 Bootstrap | PASS | detect-only: markitdown 0.1.5, .NET 8 (8.0.27), `uip` 1.196.4, UiPath skills present; structure discovery correctly n/a (not a UiPath repo) |
| 2 Ingest | PASS | `inputs.md` / `components.md` / `moa.md` (simple preset, logged) / first-run `rpa-constitution.md` committed; markitdown conversion skipped per ingest.md §1 (source already `.md`); run-slug `0001-vendor-invoice-intake` |
| 3 Brainstorm | PASS-WITH-DEVIATION | self-run (headless); `Framework: reframework` proposed per the heuristic + stamped; `orchestrator.md` convention-proposed, all names `?`-flagged; A1–A25 + open deps D1–D2 logged |
| 4 Plan | PASS | `sdd.md` (base ToC per precedence; §10 = 10 ACs), `architecture.md`, per-process `tobe.md`, `assumptions.md`, `process-inventory.md`, `tasks.md` (7 tasks / 4 waves); `check_mermaid.py` → `mermaid OK` (run for real, twice) |
| 5 Design gate | PASS | checker dispatched **as a real subagent** (plan mode, opus per MoA): 0 BLOCKER / 1 WARNING / 3 INFO → no plan loop; full gate summary rendered into progress.md, auto-approved on defaults (reframework / XAML-only / Publish: none); ADR-0001 written; learnings harvested + indexed |
| 6 Build | PASS-WITH-DEVIATION | worktree + branch `wi/0001-vendor-invoice-intake`, dossier as first branch commit, `tokens.md` scaffolded via `check_tokens.py --init` + exact checker row (57,896); **stopped before wave 1** (boundary B6) with all 6 delegation prompts recorded |
| 7 Verify & ship | SKIPPED | boundary B6; the full REFramework gate command list was recorded instead |

**Independent spot-check (orchestrator):** worktree + 8-commit history exactly as reported
(`ingest → orchestrator → ADR → learnings → dossier → ledger ×2` on top of the fixture commit), both
trees clean; `verification.md` is a real coverage matrix (all 10 ACs → covering tasks, `Wired?`
column, the WARNING honestly scoped); `progress.md` carries every phase transition, the embedded
gate summary, and the dry-run boundary log line. One extra check the agent didn't make:
`check_tokens.py` against the mid-run ledger **fails with exit 1** ("Subagents (exact) sum not
filled") — correct behavior, the sum is finalized at ship, which this run deliberately never
reached; the guardrail demonstrably bites.

**Notable observations**

- **Nested agent dispatch works.** The test harness assumed a subagent would have to perform the
  checker role inline; in fact the Agent tool + `wi:wi-code-checker` type were available one level
  down, and the checker ran as a genuine MoA-tiered (opus) dispatch — the plugin's agent wiring is
  exercised for real even when the whole flow itself runs inside a subagent.
- **The recorded build delegations are high-fidelity.** Six prompts (T1–T5, T7; T6 wire-up deferred
  on open dep D1), each pinning the worktree/branch, the git-ownership rule (subagent never
  commits), the XAML-only paradigm with the no-`.cs`/no-Invoke-Code hard rule, the constitution's
  house rules restated, and a per-task `uip` validation verify step.
- **`--auto` degrades sanely with no user at all**: every elicitation (orchestrator names, framework,
  paradigm, publish) resolved to a logged assumption or constitution default; open deps D1/D2 were
  deferred *visibly* (gate summary + progress.md) rather than silently dropped.

## 4 · Spec findings (merged)

What the dry runs surfaced in the skill text itself — the actionable output. R* = found by the rpa
run, V* = found by the dev run.

### From /wi:rpa

- **R1 · `--auto` scope contradiction** — `skills/rpa/SKILL.md` (~24) says "`--auto` collapses
  everything *after* brainstorm" (brainstorm stays interactive) while
  `brainstorm-protocol.md` (~17–19, 27–28) defines self-answering the must-asks as *the `--auto`
  behaviour*. The two disagree on whether a `--auto` run converses at all.
- **R2 · No brainstorm-mode stamp for `--auto`** — `brainstorm-protocol.md` (~22–25) offers only
  `via superpowers:brainstorming` | `via wi fallback`; a headless `--auto` run with superpowers
  *installed* fits neither. The stamp conflates "engine absent" with "auto mode".
- **R3 · Empty component registry unspecified** — `ingest.md` §3 never says what to write when zero
  components are found (fresh repo); no "none" convention in the template table.
- **R4 · Nobody owns creating the first-run constitution** — `skills/rpa/SKILL.md` step 2 (~44)
  lists "a first-run `rpa-constitution.md`" among the committed outputs, but no reference
  (uipath-bootstrap / ingest / brainstorm-protocol) instructs its creation; only the template's own
  header implies it. A literal reader never creates it.
- **R5 · ADR requirement is implicit** — the gate render mirrors research's `**Approach
  (ADR-NNNN):**` line and `rpa-directory.md` (~75) says framework ADRs go in `.wi/adr/`, but the rpa
  Procedure never instructs writing one; a SKILL.md-only reader reaches the gate ADR-less.
- **R6 · Framework confirmation under `--auto` unstated** — step 5's `--auto` clause (~92) names
  paradigm + publish defaults but not the framework confirmation; "as proposed at brainstorm" must
  be inferred.
- **R7 · Design-phase subagent tokens fall through the ledger** — rpa scaffolds `tokens.md` only on
  the first *build* delegation, but the pre-gate checker (step 5) is a subagent whose exact count
  exists only at completion; by the time the ledger exists the figure is normally lost. (dev
  scaffolds at research start — rpa has no design-phase scaffold point.)
- **R8 · Verification-gate commands are generic** — `verification-gate.md` (~38–43) pins no literal
  `uip` subcommands while demanding non-interactive, time-bounded runs; deliberate
  borrow-don't-reinvent, but the gate is not executable as written.
- **R9 · `adr/index.md` frontmatter inconsistency** — `adr-template.md`'s index template has no OKF
  frontmatter; `wi-directory.md` (~99) calls it a *typed* index.
- **R10 · e2e-test-needs-queue hole** (= the checker's own W1) — a queue-based design under a
  disconnected tenant leaves the natural AC verifier (local e2e run) without its queue;
  brainstorm-protocol §5 / build-uipath §3 / the gate's degrade clause each handle tenant absence,
  but no reference addresses this gap. The plan-mode checker caught it, which is the system working
  — but the method has no written answer for it.
- **R11 · Minor** — `rpa-build` exists only as a MoA key + a SKILL.md parenthetical; there is no
  `agents/rpa-build.md`, and a reader may search for it.
- **R12 · Minor** — `ingest.md` §1 "copy as-is (don't re-process)" immediately followed by "prepend
  OKF frontmatter" reads as contradictory for already-`.md` PDDs.

### From /wi:dev

- **V1 · Linter-less repos vs the preflight** — `skills/dev/SKILL.md` (~70–74) +
  `references/keep-alive.md` (17–26): the `/goal` condition embeds `<lint + test commands>` and the
  preflight requires both to exist and not be `UNKNOWN — ask`. A legitimately linter-less repo
  records "n/a — not configured"; neither file says whether n/a passes the preflight or how the
  template renders without a lint command.
- **V2 · superpowers:brainstorming contract collision** — `skills/brainstorm/SKILL.md` (23–32) says
  delegation means "capture the outcome into brief.md", but the delegate's own checklist mandates a
  `docs/superpowers/specs/` design doc, a user spec-review gate, and "the ONLY skill you invoke
  after brainstorming is writing-plans". wi never says which parts of the delegate's contract are
  suppressed; followed literally, both a superpowers spec file and wi's brief.md get written and
  writing-plans fires out of phase.
- **V3 · TDD task-shape ambiguity** — `skills/plan/SKILL.md` (~44–45: "the first task for a piece
  of behavior writes the failing test") vs (~77: "each task … ends green") vs
  `agents/wi-task-runner.md` (39–48: red+green inside one task): a separate red task cannot end
  green, and in parallel waves it races any sibling whose Verify runs the full suite. This run
  dodged it only via build §2's authored-not-run refinement; plan's own text gives no guidance for
  writing Verify lines under parallelism.
- **V4 · Researcher can't write its own notes** — `agents/wi-researcher.md`: the `tools:` allowlist
  (line ~6) has no Write/Edit, yet the Output contract (~127–132) requires writing a notes file and
  confirming it parses — only achievable via Bash heredoc, fragile on Windows shells; the dispatch
  prompt had to teach the workaround.
- **V5 · No-remote repos can never close out** — `skills/ship/SKILL.md` §7 (~233–256) + §8
  (~267–268) assume a remote exists; the sole checklist substitute for "PR open" is "branch pushed
  + …". A repo with no `origin` can never satisfy either clause, so a strictly-read close-out never
  reaches Phase=done. (The sandboxed/detached variant in `worktrees-and-subagents.md` 60–64 covers
  a different case.)
- **V6 · Worktree-removal contract collision** — `skills/ship/SKILL.md` §8 (~260, "remove the
  worktree — safe once the branch is pushed") vs `superpowers:finishing-a-development-branch`
  (Option 3: never clean up the worktree; provenance rule: only remove worktrees under
  `.worktrees/`): wi's sibling-dir worktree fails the delegate's provenance check, so the skill §7
  tells ship to delegate to refuses the removal §8 requires.
- **V7 · Dispatch guidance contradicts itself** — `build/references/worktrees-and-subagents.md`
  (~76–79, "pass the task-runner prompt inline to a generic worker — don't depend on a
  pre-registered named agent") vs `skills/build/SKILL.md` (~51, "one fresh `wi-task-runner` (see
  agents/wi-task-runner.md) per task") and the plugin actually registering named agents. The caveat
  is Codex-motivated but stated platform-generally.
- **V8 · Gate re-print assumes a present user** — `skills/research/SKILL.md` §4 (~127–129) says to
  print the keep-alive again because "the user is present — they just approved"; false premise
  under `--auto`, and the skill doesn't say whether auto mode prints/arms here.
- **V9 · Dossier prune needs `git rm -f`** — `skills/ship/SKILL.md` §6: pruning `verification.md`
  collides with git state when the result-mode checker refreshed a file already committed with
  plan-mode content; `git rm` fails without `-f` and the skill text never mentions it (hit live in
  this run).
- **V10 · Minor** — `skills/scan/SKILL.md` (~250) "Rules: ~10-25 nodes" for the architecture
  diagram is unattainable on a micro-project (real diagram: 5 nodes) and conflicts with the same
  skill's keep-files-tight framing.
- **V11 · Minor** — `references/moa.md` (~42–44): "checker never below orchestrator's tier" is
  enforced against the *configured* orchestrator tier, not the actual session model — a
  higher-tier session with the simple preset dispatches the checker below the session tier with no
  warning (the warn-once rule only covers the session being *below* config).
- **V12 · Edge case** — ship §4 commits the learnings index line on the feature branch, so until
  merge, main's `.wi/learnings.md` silently lacks the in-flight feature's line while the rest of
  main's `.wi/` looks current; a `scan --refresh` on main mid-PR reads a stale index. Worth a
  sentence in `wi-directory.md`.

### Where the weight is

Three themes cover most of the 24: **(a) `--auto`/headless semantics are under-specified** at the
edges — R1, R2, R6, V1, V5, V8 are all "the text assumes a user or a remote exists"; **(b)
delegate-contract collisions** — wi mandates delegating to superpowers skills but never says which
parts of the delegate's own contract it supersedes (V2, V6, V7); **(c) bookkeeping gaps** — design-
phase tokens (R7), the unowned first-run rpa-constitution (R4), the implicit ADR (R5), the stale
learnings index on main (V12). R10 (e2e-needs-queue) is the one genuine *method* hole; the plugin's
own plan-mode checker caught it live, which is the mechanism working as designed.

## 5 · Reproducing this dry run

1. Create the two fixtures as in §1.3 (any tiny green-test project + any small single-process PDD).
2. Dispatch one subagent per flow with: the repo path as read-only SUT, `${CLAUDE_PLUGIN_ROOT}`
   substitution, the boundary table §1.2, and the report schema §1.4.
3. Spot-check artifacts on disk against each skill's contract before trusting the agent's verdicts.

Evidence from this run (ephemeral — lives under the background job's tmp dir and is cleaned with
it): `dryrun-dev/notes-cli` (branch `wi/0001-search-command` @ `2d0cca2`, kept unmerged) and
`dryrun-rpa/invoice-intake` + its `…-wi-0001-vendor-invoice-intake` worktree (branch tip
`206516e`).

## 6 · Fix sweep + re-verification (same day)

All 24 findings were fixed in one sweep. Three needed a decision first, locked as: **V5** — a repo
with no `origin` closes out locally (`Close-out: local (no remote)` marker + recorded push/PR
recovery pair; Phase=done reachable, and the keep-alive is *never armed* on such a repo); **R10** —
the no-tenant dev-verification strategy is decided at brainstorm and gate-approved (defer
queue-dependent checks with the dep, or a named local substitute); **V11** — moa.md now states the
pricing policy: dispatches run at the **configured** tier, never auto-escalated to the session
model; `simple` (opus/sonnet, the `--auto` default) is capped at opus by design; tiers above opus
enter a run only via the interactively-chosen `smart` preset or hand-written overrides.

The headline semantic fix (R1/R2 + mirrors): **`--auto` never collapses brainstorm — the user who
typed the command is present for it; self-answering with logged assumptions is a separate
*headless* fallback** (unattended dispatch: CI, a subagent, a scheduled run), stamped
`, self-answered (headless)` alongside the engine. That is exactly the behavior the README already
advertised — the sweep aligned the reference text to it.

**Re-verification** — two fresh agents ran against the edited (then-uncommitted) tree:

- *dev slice* (steps 1–4 executed in a pristine linter-less sandbox + consistency read of the
  rest): **all 12 V-findings FIXED**. The preflight passed by the letter with lint recorded
  `n/a — not configured` and rendered a clean test-only `/goal` condition; the fable session over
  the simple preset correctly produced no warning and no escalation.
- *rpa front half* (steps 1–5 executed, real MoA-tiered checker): **all 10 in-slice R-findings
  FIXED** (R8/R9 verified by read, not runtime — the gate itself wasn't run). The run exercised the
  new machinery live: ingest created the first-run constitution and the exact empty-registry state;
  the ledger was scaffolded pre-checker and carries the round-1 exact row (54,251); the checker's
  WARNING→revise→re-check loop converged (0 BLOCKER both rounds → CHECK PASSED).

The re-verification surfaced **11 second-order findings** (6 dev, 5 rpa) — interactions the first
edits introduced or exposed — all fixed in the same sweep. The sharpest: an armed `/goal` PR-open
condition could spin forever on a no-remote repo (dev's preflight now refuses to arm without a
remote); dev's "not self-answered" preflight clause contradicted the new headless rule (carve-out
added); a checker **re-check round can return without a completion notification** (a resumed agent)
— the ledger now records `unavailable` for that row, never an estimate; the WARNING-only re-check
loop is now explicitly the orchestrator's call (BLOCKER loops stay mandatory); and the last
surviving `--auto`↔headless conflation (rpa-constitution-template's email rule) plus two stale
templates (scan's repo-map lint cell now teaches the verbatim `n/a — not configured` token;
rpa-directory's stamp example carries the interactivity suffix) were aligned.

Re-run evidence (ephemeral): `dryrun-dev2/notes-cli` (stopped at Phase=research per the slice
boundary) and `dryrun-rpa2/invoice-intake` (stopped at Phase=design-gate, gate auto-approved,
`## CHECK PASSED`).
