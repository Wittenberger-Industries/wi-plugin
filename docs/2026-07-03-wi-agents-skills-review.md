---
type: Review
title: Review — the 3 wi agents & 8 skills, second pass (post-fix rescan)
description: Fresh full-source review after the 2026-07-02 review's 21 fixes landed (H1-H6, M1-M9, L1-L9) — 3 new High, 8 Medium, 12 Low findings, ranked with evidence and concrete fixes.
timestamp: 2026-07-03
tags: [review, agents, skills, quality]
---

# Review — the 3 wi agents & 8 skills (second pass)

Scope: everything under `agents/` and `skills/` (all 8 SKILL.md + all 24 reference files), plus
`references/`, `README.md`, `AGENTS.md`, and the three manifests — read in full on branch
`review-fixes-2026-07` (`b0926b0`), cross-checked against `scripts/validate.py` and a mechanical
sweep (rename residue, old agent names, cross-file path validity, `.wi/` tree consistency, slug
validity, stated counts).

**State of the previous review:** all 21 findings from `2026-07-02-wi-agents-skills-review.md`
(H1-H6, M1-M9, L1-L9) verifiably landed on this branch, and the fixes are *good* — the two-layer
ship verification (H6) is now unambiguous where it was rewritten, the dossier-commit model (H1) is
coherent on the dev path, the single progress-writer (H4) is stated in all three places, the gate
transition (H5) has both belt and suspenders, and `validate.py` is green with the new lints wired
into CI. This pass hunts what the sweep itself introduced or missed. The pattern of what it found:
**every High is a place where a fix or feature was applied to one path (dev / REFramework / one
file) and not its mirror** (rpa / Maestro / the sibling file).

Mechanical sweep results worth stating up front, because they're clean: every cross-file path in
skills/agents/references resolves; every `/wi:` command and external skill slug is real; all stated
counts (3 agents, 8 skills, seven-file dossier, six rollback files) are correct; no `.wi/goals`
residue outside the two intentional migration commands; the keep-alive block is genuinely
single-sourced now.

---

## High — will break or silently corrupt a run

### H1 · `sdd.md §13` doesn't exist — the RPA acceptance-criteria anchor points at nothing

Seven references across five files gate the entire RPA verification chain on "acceptance criteria
§13":

- `skills/rpa/SKILL.md:72` (pre-gate checker dispatch: "`sdd.md` (acceptance criteria §13 + locked
  decisions)") and `:110` (result-mode check "over `sdd.md` §13")
- `agents/wi-code-checker.md:50` ("acceptance criteria in §13; locked decisions across §1-§7")
- `skills/rpa/references/verification-gate.md:74`, `:86`, `:88`
- `references/moa.md:133` ("`spec.md` (or `sdd.md` §13)")

But the base ToC in `skills/rpa/references/sdd-template.md` runs **§1-§9** and contains **no
acceptance-criteria section at all** — §8 is "Other remarks" (assumptions, open questions, risks),
§9 is UiPath Apps. A checker dispatched in plan mode to build a coverage matrix from "§13" of a
base-ToC SDD finds no such section; whatever it does next (invent criteria from §7? return a
BLOCKER against its own template? silently skip) is undefined behavior at the exact point wi
promises rigor. The template even instructs "fill every section from the design; if a section can't
be filled, that's a brainstorm gap" — and then doesn't have the one section five other files verify
against.

The deeper fragility: the ToC is *deliberately overridable* (an existing client SDD's ToC wins —
sdd-template.md precedence rule 1), so **any** hard-coded section number is wrong by design for
exactly the client-standard case the precedence rules exist to serve.

**Fix, two halves:**
1. Add an explicit `## Acceptance criteria` section to the base ToC (the natural home is a
   dedicated section between §7 and "Other remarks" — one criterion per line, each naming its
   verifying check, mirroring `spec.md`), and mark it **never omitted, whatever ToC wins** — when a
   client ToC has no such section, it is appended.
2. Everywhere else, reference it semantically, not numerically: "the SDD's acceptance-criteria
   section" (optionally "(§10 in the base ToC)"). Then a client ToC can't break the anchor. Add the
   dead string `sdd.md §13` / `SDD §13` to `validate.py`'s dead-strings lint so it can't creep back.

### H2 · The Maestro build path lacks the Isolate step — the dossier never reaches the worktree

