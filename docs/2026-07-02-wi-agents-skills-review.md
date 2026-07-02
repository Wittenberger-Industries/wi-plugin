---
type: Review
title: Review — the 3 wi agents & 8 skills (issues / improvements)
description: Full-source review of agents/ and skills/ — findings ranked high/medium/low with evidence and concrete fixes. Updated after the PR #16 rescan (MoA role redesign; new H6 + M9) and the decided goal→feature rename (M1).
timestamp: 2026-07-02
tags: [review, agents, skills, quality]
---

# Review — the 3 wi agents & 8 skills

Scope: everything under `agents/` (wi-code-checker, wi-researcher, wi-task-runner) and `skills/`
(scan, dev, brainstorm, research, plan, build, ship, rpa + all 20 reference files), cross-checked
against the manifests, `scripts/validate.py`, the bundled ship/scan scripts, the git history since the
1.0.0 release, and the *installed* plugin caches (wi 1.0.0 and the UiPath marketplace) on this machine.
`python scripts/validate.py` passed on the tree this review was first written against; after #16 it
**fails on main** (see M9) — and everything below is beyond what it checks anyway.
Re-verified against PR #16 (`8d31c35`, MoA role redesign, merged 2026-07-02) — line references below
are current for that tree.

**Overall:** the architecture is genuinely strong — state-on-disk with typed OKF files, completion
markers everywhere a loop must parse an outcome, bounded loops (max 2 rounds) at every review point,
the worktree git-landmine rules (`refs/stash` really is shared), provenance tagging + the Runtime State
Inventory, the slopsquat guard, and a token ledger with real scripts and unit tests. The issues found
are mostly *drift*: places where one file moved on and its counterparts didn't, plus a few
cross-platform assumptions that demonstrably fail on Windows.

> **Update — PR #16 rescan.** The MoA role redesign (`8d31c35`) landed after the first pass. It
> **resolves** M3's role-key clause (MoA roles are now keyed by the real agent names) and its rename
> sweep is otherwise clean — 28/28 unit tests pass (run with `python`, reinforcing H3); the one
> cosmetic straggler is `moa_review.py:186`, which still says "reviewer API call failed". It
> **introduces** one new finding, **H6**: ship §2 and moa.md now disagree on whether the cross-provider
> check replaces the result-mode checker dispatch. Shifted line references (H2, H3, M4, L7) are
> refreshed. #16 also broke the repo's own validator on main — promoted to a finding, **M9**.
> Separately, M1 is upgraded from finding to **decision**: the `goal` work unit is renamed
> to **feature** — scope and migration recorded there.

---

## High — will break or silently corrupt a run

### H1 · The goal dossier is never committed before the worktree is created

- `skills/build/references/worktrees-and-subagents.md:33` asserts: *"If `.wi/` should be visible inside
  the worktree (it is, since it's committed), nothing extra is needed. The goal folder travels with the
  branch."*
- `skills/research/references/wi-directory.md:128` makes it load-bearing: *"During build, the goal
  branch's copy is canonical — tick tasks and log in the worktree's `.wi/`."*
- But no phase is ever instructed to commit `.wi/`. A grep across `skills/` finds exactly two commit
  instructions: build's per-task commits (in the worktree) and ship's dossier commits (on the branch).
  dev, brainstorm, research, and plan create `brief.md`/`spec.md`/`tasks.md`/`progress.md` as
  **untracked** files in the main checkout.

`git worktree add -b wi/<slug>` checks out HEAD — untracked files don't follow. So the worktree has no
`.wi/goals/<slug>/` at all: task-runners can't tick the progress.md they're told to tick, ship's
"dossier rides the PR" premise fails, and "main's copy catches up on merge" has nothing to catch up to.

**Fix (pick one, then say it in all three places — build SKILL §1, worktrees-and-subagents.md,
wi-directory.md):**
1. Each phase ends by committing its `.wi/goals/<slug>/` outputs on the current branch (matches
   "main catches up on merge"; costs WIP commits on main), **or**
2. build §1 gains an explicit first step after `git worktree add`: move/copy the goal folder into the
   worktree and commit it as the branch's first commit (`chore(<slug>): goal dossier`), leaving main's
   working tree clean.

Option 2 fits the current design intent best (main never carries unmerged dossiers).

### H2 · rpa delegates the whole build to a skill that no longer exists: `uipath-rpa-workflows`

The UiPath marketplace's skill is **`uipath-rpa`** (verified against the installed
`uipath-marketplace` cache — there is no `uipath-rpa-workflows`). wi names the stale slug in 10 places
across 4 files: `skills/rpa/SKILL.md:19,100,102`, `skills/rpa/references/build-uipath.md:13,34,98`,
`references/uipath-bootstrap.md:29,37`, `references/sdd-template.md:11`.