The 07-02 review's H1 fix (move the feature folder into the worktree, commit it as the branch's
first commit) landed in `skills/build/SKILL.md` §1 **and** in `skills/rpa/references/build-uipath.md`
§1 ("Isolate", lines 21-27) — but `skills/rpa/references/build-maestro.md` has **no Isolate section
at all**: it opens directly with "## 1. Execute the build DAG in waves". `skills/rpa/SKILL.md:96`
says only "Create the worktree, reuse components…, then build per the Framework" and delegates the
rest to the framework reference — so on the REFramework path the move happens (the reference has
it) and on the Maestro path it doesn't.

Consequence on `Framework: maestro`: the worktree starts without `.wi/features/<slug>/` (still
untracked on main). `build-maestro.md:29-31`'s "initialize `tokens.md` on the first delegation if
absent" then scaffolds a **fresh, divergent ledger** in the worktree (the real one, with any
pre-build rows, sits on main); `sdd.md`/`tobe.md` aren't readable in-tree for delegations that
resolve paths from the worktree; and ship's "dossier rides the PR" premise fails exactly as
pre-fix — the bug class was closed on three of four paths.

**Fix:** hoist the step to the framework-neutral spot — `rpa/SKILL.md` §6 gains the same sentence
build-uipath.md §1 has ("Same first step as `wi:build`: move `.wi/features/<slug>/` into the
worktree and commit it as the branch's first commit; skip if already there") — or give
build-maestro.md its own §0/§1 Isolate mirroring build-uipath.md. Hoisting is better: one statement
instead of two copies (the same drift that produced this finding).

### H3 · Project-level `.wi/` files have no commit owner — ADRs never ride the PR, and ship's docs-sync can collide on merge

The H1 fix defined a commit lifecycle for the **feature folder** only. Project-level `.wi/` files —
`constitution.md`, `repo-map.md`, `overview.md`, `architecture.md`, `glossary.md`, `adr/`,
`roadmap.md`, `moa.md` — are written by scan/brainstorm/research/dev on the main checkout and **no
phase is ever instructed to commit them**:

- `skills/scan/SKILL.md:22` claims "Outputs (all under a **committed** `.wi/`)" — but scan's
  procedure (steps 1-6) contains no commit step. The claim is aspiration, not instruction.
- `skills/research/references/wi-directory.md:48` says "**Commit `.wi/`.** It is documentation" —
  then specifies the lifecycle only for `features/<slug>/`.
- `skills/build/SKILL.md:35` states the ground truth: "no phase before build commits it".

What breaks, concretely:

1. **ADRs don't reach the branch or the PR.** research §1d writes `.wi/adr/ADR-NNNN` on main,
   uncommitted. The worktree is created from HEAD, so it has no `.wi/adr/`. Yet ship §2
   (`skills/ship/SKILL.md:40-41`) dispatches the result-mode checker "against `spec.md`'s
   acceptance criteria + locked decisions (**ADRs**, constitution)" — read from the worktree,
   there are none — and `PR.md`'s `### Decisions` block (`ship/SKILL.md:226`) links
   `.wi/adr/ADR-NNNN-*.md`, a path that resolves neither on the branch nor for a PR reviewer.
   After merge, the ADR is *still* untracked — the "project memory compounds" promise holds on one
   machine only.
2. **Ship's docs-sync forks the scan docs.** ship §3 updates `.wi/architecture.md` /
   `overview.md` / `repo-map.md` *in the worktree* and commits them on the branch. In any repo
   whose scan outputs were never hand-committed by the user, those files don't exist in the
   worktree — ship re-creates them from scratch (§3's "if it doesn't exist yet… create it now"
   assumes greenfield is the only absence case; uncommitted-scan is the common one). On merge,
   main then holds an incoming tracked `architecture.md` **and** its own untracked scan-era
   `architecture.md` at the same path — `git merge` refuses ("untracked working tree file would be
   overwritten") right at the finish line of a hands-off run, or the two silently fork.
3. **`.wi/moa.md` is read from an undefined location.** dev step 1 / rpa step 2 write it on main.
   ship §2 branches the cross-provider layer on "`.wi/moa.md`'s `## Cross-provider config`" — an
   agent whose CWD is the worktree reads a missing file and logs `cross-provider layer skipped`,
   silently disabling a configured check. Which checkout's `.wi/` each post-worktree phase reads
   is currently unstated for everything except the feature folder.

**Fix:** give project-level files the commit rule the feature folder got — *committed where they're
written, by the phase that writes them*: scan commits its four docs (+ the greenfield `.gitignore`),
brainstorm commits glossary updates, research commits the ADR + index row, dev/rpa commit `moa.md` /
`roadmap.md` (`chore(wi): …` / `docs(wi): …` subjects). State it once in wi-directory.md's
Conventions ("project-level `.wi/` files are committed where they're written; only the feature
folder defers to build's first branch commit") and add the one-line commit instruction to each
writing phase. That makes scan's "committed `.wi/`" true, puts ADRs on the branch (research commits
on main *before* build branches from HEAD), lets ship §3 edit tracked files instead of re-deriving
them, and makes "which `.wi/` do I read" moot — the worktree carries current copies. Teams that
don't want wi committing to main can override in the constitution; say so in the same bullet.

---

## Medium — contradictions and drift that misdirect an agent

### M1 · `check_points: per-wave` triggers three different things depending on which file you read

- `skills/build/SKILL.md:84-88` (wave-end gate): when per-wave, "also run **the cross-provider
  diff review** … over the wave's diff" — the script layer only.
- `references/moa.md:117` (RESULT mode): "(ship, and — when `check_points: per-wave` — each build
  wave-end gate)" — the **checker dispatch itself** runs per-wave.
- `references/moa.md:111`: the checker "always runs **twice per feature**" — contradicting :117
  three bullet-points above it.

Recommendation: per-wave scopes the **cross-provider layer only** — it matches build §2, keeps
"twice per feature" true, and mid-build there is no complete feature for a result-mode pass to
verify anyway. Fix is one parenthetical: move moa.md:117's per-wave clause off RESULT mode and onto
the diff-review sentence (its own §cross-provider already says it right: "additionally at each
build wave-end gate over that wave's diff").

### M2 · ship prunes `verification.md` in §5.2 but distills it into `PR.md` in §6 — and calls the prune "close-out"

Order of operations in `skills/ship/SKILL.md`: §5.2 deletes `verification.md` + `moa-review.md` →
§5.5 commits the tidy → §6 writes `PR.md`, whose template says the Verification block is
"Distilled from verification.md, which is pruned at close-out" (`:220`). Two problems:

1. **Resume hazard:** a run interrupted between §5.2 and §6 resumes with the checker verdict
   deleted from disk and `PR.md` not yet written — the Verification block can no longer be
   reconstructed. "State on disk" is wi's own first principle; this is the one step that deletes
   state it still needs.
2. **Wording drift:** the prune actually happens at §5 (pre-PR), but three places say "pruned at
   close-out" (`ship/SKILL.md:220`, `agents/wi-code-checker.md:103`,
   `wi-directory.md:36`/`rpa-directory.md:56` say close-out too) — §8's close-out only *verifies*
   pruned.

**Fix:** distill first, delete second — swap the order so §6 (write `PR.md` from
`verification.md`/`moa-review.md`) runs before the §5.2 prune, or move the prune into §8's
checklist proper. Then make the three "pruned at close-out" phrasings match whichever spot wins.

### M3 · The close-out box "worktree removed; merged branch deleted" can't be honestly ticked when the PR just opened

`ship/SKILL.md:258` : "After the PR is open (or merged), clean up: remove the worktree and delete
the merged branch", and the §8 checklist (`:276`) requires "worktree removed; merged branch
deleted" before `Phase = done`. On the normal path the PR was opened seconds ago and is **not
merged**. A literal agent either can't tick the box (close-out blocks, the keep-alive loop that
waits on Phase = done spins) or resolves the tension by deleting the branch — and deleting the
*remote* branch closes the open PR. The worktree reference gets it right
(`worktrees-and-subagents.md:43-47`: `git branch -d` "if fully merged"); the checklist is the blunt
copy.

**Fix:** make the box conditional and explicit: "worktree removed; **local** branch deleted only
if fully merged (`git branch -d`, which refuses otherwise); the remote branch and an open PR are
never deleted". Removing the worktree post-push is safe and can stay unconditional.

### M4 · The directory references omit files ship's stray-sweep must protect

ship §5.1's whitelist rule is "the flow's directory reference's project-level list … when in doubt
the directory reference wins". But:

- `wi-directory.md` contains **zero** mentions of `moa` — neither `.wi/moa.md` (a project-level
  config file sitting loose in `.wi/`, exactly what the sweep hunts) nor `moa-review.md` (a
  feature-folder ephemeral that `ship/SKILL.md:49` and `moa.md:135` both write; the ephemera
  bullet lists only `research/` + `verification.md`). The MoA config is literal sweep-bait under
  the "no strays loose in `.wi/`" convention.
- `rpa-directory.md`'s project-level list (`:49-51`) and tree omit `adr/` — while its own
  Conventions (`:66-67`) say ADRs "go in the project-wide `.wi/adr/` log, same as `wi:dev`". An
  rpa-flow sweep that follows its whitelist relocates or deletes the decision log. Same omissions:
  `moa.md`, `roadmap.md`, and the dev project files (`constitution.md`, `repo-map.md`, …) for the
  realistic repo where both flows have run.