Worst case is explicit: build-uipath.md:98 — *"If `uipath-rpa-workflows` isn't installed, build can't
proceed — stop with the complete SDD pack"* — and uipath-bootstrap.md:29 tells the run to check the
skills list for that name. A compliant agent stops the build half **while the correct skill is
installed**. (`uipath-platform`, `uipath-maestro-flow`, and `uipath-project-discovery-agent` are all
still correct.)

**Fix:** update the slug everywhere; better, centralize the delegated-skill names in one table in
`uipath-bootstrap.md` that the other files reference, and phrase the availability check by capability
("the UiPath skill that owns `.xaml`/`.cs` authoring — `uipath-rpa` as of 2026-07") so an upstream
rename degrades to a lookup instead of a hard stop. A `validate.py` lint for known-external-slug
strings would have caught this class.

### H3 · Every scripted step hardcodes `python3` — which fails on Windows (proved on this machine)

On this repo's own dev box `python3` resolves to the Microsoft Store stub ("Python was not found…")
while `python` is 3.13.2. The skills/agents contain 12 `python3 ${CLAUDE_PLUGIN_ROOT}/…` invocations:
`check_tokens.py --init` (research §0, build §2.4, rpa §6, build-maestro, build-uipath),
`token_report.py --write` and `check_tokens.py` close-out gate (ship §5.3, §8), `check_mermaid.py`
(scan, ship §3), `moa_review.py` (moa.md:128), and the markitdown probe (uipath-bootstrap.md).

The close-out gate is the sharp edge: ship §8 says the `check_tokens.py` **exit code is the close-out
condition the keep-alive loop waits on** — a command that can't launch on the author's primary platform
(and the natural platform for the UiPath/rpa audience) stalls the very loop wi is built around. The
README already hedges ("`python scripts/validate.py` (or `python3`)"); the skills don't.

**Fix:** standardize the instruction to "run with the platform's Python launcher — `python3`, `python`,
or `py -3`, whichever resolves" once (e.g. in wi-directory.md or a one-line convention in each SKILL's
first script mention), or simply write `python` everywhere and note the fallback. Cheap, high leverage.

### H4 · Two owners tick progress.md — a write race the docs themselves set up

- `agents/wi-task-runner.md:105`: *"Tick the task's checkbox in `progress.md` **only** when the
  self-check is PASS"* — the **runner** ticks.
- `skills/build/SKILL.md:60`: *"tick `progress.md` and commit the task … only when the runner reports
  `Self-Check: PASS`"* — the **orchestrator** ticks.
- `worktrees-and-subagents.md:104`: *"The subagent returns that short report; **you** tick
  `progress.md`, commit, and move on"* — orchestrator again (and its dispatch skeleton never tells the
  runner to tick).

With parallel waves, N runners plus the orchestrator read-modify-write the same file: lost updates,
double ticks, and (per H1) possibly no file to tick at all. It also violates wi-directory.md's own
"one writer per phase" convention.

**Fix:** single writer. The orchestrator owns progress.md during build (it already owns commits and
acts on reports); change wi-task-runner.md to *report* Self-Check and leave the ticking to the
dispatcher. This also removes the runner's only required write outside its task's named files.

### H5 · plan sets `Phase = design-gate` before the pre-gate checker has run — resume skips verification

- `skills/plan/SKILL.md:62` (step 5): *"Mirror the task titles into progress.md, set Phase =
  design-gate, and stop."*
- `skills/research/SKILL.md:74-80` (§2): after plan returns, dispatch the checker in plan mode, loop
  BLOCKERs (max 2 rounds), *"Then Phase = design-gate."*
- `skills/research/SKILL.md:36` (§0): resume = *"re-enter the phase it names (research | plan |
  design-gate)."*

As written, the phase flips to `design-gate` at the end of plan. Any interruption between plan
finishing and the checker running resumes straight into the gate — the plan-mode verification is
silently skipped, which is precisely the "silent scope-reduction" class the checker exists to catch.