- Cosmetic: README's `.wi/` tree also omits `moa.md`.

**Fix:** add `moa.md` to both project-level lists and trees; add `moa-review.md` to
wi-directory.md's feature tree + both ephemera bullets; extend rpa-directory's whitelist with
`adr/` (+ `roadmap.md`), plus one line covering mixed repos: "a repo that also carries dev-flow
project files: the whitelist is the union of both directory references".

### M5 · rpa §2 re-conflates the two verification layers the H6 fix just separated

`skills/rpa/SKILL.md:41-42`: "**wi-code-checker runs its ship-phase cross-provider check** per the
same rules as `wi:ship`." The checker never runs the cross-provider check — the whole point of the
H6 fix (ship §2, `moa.md:150`) is that the script layer runs **beside** the checker's result-mode
pass, never as it or instead of it. One sentence of exactly the vocabulary the redesign retired.
**Fix:** "…and at ship the cross-provider diff review layers on top of wi-code-checker's
result-mode pass, per the same rules as `wi:ship`."

### M6 · `.codex-plugin/plugin.json` is still 1.0.0 with a pre-Maestro description

The M2 bump reached `.claude-plugin/plugin.json` and `marketplace.json` (both 1.1.0) but
`.codex-plugin/plugin.json:3` still says `1.0.0`, and its description is REFramework-only (no
Maestro, no `--refresh`, no keep-alive wording the other two carry). Root cause is structural: the
README's own versioning rule (`README.md:199-205`) names only the two Claude manifests, and
`validate.py` checks the Codex manifest declares name/version/skills but not that versions agree.
**Fix:** bump + refresh the description now; name all three manifests in the README rule; add a
three-way version-parity check to `validate.py` (three lines, prevents this class forever).

### M7 · README still describes MoA in the retired role vocabulary — and rpa as REFramework-only

- `README.md:155-158`: "`.wi/moa.md` assigns models per role — orchestrator (informational),
  **execution, checker**, and an independent cross-provider **reviewer** … that code-reviews the
  finished feature." Post-#16 the roles are keyed `wi-code-checker` / `wi-researcher` /
  `wi-task-runner` — there is no `execution` role, and the cross-provider layer is deliberately
  *not* a "reviewer" role (that framing is what #16 removed; commit `b0926b0` fixed the script's
  wording but missed this bullet). A reader configuring `.wi/moa.md` from the README writes rows
  the dispatch rule will never look up.
- Maestro is missing from the three README spots that describe rpa: the command table (`:20`
  "builds a REFramework solution"), the flow diagram (`:70` "-> REFramework build ->"), and the
  skills table (`:118`) — while the README's own roadmap (`:220`) says Maestro shipped as a
  first-class framework. The M7 fix reached plugin.json and the skill description but not the
  README body.

**Fix:** reword the MoA bullet with the real role names + "cross-provider diff review (a layer on
top of the checker's result mode)"; add "REFramework or Maestro" in the three spots.

### M8 · workflow.md's resume contract omits the design-gate re-entry guard

The H5 fix added the guard to `research/SKILL.md:34-37` (resuming at `design-gate` requires a fresh
plan-mode `verification.md`, else run the checker first). But
`skills/research/references/workflow.md` — self-described as the canonical "Phase contracts &
resumability" reference — still says only "Resume = read it and re-enter that phase" (`:28`), and
its contracts table has no trace of the guard. An agent resuming from the reference alone re-enters
the gate without the pre-gate verification — the exact hole H5 closed, alive in the file whose one
job is resume semantics. **Fix:** one footnote on the design-gate row: "re-entry requires a fresh
plan-mode `verification.md`; missing or older than `spec.md`/`tasks.md` → run the checker pass
first (research §0)."

---

## Low — polish, hygiene, one-line fixes

- **L1 · Stale agent name in integrations.md.** `integrations.md:33` "the `researcher` agent" —
  the registered name is `wi-researcher` (the build row two lines down correctly cites
  `agents/wi-task-runner.md`).
- **L2 · moa.md points at the wrong dev step.** `moa.md:93` "(dev step 2, rpa step 2)" — dev's MoA
  first-run setup lives in **step 1** (`dev/SKILL.md:29-32`).
- **L3 · The gate template assumes an ADR always exists.** `research/SKILL.md:93` hardcodes
  "**Approach (ADR-NNNN):**" while plan §2 / adr-template make ADRs conditional ("Trivial features
  get no ADR — don't manufacture decisions"). Say what to render when none exists: "Approach: …
  (no ADR — nothing hard to reverse)".
- **L4 · `[docs]` task tag is used but not in the enum.** plan step 4 says substantial doc work
  "gets its own `[docs]` task", but the tasks.md format line (`plan/SKILL.md:79`) offers only
  `[backend|frontend|infra|test]`. Add `docs` (and note it has no routing behavior, unlike
  `frontend`).
- **L5 · dev counts its own interactions two ways.** `dev/SKILL.md:14` "two interactive moments —
  brainstorm and the design gate" vs Boundaries (`:98-99`) "brainstorm **+ a one-line handoff
  confirmation +** the design gate". Either fold the confirmation into the brainstorm stop (like
  the preflight already is) or say "two conversations plus a one-line confirmation" up top.
- **L6 · `pdd-images.md` is referenced but never produced.** `brainstorm-protocol.md:51` reads
  "(+ any recovered diagram descriptions in `pdd-images.md`)" — no step in ingest.md (whose §1
  handles dropped images) ever creates or names that file. Name it as ingest §1's recovery output,
  or drop the parenthetical.
- **L7 · The checker still says "the fixed seven-file dossier rule" unqualified.**
  `wi-code-checker.md:104` — that's the dev manifest; the agent explicitly serves rpa runs (its own
  RPA mapping, ~11 files). Say "the flow's fixed dossier manifest is preserved".
- **L8 · rpa-constitution's Gate section isn't framework-aware.**
  `rpa-constitution-template.md:113` "Output matches the gate-approved paradigm — always
  REFramework XAML" is wrong under `Framework: maestro` (the template's own Framework section
  supports maestro; the verification-gate reference branches correctly). Qualify: "REFramework
  runs: …".
- **L9 · rpa's H1 heading predates Maestro.** `rpa/SKILL.md:11` "— PDD → SDD → built REFramework
  project" (the description and defaults are already framework-aware). "…→ built RPA solution
  (REFramework or Maestro)".
- **L10 · marketplace.json's plugin description says "/goal-driven".** `marketplace.json:14`
  "Opinionated dev loop for /goal-driven work" vs plugin.json's updated "built for
  keep-alive-driven work" — align to keep-alive (also truer on Copilot, which has no `/goal`).
- **L11 · Three placeholders for one path.** The rpa feature folder is `<run-slug>`
  (rpa-directory:26), `<slug>` (rpa/SKILL:104, build-uipath:77, build-maestro:31), and `<run>`
  (sdd-template:4,40). Normalize on `<run-slug>`.
- **L12 · task-runner names design skills by marketplace id in a skills-list context.**
  `wi-task-runner.md:58-59` "available in your skills (`frontend-design` primary;
  `pbakaus/impeccable` for polish, `leonxlnx/taste-skill` …)" — in a session's skill list those
  surface as bare `impeccable` / `taste-skill`; the owner-qualified ids belong in
  integrations.md/plugin-bootstrap (where they already are). Match by bare name here.

---

## Suggested order of attack

1. **H1 + H2** — same-day, small diffs: give the SDD its acceptance-criteria section and make the
   references semantic (+ the `§13` dead-string lint); hoist the dossier-move into rpa §6 so
   Maestro isolates like everything else.
2. **H3** — decide and write the project-level commit model (one Conventions paragraph + one
   commit line per writing phase). It unblocks the ADR→checker→PR chain and settles which `.wi/`
   post-worktree phases read.
3. **M1 + M2 + M3** — one coherent pass over ship/SKILL.md + moa.md + wi-code-checker.md: per-wave
   semantics, distill-before-prune, and the merged-branch checklist wording. Same files, one PR.
4. **M4** — right after H3/M1, since the commit model and moa artifacts change what the directory
   references must list.
5. **M5-M8 + L1-L12** — the wording/manifest sweep, one mechanical PR; fold the two validate.py
   additions (manifest version parity, `§13` dead string) in first so the sweep stays swept.

One structural observation for the maintainer, no action required: three of the four Highs across
both reviews trace to the same root — a rule stated in one file and mirrored by hand into siblings
(dev↔rpa, REFramework↔Maestro, skill↔reference). Where a rule must hold across flows, the pattern
that has worked (keep-alive.md, the uipath-bootstrap slug table, the flow-keyed dossier manifest)
is: state it in exactly one file and make the siblings point there. Candidates that are still
hand-mirrored: the worktree-isolate step, the ephemera list, the git-landmine block
(wi-task-runner.md ↔ build-uipath.md §4).