**Fix:** plan leaves Phase = `plan` (research owns the transition after the checker passes), **or**
the design-gate re-entry requires a fresh plan-mode `verification.md` and dispatches the checker first
when it's missing/stale. Either close works; today the two files disagree.

### H6 · (new in #16) A configured cross-provider check silently replaces the goal-level result check

PR #16 rightly folded the free-floating "reviewer" into wi-code-checker — but ship's merged block makes
the script *replace* the agent pass instead of layering onto it, and the docs now disagree:

- `skills/ship/SKILL.md:43-56`: dispatch wi-code-checker in result mode, *"refreshing
  `verification.md`"* — then: when a provider + API key are present, *"this pass **runs as** an
  independent cross-provider check … through `moa_review.py` → `moa-review.md`"*, with the Claude
  checker dispatch demoted to the **fallback** branch (unconfigured / exit 2 / exit 3).
- `references/moa.md:142` promises the opposite: *"the cross-provider path is a layer on top of
  checker, **never a replacement**."*
- The accepted spec (`docs/specs/2026-07-02-moa-role-redesign-design.md` §2) sides with ship — and its
  "no runtime behavior regression" goal misses that pre-#16 ship ran **both** blocks (the MoA review
  *and* the checker's result mode were separate steps).

When a provider is configured (the smart preset), the regression is real: `moa_review.py` receives only
the diff + spec text — no Read/Grep/Bash against the repo — so "delivered and **wired**, not just
present" is unverifiable; nothing refreshes `verification.md`, which ship §2's own first sentence,
§5.2's prune step, and `PR.md`'s Verification block all assume exists; and "ship never opens the PR on
a goal wi-code-checker says isn't met" is vacuous because wi-code-checker never looked. The two layers
are different checks, not two providers of one check: the cross-provider diff review is *line-level*
(it belongs beside ship §2's self-review), the checker's result mode is *goal-level*.

**Fix:** run both under the existing max-2-round budget — the cross-provider diff review (when
configured) *and* the agent-dispatched result pass that refreshes `verification.md` — or explicitly
re-scope the script as a line-level review layer. Then make `moa.md:142` and ship §2's opening sentence
say the same thing, whichever is chosen.

---

## Medium — drift and contradictions that misdirect an agent

### M1 · "goal" is wi's most overloaded word — decided 2026-07-02: the work unit becomes **feature**

Three meanings collide: the work-unit folder (`.wi/goals/<slug>/`), the retired autonomous *engine*
named `goal` (still haunting ~11 lines: `skills/brainstorm/SKILL.md:17,18,83,90,123` — "the autonomous
engine (`goal`)", "let `dev` handle the handoff to `goal`" — `skills/research/SKILL.md:116`,
`skills/research/references/workflow.md:11-13,45,78`,
`skills/research/references/wi-directory.md:136`), and the keep-alive command `/goal`, which is
**Claude Code's / Codex's built-in** — external to wi (the plugin ships no command of its own). An
agent told to "hand off to `goal`" can pick any of the three.

**Decision (maintainer, 2026-07-02):** retire "goal" as the work-unit name — the unit becomes a
**feature**, the folder `.wi/goals/` → **`.wi/features/`**, prose follows ("feature dossier", "feature
branch", "per-feature ledger"). Why `feature` over the other candidate, `plans`: both manifests already
advertise the unit that way (*"/wi:dev brainstorms a feature with you"* — plugin.json:4,
marketplace.json:14), it matches the `feat(<slug>)` commit convention and the `wi/<slug>` feature
branch, and it stays serviceable for fix/refactor/rpa runs; `plans` would collide head-on with the plan
phase, the plan-mode checker, and the spec/tasks artifacts that phase owns.

**Sweep scope (measured on `8d31c35`):** ≈283 matching lines across 40 tracked files (docs/ archives
excluded), 44 of them literal `.wi/goals/` path references in 19 files. Biggest holders: ship SKILL
(39), wi-directory.md (34), the three agent prompts (30), dev SKILL (25). One real format touch:
`_ledger.py:29` writes a `goal: <slug>` frontmatter key into every tokens.md (tests assert it) — rename
the key to `feature:` in template + tests; `check_tokens.py` derives the slug from the *path*
(check_tokens.py:26), so legacy ledgers still verify. **Stays "goal":** the external `/goal` keep-alive
references (README, AGENTS.md, codex/copilot-tools.md, dev §4, manifests) — that's the platform's name,
and once the folder is `features/` it's the only "goal" left, so the collision dissolves. Reword the
checker's "goal-backward" tagline to "works backward from the feature's acceptance criteria" to finish
the job. Migration: per #16's own stance ("predates any real external adoption") a clean break is fine
— dev/rpa step 2 gains one line: a repo with a legacy `.wi/goals/` gets a one-time
`git mv .wi/goals .wi/features`.

**Sequencing:** its own mechanical PR *after* the H1/H4/H5/H6 fixes (they edit the same files; keep
their review readable), then the M2 version bump. Land the `validate.py` dead-name grep (L9) in the
same PR so `goals/`, the engine-`goal`, and the old slug can't creep back.

### M2 · Release hygiene: post-1.0.0 behavior changes with no version bump

`git log 8e8c586..HEAD` (the 1.0.0 release commit → main) contains the whole MoA feature (#14), the
rpa house rules (#13), the agent rename PR (#15, `e9a7e99`), and now the MoA role redesign (#16,
`8d31c35`), yet `.claude-plugin/plugin.json` still says `1.0.0`. The hazard is observable live on this
machine: the installed cache (`~/.claude/plugins/cache/wi/wi/1.0.0/agents/`) still serves
`name: checker|researcher|task-runner` (pre-rename), while the current session — loading fresher bytes
— registers `wi:wi-code-checker` / `wi:wi-researcher` / `wi:wi-task-runner`: two different byte-states,
both stamped 1.0.0. "Same version, different bytes" makes support/repro guesswork; it stays that way
until a bump + `/plugin marketplace update` republish.

**Fix:** bump to 1.1.0 now; adopt "any change under `skills/`/`agents/` bumps the version in the same
PR" (the README's own maintenance section implies it); optionally have `validate.py` warn when the
tree differs from the last tag at an unchanged version.

### M3 · Agent naming is inconsistent three ways

`wi-researcher` and `wi-task-runner` follow `wi-<role>`; the checker is `wi-code-checker` (file +
`name:`) while every skill and the README call it "the checker" (the third inconsistency — MoA's
`checker` role key — was resolved by #16, which keys MoA roles by the full agent names). The namespace
stutter is no longer a prediction: this session registers `wi:wi-code-checker` / `wi:wi-researcher` /
`wi:wi-task-runner` (the pre-rename cache registered the much cleaner `wi:checker`). The `wi-` prefix was
a deliberate cross-platform tag (PR #15), fine — but then the checker should be `wi-checker` for
symmetry, and the stutter on Claude is worth an explicit note in the agent files or README so nobody
"fixes" it back. Related staleness: `AGENTS.md:13` still says *"plus **two** subagent prompt templates
under `agents/`"* — there are three.

### M4 · ship's dev-shaped hard-codings fight the rpa flow it's told to serve

rpa §7 says "reuse the **ship** skill" with an artifact mapping, but ship's own text stays dev-only:

- ship §5.1's stray-sweep whitelist ("Project-level files stay where they are: constitution.md,
  repo-map.md, overview.md, architecture.md, glossary.md, roadmap.md, adr/, learnings.md, learnings/")
  omits every rpa project-level file — `rpa-constitution.md`, `sdd-template.md`, `inputs.md`,
  `components.md`, `orchestrator.md` (rpa-directory.md:17-21 says these "persist across runs, never
  pruned"). A literal sweep relocates or deletes them as strays.
- ship §5.4 / §8 pin "dossier = **exactly the seven files**", while the rpa dossier is ~11 files plus
  `processes/<p>/tobe.md` (rpa/SKILL.md:129).

**Fix:** make ship read the applicable dossier manifest instead of hard-coding it — e.g. a
`Dossier:`/`Flow: dev|rpa` line in progress.md, or "the fixed dossier per the flow's directory
reference (wi-directory.md / rpa-directory.md)". At minimum, add "RPA runs: see rpa/SKILL §7 mapping"
callouts inside ship §5 and §8, where the executing agent will actually be reading.

### M5 · Skill descriptions summarize workflow (the SDO trap), and scan's is over the limit

superpowers:writing-skills is explicit — and cites test evidence — that a description which summarizes
the workflow becomes a shortcut: the agent follows the description and skips the body. Most wi
descriptions do exactly that (build's lists "creates a dedicated worktree + branch, runs each task's
failing-test-first cycle, commits per task, ticks progress.md"; ship's lists its entire §1-§8
pipeline; dev's narrates the whole loop). Sizes: scan **1070 chars** — over the 1024-char `description`
cap in the agent-skills spec (Claude currently tolerates it; other loaders may truncate) — dev 831,
ship 724, rpa 691.

**Fix:** keep the rich *trigger* phrases (they're good and they're what auto-trigger needs), cut the
step-by-step *process* summaries; get every skill under 1024 (scan first). Add a description-length
check to `validate.py`. Agent descriptions with `<example>` blocks are a different convention and are
fine as-is.

### M6 · question-patterns.md contradicts the brainstorm contract

`skills/brainstorm/references/question-patterns.md:11` (and its frontmatter description): *"The
brainstorm phase gets **one round** of questions."* The skill it serves says the opposite —
brainstorm/SKILL.md:23 "Batch related questions into **focused rounds**… the answers come from the
user", :86 "Ask in focused rounds; stop when the WHAT is clear", and dev §4 sends the run back for
"one more brainstorm round" on a hole. An agent that obeys the reference crams everything into one
round and self-answers the remainder — the exact monologue failure brainstorm/SKILL.md:20-24 warns
against. **Fix:** "a handful of focused rounds — make each count."

### M7 · Stale integration facts

- `skills/research/references/integrations.md:71-74`: *"`wi:rpa` **(planned)** will be another
  command…"* — rpa shipped at v0.7.0 and is a headline feature of 1.0.0.
- The rpa surface descriptions are pre-Maestro: `skills/rpa/SKILL.md` description ("builds a
  REFramework project"), `.claude-plugin/plugin.json` and `marketplace.json` ("into a built
  REFramework solution") — while the README's roadmap and the skill body make `Framework:
  reframework | maestro` a first-class gate choice. A "build a **Maestro flow** from this PDD" request
  matches none of the advertised trigger language. **Fix:** mention Maestro in all three descriptions.

### M8 · The keep-alive handoff block is maintained in three copies

The `/goal` condition line + the Copilot Autopilot command + the ⚠️ unattended-run warning are
duplicated verbatim in dev §4 (`skills/dev/SKILL.md:76-95`), research §4
(`skills/research/SKILL.md:119-141`), and (abridged) README. Three copies of a security-relevant
warning and an exact command template is drift waiting to happen — this review found them still in
sync, which is the best time to deduplicate. **Fix:** extract to
`references/keep-alive.md` (both skills already lean on `${CLAUDE_PLUGIN_ROOT}` references), or add a
`validate.py` check asserting the blocks are identical.

### M9 · (new in #16) main's own validator is red — and nothing at merge time would have caught it

`python scripts/validate.py` on `8d31c35` fails:
`docs\plans\2026-07-02-moa-role-redesign.md: OKF — no frontmatter (needs a non-empty 'type')`. The file
is a superpowers writing-plans artifact and opens directly with `# MoA role redesign Implementation
Plan` — no OKF frontmatter block (its companion,
`docs/specs/2026-07-02-moa-role-redesign-design.md`, is conformant: `type: Design Spec`). A red
validator is worse than a missing one: every *new* violation now hides behind the known failure, and
the truncation guards (trailing newline, fence balance) quietly stop protecting the tree the moment
people stop expecting green.

**Fix, two halves:**
1. **Make it green again** — either give the plan doc minimal OKF frontmatter (`type: Implementation
   Plan` + title/description/timestamp, one paste), or deliberately exempt generated plan artifacts
   (skip `docs/plans/` in validate.py) if superpowers-formatted plans are meant to keep their native
   shape. Pick one on purpose; don't leave it red.
2. **Make it stay green** — `.github/` is empty, so nothing runs the validator at merge time. A
   ~10-line `validate.yml` (checkout → setup-python → `python scripts/validate.py`) closes the gap and
   is the natural home for every L9 lint this review proposes.

---

## Low — polish, robustness, hygiene

- **L1 · CRLF breaks ship's frontmatter strip.** ship §7/§8's
  `awk 'NR==1&&$0=="---"{f=1;next} f&&$0=="---"{f=0;next} !f'` compares whole lines; on a Windows
  checkout with `core.autocrlf=true` the lines are `---\r` and the strip silently no-ops — the PR body
  ships with raw OKF frontmatter on top. Harden with `sub(/\r$/,"")` first (and note `mktemp`/`awk`
  assume Git Bash on Windows — true for Claude Code, not guaranteed for Copilot CLI).
- **L2 · scan `--refresh` step 3 gives a non-runnable git command.** `git diff --stat <approx. scan
  date>..HEAD` — `git diff` takes refs, not dates. Give the working form, e.g.
  `git diff --stat $(git rev-list -1 --before="<scan date>" HEAD)..HEAD` (or `git log --stat --since`).
- **L3 · The checker must write `verification.md` but has no Write tool.**
  `agents/wi-code-checker.md:6` grants Read/Grep/Glob/Bash, yet §Output requires writing the file and
  confirming its frontmatter parses — forcing a Bash heredoc write, the exact interrupted-write pattern
  that produced this repo's truncation guard. Either add `Write` (keeping "read-only" as "read-only
  toward the *project*; writes only `.wi/goals/<slug>/verification.md`") or have the orchestrator
  persist the file from the checker's returned report.
- **L4 · task-runner's `auth-gate` outcome has no completion marker.** The report status enum is
  `done | blocked | auth-gate` (wi-task-runner.md:108) but the machine-parsed last line offers only
  `## TASK COMPLETE` / `## TASK BLOCKED` (:116). Specify the mapping (auth-gate ⇒ `## TASK BLOCKED`)
  or add `## TASK AUTH-GATE` — build §2.4 branches on this state, so it shouldn't be ambiguous.
- **L5 · Lazy/truncated reference descriptions.** workflow.md's description ends mid-sentence ("…run
  by..."), integrations.md's is "wi is deliberately thin.", pitfalls-catalog's "A foresight
  checklist.", question-patterns' repeats the wrong one-round claim (M6). Since OKF indexes reuse
  `description`, these are worth one tightening pass — and `validate.py` could flag descriptions
  ending in `...`.
- **L6 · Examples predate the numbered-slug convention.** adr-template.md's index example rows use
  `event-store` / `task-tags` goals; templates get copy-pasted, so show `0001-event-store` form.
  (Checked the other templates — progress/tobe/ingest are already `NNNN-` aware.)
- **L7 · Internal-tracker references in shipped docs.** moa.md:122 "rejected as cost-prohibitive — see
  issue #12's scope revision" (also moa_review.py's docstring); the agent frontmatter comments cite
  spec IDs ("# X3: …"). Installed-plugin readers can't resolve either; state the rationale inline.
- **L8 · dev step 2 is a wall.** One paragraph carries ordinal assignment, resume detection, in-flight
  overlap, done-slug collision, and roadmap dependency stacking. It's all good content — split it into
  the five sub-bullets it actually is, so a resuming agent can find the rule it needs.
- **L9 · No behavioral tests for the skills themselves.** The scripts are unit-tested
  (`tests/test_moa_config.py`, `tests/test_tokens_guardrail.py`) and validate.py guards structure, but
  nothing exercises skill *behavior* (superpowers' writing-skills would call for baseline/pressure
  scenarios per change). Pragmatic middle ground: extend `validate.py` with the mechanical lints this
  review kept wishing for — description length (M5), known-external-slug allowlist (H2), duplicated
  keep-alive block consistency (M8), dead-name greps (`` `goal` ``, `uipath-rpa-workflows`) — each is a
  regex away and each would have caught a real finding above.

---

## Suggested order of attack

1. **M9 + H2 + H3** — same-day fixes: re-green the validator (one paste) and wire it into CI so it
   stays green, then un-break the rpa build half and the close-out gate on Windows.
2. **H1 + H4 + H5 + H6** — decide the dossier-commit model, the single progress.md writer, the
   design-gate transition owner, and the two-layer ship verification together; one coherent "state on
   disk + verification chain" tightening across build/plan/research/ship SKILLs +
   worktrees-and-subagents.md + wi-directory.md + wi-task-runner.md + moa.md.
3. **M1** — the decided `goal` → `feature` rename as its own mechanical PR (folder, prose,
   `_ledger.py` key + tests; `/goal` stays), right after the H-fixes so it doesn't tangle their diff.
4. **M2** — bump to 1.1.0 and republish so the installed plugin matches the repo (and the agent rename
   actually reaches sessions from the cache, not just this checkout).
5. **M6, M7, M3/AGENTS.md** — the remaining stale-name sweep, in one PR.
6. **M4, M5, M8** — ship parameterization, description diet, keep-alive dedup.
7. The **L** items as a rolling polish PR; fold the L9 lints into `validate.py` first so the sweep
   stays swept.
