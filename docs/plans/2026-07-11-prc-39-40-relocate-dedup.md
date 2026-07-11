---
type: Implementation Plan
title: "PR C — #39 relocate dev step 2's rare branches + #40 dedup restated rules (v1.7.1)"
description: Lossless relocation (dev step 2 → references/feature-folder-cases.md) then rule dedup to canonical owners with one-line pointers; rules-map, exact edits, dry-run + load-alone verification.
timestamp: 2026-07-11
tags: [context-budget, dev, dedup, safe-refactor, plan]
---

# PR C — #39 + #40 (v1.7.1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This plan is markdown prose surgery: "tests" are `scripts/validate.py`, `pytest tests/`, grep assertions, file-tail checks, and subagent dry-runs.

**Goal:** land GitHub issues #39 (move dev step 2's six edge-case branches to an on-demand reference) and #40 (deduplicate rules restated across loaded files) as one patch release, v1.7.1 — lossless relocation/dedup, no behavior change.

**Architecture:** #39 first (verbatim move + classifier), then #40 (dedup sweeps the post-#39 text) — the order the triage doc mandates. Every rule keeps exactly one canonical owner; every other site keeps a terse pointer that stays standalone-correct. Baseline: `main@627f655` (v1.7.0). All line numbers below refer to that commit.

**Tech stack:** markdown skill/reference files; `scripts/validate.py`; `pytest tests/`; subagent dry-runs for branch routing and load-alone correctness.

## Global constraints (from the triage doc's guardrails)

- Rules inventory before/after for every commit that moves or rewords rule text; attach to the PR body. Test: *does each touched file still make correct decisions if loaded alone?*
- `python scripts/validate.py` + `pytest tests/` green after every task; check file **tails** after each markdown edit (repo has shipped mid-sentence truncations).
- New files only in whitelisted dirs — `references/` is whitelisted (`!/references/**` in `.gitignore`). No new top-level paths.
- Agent charters: only `wi-task-runner.md` is edited, only its frontend bullet, pointer-form; **never** alter report caps, output markers, verification-gate contracts, or tool lists. `wi-code-checker.md` is deliberately untouched (its frontend check is enforcement duty, not a restatement).
- No AI attribution in commits/PRs.
- Version: `.claude-plugin/plugin.json` and the plugin entry in `.claude-plugin/marketplace.json` → **1.7.1** (patch: relocation/dedup only). The top-level `0.1.0` marketplace schema version stays.

---

## Rules-map (#40's inventory: rule → canonical owner → sites → action)

This section is #40's required rules-map; its commit precedes the code commits (triage: "first commit is the rules-map"). "Kept" = site keeps a pointer or site-specific operational text; "no edit" = already pointer-form.

| # | Rule | Canonical owner | Sites & action |
|---|------|-----------------|----------------|
| R1 | **Ledger rule** — append the `tokens.md` row the moment the completion notification arrives; exact tokens + Duration; `unavailable` when unobservable, never an estimate; no-notification dispatch records `unavailable` | `wi-directory.md` §tokens.md template (named "**the ledger rule**" there; `_ledger.py` owns the bytes) | research/SKILL.md principles + §2 → pointer; build/SKILL.md §2.4 → pointer; rpa/SKILL.md §5 → pointer; ship/SKILL.md §6.3 → pointer; workflow.md §Token budget tail → pointer summary; wi-directory Log-bullet internal dup → trimmed; ship §8 checkbox + final-report wording kept (gate semantics); scripts get a canonical-pointer comment |
| R2 | Two gates, both deliberate; no questions outside them | `workflow.md` §Rules 2–3 | dev §6, research principles → add "(workflow.md's no-questions rule)" anchors; dev Boundaries mode-mapping kept (dev-specific); README kept (docs, not loaded path) |
| R3 | Frontend delegation mandatory when installed; report/log `frontend via …` | `integrations.md` §Frontend work | build §2.3 → operational core + pointer; `agents/wi-task-runner.md` frontend bullet → contract + pointer (alternates list & install-id note drop; they live in the owner); `agents/wi-code-checker.md` check 7 → **no edit** (enforcement duty, cites owner); plugin-bootstrap.md → **no edit** (install offer, not a restatement) |
| R4 | Commit `.wi/` where written (project-level rule) | `wi-directory.md` §Commit `.wi/` | scan, brainstorm, dev, research §1d, rpa ×2, models.md, rpa-directory.md, ship §3 — **all already pointer-form; no edits** (inventory only) |
| R5 | `python` fallback (`py -3` Windows / `python3` Linux-macOS) | **new** `workflow.md` §Script invocation | research §0, build §2.4, ship §3, rpa §5 + §6, build-uipath.md §2.4, models.md diff-review step 2 → each keeps "(python fallback: workflow.md …)" |
| R6 | Keep-alive handoff templates + platform map + "works without it" framing | `references/keep-alive.md` (self-declared single source) | dev §4 print + armed-tail → shrink; research §4 print → shrink; dev intro framing line kept |
| R7 | Model-routing first-run setup + pre-1.3 legacy config migration | `models.md` §First-run setup | dev step 1, rpa step 2 → decision-form + pointer (legacy-rename mechanics drop) |
| R8 | Slug/ordinal numbering rule | `wi-directory.md` §Slugs bullet (absorbs 2 clauses: resumed feature keeps its number; roadmap row numbered at creation) | post-#39 `feature-folder-cases.md` §Ordinal → pointer + case notes; `ingest.md` §1 → pointer; dev step 2 keeps the one-line common-path form |
| R9 | Superpowers precedence — delegation points only | `integrations.md` §Who initiates | dev Boundaries, rpa tail → 2-line pointer form; build §1 / ship §1+§7 already pointers, no edit |
| — | **Deferred to #41:** dossier lifecycle (committed at gate; worktree copy canonical; main catches up) — research §3 / build §1 / rpa §5 / build-uipath §1 / wi-directory ×2 / ship §6 all restate with phase-specific operational detail; judgment-heavy prose, exactly #41's job. **Deferred:** resolve-once trigger phrasing (placed deliberately by #38 in PR #45, already pointer+trigger form). **Deferred:** ship §8 report-side honesty wording (report-rendering guidance, operationally placed). | | |

#39's inventory is clause-level and lives in Task 2/3's verify steps: each of the six branches' sentences must have a verbatim home in `references/feature-folder-cases.md`.

---

### Task 0: Worktree + branch

- [ ] **Step 1:** Via superpowers:using-git-worktrees — create worktree + branch `prc-39-40` off `main` (sibling dir `../wi-plugin-prc-39-40`).
- [ ] **Step 2:** `git status` clean; `git log --oneline -1` shows `627f655`.

### Task 1: Commit this plan (carries #40's rules-map)

- [ ] **Step 1:** Save this file as `docs/plans/2026-07-11-prc-39-40-relocate-dedup.md`.
- [ ] **Step 2:** `python scripts/validate.py` → exit 0.
- [ ] **Step 3:** Commit: `docs: PR C implementation plan + rules-map (#39 #40)`.

### Task 2 (#39): Create `references/feature-folder-cases.md`

**Files:** Create `references/feature-folder-cases.md`.
**Interfaces — produces:** the file dev step 2's classifier (Task 3), wi-directory's xref (Task 4), and rpa's legacy pointer (Task 4) point at. Section anchors: `## Legacy migration`, `## Ordinal assignment (edge cases of the numbering rule)`, `## Resume detection`, `## In-flight overlap`, `## Done-slug collision`, `## Roadmap match & dependency stacking`.

- [ ] **Step 1:** Write the file. Body per branch = the exact sentences of dev/SKILL.md lines 43–69 at `627f655` (bullet markers stripped, indentation reflowed — clause-verbatim), each preceded by a new **Tell:** line. Full content:

````markdown
---
type: Reference
title: "Feature-folder cases — the rare branches of opening a feature"
description: "On-demand handling for the non-default cases hit when opening a feature folder — legacy migration, ordinal edge cases, resume, in-flight overlap, done-slug collision, roadmap rows — factored verbatim out of dev step 2; loaded only when the classifier lands on one."
timestamp: 2026-07-11
tags: [dev, feature-folder, resume, roadmap, reference]
---

# Feature-folder cases — the rare branches of opening a feature

`dev` step 2 classifies every idea — **new / resume / in-flight-overlap / done-collision / roadmap-row /
legacy-repo** — and opens this file for anything but a plain new feature (`rpa`'s run seed routes its
legacy case here too). Each case carries its detection tell and its handling, factored verbatim out of
the skill so nothing changes in substance; the common path (derive slug, assign the ordinal, create the
folder, seed `progress.md`) stays in the skill and never needs this file. Cases compose — a legacy repo
may also hold a resume; a roadmap row still gets an ordinal — so apply every case whose tell fires, in
the order below.

## Legacy migration

**Tell:** the repo's work units still live under the pre-rename folder (`goals`, not `features`).

A repo whose work units still live under the pre-rename folder gets a one-time
`git mv .wi/goals .wi/features` before proceeding — commit it; the dossiers inside are untouched.

## Ordinal assignment (edge cases of the numbering rule)

**Tell:** applies at every creation; the edge cases in the parenthetical are what this section is for.

Derive a kebab-case name, then prefix the **next global 4-digit ordinal** so `<slug>` = `NNNN-<name>`
(e.g. `0001-stripe-webhooks`) — mirroring `ADR-NNNN`: the ordinal is global across `.wi/features/`,
monotonic, assigned **once at creation, never renumbered** (next = highest existing `.wi/features/`
ordinal + 1, else `0001`; legacy unnumbered features are left as-is and ignored by the scan; a resumed
feature keeps its number; a roadmap row's name is numbered when its folder is first created).

## Resume detection

**Tell:** an in-flight feature (`.wi/features/*/progress.md` with Phase ≠ `done`) reads as this same idea.

Scan `.wi/features/*/progress.md` for Phase ≠ `done`. One matches this idea (same/near slug, or a title
that reads as the same feature)? Then this is a **resume, not a new feature**: re-read its progress.md,
announce the phase and what's left (ticked tasks, recorded decisions), and re-enter that phase —
research/build/ship all re-enter from progress.md (workflow.md). Never seed a second folder for the same
feature; never overwrite an existing dossier.

## In-flight overlap

**Tell:** the idea is new, but other features are in flight.

Idea is new but other features are in flight: say so in one line (slug + phase each). If their `tasks.md`
files overlap this idea's likely surface, run sequentially — two features editing the same module trades
merge conflicts for wall-clock.

## Done-slug collision

**Tell:** the derived kebab name collides with a **done** feature's.

Slug collides with a **done** feature: the global ordinal already makes the new folder unique (it gets
the next number), so the kebab name may safely repeat across ordinals; only add a `-2` suffix to
disambiguate identical names when scanning. A finished dossier is history, not a scratch folder.

## Roadmap match & dependency stacking

**Tell:** `.wi/roadmap.md` exists and this idea is one of its rows.

If `.wi/roadmap.md` exists and this idea is one of its rows, use the row's slug, mark it `in-progress`,
and carry the row's notes + sequencing rationale into brainstorm as seed context — the WHAT was
part-captured when the roadmap was written, so brainstorm gets shorter, not skipped. Check its
**Depends on**: a dependency that is done-but-unmerged (PR still open) means this feature would build
against code `main` doesn't have — ask once (inside the brainstorm stop, like the preflight): wait for
the merge, **stack** this branch on the dependency's branch (record it in progress.md; retarget the PR
after the dep merges), or proceed off `main` deliberately.
````

- [ ] **Step 2:** Verify verbatim-ness: for each of the six branches, every sentence of the dev original appears in the new file (allowing only bullet-marker strip / reflow / the Roadmap branch's leading "if" capitalized). Diff-assisted eyeball, clause by clause.
- [ ] **Step 3:** `python scripts/validate.py` → 0; file tail intact (ends `deliberately.\n`).
- [ ] **Step 4:** Commit: `feat: feature-folder-cases reference — dev step 2's six branches, verbatim (#39)`.

### Task 3 (#39): Rewrite dev step 2 = common path + classifier

**Files:** Modify `skills/dev/SKILL.md:39-74`.

- [ ] **Step 1:** Replace step 2 (from `2. **Open the feature folder — or resume the one already open.**` through `…so never write a date-only or guessed one.`) with exactly:

```markdown
2. **Open the feature folder — or route the edge case first.** Parse flags: `--auto` sets **Gate mode:
   auto-approve** in progress.md — tell the user the design gate will be auto-approved and recorded, not
   asked. Then **classify the idea before creating anything** — **new / resume / in-flight-overlap /
   done-collision / roadmap-row / legacy-repo** (tells: an in-flight `features/*/progress.md` reading as
   this same idea → resume; others merely in flight → overlap; a done feature with this name →
   done-collision; a matching `.wi/roadmap.md` row → roadmap-row; a pre-rename work-unit folder
   (`goals`, not `features`) → legacy).
   Anything but a plain new feature → follow `${CLAUDE_PLUGIN_ROOT}/references/feature-folder-cases.md`
   for every case whose tell fires, before creating anything. The common path: derive a kebab-case name,
   prefix the **next global 4-digit ordinal** so `<slug>` = `NNNN-<name>` (e.g. `0001-stripe-webhooks`;
   full numbering rule — monotonic, never renumbered — in wi-directory.md's Slugs bullet), create
   `.wi/features/<slug>/`, and seed `progress.md` (template in the research skill's `wi-directory.md`).
   Every Log line — the `**Created**` seed included — opens with a full ISO-8601 timestamp from the OS
   clock (`date -Iseconds`, or `python ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/now.py`); ship computes
   the run's timing from these stamps, so never write a date-only or guessed one.
```

- [ ] **Step 2:** Verify: step 2 is 14 lines (AC ≤15); `grep -c "git mv .wi/goals" skills/dev/SKILL.md` → 0 (branch text gone); steps still number 1–6; dev step 1's "step 2 records it…" sentence untouched; Boundaries untouched.
- [ ] **Step 3:** `python scripts/validate.py` → 0; tail of dev/SKILL.md intact (ends with the "Keep dev thin" line + newline).
- [ ] **Step 4:** Commit: `feat: dev step 2 = common path + classifier routing to feature-folder-cases (#39)`.

### Task 4 (#39): wi-directory xref + rpa legacy pointer

**Files:** Modify `skills/research/references/wi-directory.md:46-50` (Slugs bullet), `skills/rpa/SKILL.md:33-34`.

- [ ] **Step 1:** wi-directory Slugs bullet — append at its end: `Creation-time edge cases (resume, in-flight overlap, done-collision, roadmap rows, legacy migration): ${CLAUDE_PLUGIN_ROOT}/references/feature-folder-cases.md.` (backtick-quote the path).
- [ ] **Step 2:** rpa step 2 — replace `a repo whose work units still live under the pre-rename folder gets a one-time` + `` `git mv .wi/goals .wi/features` before anything else; `` with `a legacy repo (work units under the pre-rename ` + backtick + `goals` + backtick + ` folder) gets the one-time migration in ${CLAUDE_PLUGIN_ROOT}/references/feature-folder-cases.md before anything else;` (path backticked; the `.wi/goals` literal is lint-restricted to lines carrying the migration command — validate.py 7c). This is #39's rpa audit outcome: legacy migration is rpa step 2's only inline edge-case branch (ordinal detail already lives in ingest.md §1); the factoring is mechanical, so it lands in this PR per the triage's pick-up note.
- [ ] **Step 3:** `python scripts/validate.py` → 0; tails intact.
- [ ] **Step 4:** Commit: `feat: wi-directory xref + rpa legacy pointer to feature-folder-cases (#39)`.

### Task 5 (#40): Canonical owners — workflow.md + wi-directory.md

**Files:** Modify `skills/research/references/workflow.md` (add §Script invocation; reshape §Token budget tail), `skills/research/references/wi-directory.md` (name the ledger rule + no-notification clause; absorb 2 ordinal clauses — no-op if #39 text already carries them; trim Log-bullet internal dup).

- [ ] **Step 1:** workflow.md — append at end of file:

```markdown

## Script invocation

Bundled scripts run as `python ${CLAUDE_PLUGIN_ROOT}/…`; where `python` does not resolve, fall back to
`py -3` (Windows) or `python3` (Linux/macOS). Every skill's script call inherits this — skills cite it
as **the python fallback** instead of restating it.
```

- [ ] **Step 2:** workflow.md lines 112–120 (`The cost is also *measured*` … `never estimated.`) — replace with:

```markdown
The cost and the time are also *measured* where they can be — never estimated: `tokens.md` records each
subagent's **exact** usage and `Duration`, ship's `token_report.py` parses the session transcript for
the real orchestrator total and derives the autonomous wall-clock from `progress.md`'s OS-clock Log
stamps, and anything unobservable is written `unavailable`, never a fabricated number. The full
discipline — row timing, stamp format, what ship's finalize fills — is wi-directory.md's `tokens.md`
template section; phase skills cite it as **the ledger rule**.
```

- [ ] **Step 3:** wi-directory.md tokens intro (lines 177–182) — rewrite the first two sentences to name the rule and absorb the no-notification clause: `Append a row the **moment** each subagent's completion notification arrives (**the ledger rule** — phase skills cite it by this name): the token figure exists only in that notification, and a dispatch that returns without one (e.g. a resumed agent) records ` + backtick + `unavailable` + backtick + `, never an estimate. Each row also carries its **Duration**: the notification's elapsed time, or the delta between your dispatch stamp and the notification's arrival (OS clock) — ` + backtick + `unavailable` + backtick + ` when neither exists, never an estimate.` (rest of the paragraph unchanged).
- [ ] **Step 4:** wi-directory.md Slugs bullet — confirm it now covers "a resumed feature keeps its number; a roadmap row's name is numbered when its folder is first created"; if not, add those two clauses after the legacy-features sentence.
- [ ] **Step 5:** wi-directory.md Log bullet (lines 113–117): replace `— ship's ` + "`token_report.py`" + ` derives the run's autonomous wall-clock (research→gate-open + gate-approved→PR, i.e. manual waits and idle time excluded) from exactly these stamps, so` with `— ship's ` + "`token_report.py`" + ` derives the run's autonomous wall-clock from exactly these stamps (spans + exclusions: the ` + "`tokens.md`" + ` section below), so`.
- [ ] **Step 6:** `python scripts/validate.py` → 0; tails intact.
- [ ] **Step 7:** Commit: `feat: canonical owners — ledger rule named in wi-directory, python-fallback house rule in workflow.md (#40)`.

### Task 6 (#40): Pointer sweep — research, build, ship

**Files:** Modify `skills/research/SKILL.md`, `skills/build/SKILL.md`, `skills/ship/SKILL.md`.

- [ ] **Step 1 (research, R1):** principles bullet "Delegate, summarize, discard" — replace from `append each one's token count as a row` through `if the ledger was skipped.` with: `append each one's ` + "`tokens.md`" + ` row the moment its completion notification arrives — the figure exists only there — per wi-directory.md's **ledger rule** (exact tokens + ` + "`Duration`" + `, ` + "`unavailable`" + ` when unobservable, never an estimate). ship finalizes the totals and a ` + "`check_tokens.py`" + ` gate blocks the PR if the ledger was skipped.`
- [ ] **Step 2 (research, R5):** §0 — replace `(` + "`python`" + ` assumed on PATH; where it does not resolve, fall back to ` + "`py -3`" + ` on Windows or ` + "`python3`" + ` on Linux/macOS)` with `(python fallback: workflow.md)`.
- [ ] **Step 3 (research, R1):** §2 — replace `each round appends its own ` + "`tokens.md`" + ` row — a re-check round that returns without a completion notification records ` + "`unavailable`" + `, never an estimate` with `each round appends its own ` + "`tokens.md`" + ` row per wi-directory.md's ledger rule`.
- [ ] **Step 4 (research, R2):** principles — `**Autonomous until the gate.**` → `**Autonomous until the gate** (workflow.md's no-questions rule).`
- [ ] **Step 5 (research, R6):** §4 — replace `print the ready-made keep-alive again (the user is present — they just approved) for the current platform: Claude Code & Codex CLI arm their built-in ` + "`/goal`" + ` with the PR-open condition; Copilot CLI relaunches under Autopilot. The exact command templates — and the unattended-run warning that must accompany the Copilot one — live in ` + "`${CLAUDE_PLUGIN_ROOT}/references/keep-alive.md`" + `; print them from there verbatim.` with `print the ready-made keep-alive again (the user is present — they just approved), **verbatim from ` + "`${CLAUDE_PLUGIN_ROOT}/references/keep-alive.md`" + `** — the single source of the platform templates (` + "`/goal`" + ` on Claude Code & Codex, the Autopilot relaunch + unattended-run warning on Copilot).`
- [ ] **Step 6 (build, R3):** §2.3 — replace the passage from `**Frontend routing is operational, not just asserted:**` through `is a defect ship's checker flags.)` with:

```markdown
**Frontend routing is operational, not just asserted** (integrations.md §Frontend work — delegation is
   mandatory when the skill is installed): a task tagged `[frontend]` MUST have its dispatch name the
   available design skill, the runner builds the UI *through it* and reports `frontend via
   frontend-design` (or `frontend via wi fallback (frontend-design absent)`), and you log that line to
   `progress.md` when the report returns (runners never write `progress.md`). Still verify behavior.
   (Ship's checker flags `[frontend]` UI built blind while the skill was installed.)
```

- [ ] **Step 7 (build, R1+R5):** §2.4 — replace from `Append the runner's token count as a row to` through `never an estimate.` with: `Append the runner's ` + "`tokens.md`" + ` row the moment its completion notification arrives — the figure exists only there; file somehow absent → ` + "`python ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/check_tokens.py --init .wi/features/<slug>/tokens.md`" + ` first (python fallback: workflow.md) — per wi-directory.md's **ledger rule** (exact tokens + ` + "`Duration`" + `, ` + "`unavailable`" + ` when unobservable, never an estimate).`
- [ ] **Step 8 (ship, R5):** §3 — replace `(` + "`python`" + ` assumed on PATH; where it does not resolve, fall back to ` + "`py -3`" + ` on Windows or ` + "`python3`" + ` on Linux/macOS — this holds for every script in this SKILL.)` with `(python fallback: workflow.md §Script invocation — holds for every script in this SKILL.)`
- [ ] **Step 9 (ship, R1):** §6.3 — replace `On a parse failure it writes ` + "`Orchestrator: unavailable for this run`" + ` (never a substitute, estimate, or fabricated figure); a missing stamp likewise yields ` + "`unavailable`" + ` timing, not a guess.` with `On a parse failure or a missing stamp it writes the honest ` + "`unavailable`" + ` (wi-directory.md's ledger rule — never a substitute, estimate, or fabricated figure).`
- [ ] **Step 10:** `python scripts/validate.py` → 0; `pytest tests/` green; tails intact ×3.
- [ ] **Step 11:** Commit: `refactor: research+build+ship cite the canonical rules (#40)`.

### Task 7 (#40): Pointer sweep — dev, rpa

**Files:** Modify `skills/dev/SKILL.md`, `skills/rpa/SKILL.md`.

- [ ] **Step 1 (dev, R7):** step 1 — replace from `**Model routing first-run setup**` through `Never re-ask an existing config.` with: `**Model routing first-run setup** (` + "`${CLAUDE_PLUGIN_ROOT}/references/models.md`" + ` §First-run setup): ` + "`.wi/models.md`" + ` absent → ask once and write+commit per that section (` + "`--auto`" + ` → the **simple** preset, logged as an assumption); present → apply it silently, warning once if the session model is below the configured orchestrator tier; a pre-1.3 legacy config → rename per that section. Never re-ask an existing config.` (the resolve-once tail of step 1 stays verbatim).
- [ ] **Step 2 (dev, R6):** §4 — replace `then print the keep-alive handoff for the current platform: Claude Code & Codex CLI arm their built-in ` + "`/goal`" + ` with the PR-open condition; Copilot CLI relaunches under Autopilot. The exact command templates — and the unattended-run warning that must accompany the Copilot one — live in ` + "`${CLAUDE_PLUGIN_ROOT}/references/keep-alive.md`" + `; print them from there verbatim.` with `then print the keep-alive handoff for the current platform **verbatim from ` + "`${CLAUDE_PLUGIN_ROOT}/references/keep-alive.md`" + `** — the single source of the platform templates (` + "`/goal`" + ` on Claude Code & Codex, the Autopilot relaunch + unattended-run warning on Copilot).`
- [ ] **Step 3 (dev, R6):** §4 armed-tail — replace `Armed, the run continues across turns until the condition holds (wi works without it, just less robustly through a stalled turn). The per-platform mechanism is in` with `Armed, the run continues across turns until the condition holds (keep-alive.md). The per-platform mechanism is in`.
- [ ] **Step 4 (dev, R2):** §6 — `**No questions anywhere in this stretch**;` → `**No questions anywhere in this stretch** (workflow.md's no-questions rule);`
- [ ] **Step 5 (dev, R9):** Boundaries — replace `**Superpowers precedence:** during a run, superpowers skills fire only at wi's delegation points (` + "`${CLAUDE_PLUGIN_ROOT}/skills/research/references/integrations.md`" + `) — never self-triggered mid-phase; wi's artifact formats always win.` with `**Superpowers precedence** (integrations.md §Who initiates — ` + "`${CLAUDE_PLUGIN_ROOT}/skills/research/references/integrations.md`" + `): delegation points only, never self-triggered mid-phase; wi's artifact formats always win.`
- [ ] **Step 6 (rpa, R7):** step 2 — replace from `Run the **model routing first-run setup** here too` through `the section format is unchanged.` with: `Run the **model routing first-run setup** here too (` + "`${CLAUDE_PLUGIN_ROOT}/references/models.md`" + ` §First-run setup): absent → one preset question (` + "`--auto`" + ` → simple, logged); present → apply, warn once on an orchestrator-tier mismatch; a pre-1.3 legacy config → rename per that section. Never re-ask.`
- [ ] **Step 7 (rpa, R1+R5):** §5 — replace from `— the checker is a subagent and its exact token count exists **only in its completion notification**;` through `never an estimate.` with `(python fallback: workflow.md) — the checker is a subagent: append its ` + "`tokens.md`" + ` row the moment its completion notification arrives, per wi-directory.md's **ledger rule** (a round returning without a notification records ` + "`unavailable`" + `, never an estimate — mirrors the dev flow's research-start scaffold; step 6's scaffold-if-absent remains the fallback). Each checker round appends its own row.` — keeping the sentence's surviving tail (`Then, before rendering the gate, …`) intact.
- [ ] **Step 8 (rpa, R5):** §6 — replace `` ` — `python` assumed on PATH; where it does not resolve, fall back to `py -3` on Windows or `python3` on Linux/macOS)`` with ` — python fallback: workflow.md)`.
- [ ] **Step 9 (rpa, R9):** tail — replace `**Superpowers precedence:** during a run, superpowers skills fire only at wi's delegation points (` + "`${CLAUDE_PLUGIN_ROOT}/skills/research/references/integrations.md`" + `) — never self-triggered mid-phase; wi's artifact formats always win.` with `**Superpowers precedence** (integrations.md §Who initiates — ` + "`${CLAUDE_PLUGIN_ROOT}/skills/research/references/integrations.md`" + `): delegation points only, never self-triggered mid-phase; wi's artifact formats always win.`
- [ ] **Step 10:** `python scripts/validate.py` → 0; tails intact ×2.
- [ ] **Step 11:** Commit: `refactor: dev+rpa cite the canonical rules (#40)`.

### Task 8 (#40): task-runner frontend pointer; ordinal single home; script comments

**Files:** Modify `agents/wi-task-runner.md:56-65`, `references/feature-folder-cases.md` (§Ordinal), `skills/rpa/references/ingest.md` (§1), `skills/rpa/references/build-uipath.md` (§2.4 python note), `references/models.md` (diff-review §2 python note), `skills/ship/scripts/_ledger.py` + `check_tokens.py` + `token_report.py` (one comment line each).

- [ ] **Step 1 (task-runner, R3):** replace the frontend bullet (from `- **Frontend tasks route to the design skill — never build UI blind.**` through `falling back.)`) with:

```markdown
- **Frontend tasks route to the design skill — never build UI blind** (the canonical rule:
  `skills/research/references/integrations.md` §Frontend work). Task tagged `[frontend]` + a design skill
  available (your dispatch normally names it; if it didn't, check your skills list) → you **MUST**
  build/refine the markup *through it*, and state `frontend via frontend-design` (or `via <skill>`) in
  your report — the orchestrator logs it to `progress.md`. No design skill installed → author markup by
  hand and report `frontend via wi fallback (frontend-design absent)`. Either way you still write the
  behavioral test and make **Verify** pass.
```

  Nothing else in the charter changes — report format, caps, markers, tools untouched.
- [ ] **Step 2 (feature-folder-cases, R8):** replace §Ordinal's body paragraph with: `Derive a kebab-case name, then prefix the **next global 4-digit ordinal** so ` + "`<slug>`" + ` = ` + "`NNNN-<name>`" + ` (e.g. ` + "`0001-stripe-webhooks`" + `) — the full numbering rule (mirroring ` + "`ADR-NNNN`" + `: global, monotonic, assigned **once at creation, never renumbered**; next = highest existing ordinal + 1, else ` + "`0001`" + `) is wi-directory.md's **Slugs bullet**. Case notes: legacy unnumbered features are left as-is and ignored by the next-number scan; a resumed feature keeps its number; a roadmap row's name is numbered when its folder is first created.`
- [ ] **Step 3 (ingest, R8):** §1 — replace `, mirroring ` + "`ADR-NNNN`" + `: global across ` + "`.wi/features/`" + `, monotonic, assigned once at creation, never renumbered. Next = highest existing ` + "`.wi/features/`" + ` ordinal + 1 (else ` + "`0001`" + `); legacy unnumbered runs are left as-is.` with ` — wi-directory.md's **Slugs rule** (monotonic, assigned once at creation, never renumbered; legacy unnumbered runs ignored by the next-number scan).`
- [ ] **Step 4 (build-uipath, R5):** §2.4 — replace `` ` — `python` assumed on PATH; where it does not resolve, fall back to `py -3` on Windows or `python3` on Linux/macOS)`` with ` — python fallback: ` + "`skills/research/references/workflow.md`" + `)`.
- [ ] **Step 5 (models.md, R5):** diff-review step 2 — replace `(` + "`python`" + ` assumed on PATH; where it does not resolve, fall back to ` + "`py -3`" + ` on Windows or ` + "`python3`" + ` on Linux/macOS)` with `(python fallback: ` + "`skills/research/references/workflow.md`" + ` §Script invocation)`.
- [ ] **Step 6 (scripts, R1):** add one comment line near the top docstring of each of `_ledger.py`, `check_tokens.py`, `token_report.py`: `Canonical prose for the ledger discipline: skills/research/references/wi-directory.md (tokens.md template).` — comments only, zero behavior.
- [ ] **Step 7:** `python scripts/validate.py` → 0; `pytest tests/` green; tails intact.
- [ ] **Step 8:** Commit: `refactor: task-runner frontend pointer; ordinal + python-fallback single homes; script xrefs (#40)`.

### Task 9: Grep assertions (the #40 AC's "no full restatement outside its owner")

- [ ] **Step 1:** Within `skills/ agents/ references/` (docs/ + README are out of scope — not loaded at run time):
  - `grep -rn "py -3" skills agents references` → only `workflow.md` (+ nothing else).
  - `grep -rn "never an estimate" skills agents references` → only `wi-directory.md` (its two canonical statements).
  - `grep -rn "carrying the same" skills agents references` → only `models.md` (legacy-config mechanics).
  - `grep -rn "unattended-run warning" skills agents references` → `keep-alive.md` + at most the two one-line pointers (dev §4, research §4).
  - `grep -rn "git mv .wi/goals" skills agents references` → only `feature-folder-cases.md`.
  - `grep -rn "never renumbered" skills agents references` → `wi-directory.md` + the two pointer parentheticals (dev step 2, feature-folder-cases §Ordinal).
  - `grep -rn "impeccable" skills agents references` → only `integrations.md`.
- [ ] **Step 2:** Fix any stray full restatement the greps surface; re-run until clean.

### Task 10: Dry-runs (six branch types) + load-alone checks

- [ ] **Step 1:** Dispatch six parallel subagents (read-only). Each gets: the worktree path, instructions to Read the NEW `skills/dev/SKILL.md` step 2 + `references/feature-folder-cases.md`, one fixture description, and must answer: (a) which case(s) it classifies, (b) the exact actions it takes, in order. Fixtures:
  1. *new:* empty `.wi/features/`, no roadmap, no `.wi/goals` → expect: no reference load; ordinal `0001`; create + seed.
  2. *resume:* `features/0003-csv-export/progress.md` Phase `build`, idea "finish the CSV export" → expect: resume — re-read progress, announce phase + remaining tasks, re-enter build; no new folder.
  3. *in-flight overlap:* `features/0002-auth/progress.md` Phase `research`, new idea "add avatars"; auth tasks touch different files → expect: one-line in-flight note; proceed (parallel ok), new ordinal `0003`.
  4. *done-collision:* `features/0001-stripe-webhooks/` Phase `done`, idea "redo stripe webhooks" → expect: new folder `0002-stripe-webhooks` (name may repeat), never touch the done dossier.
  5. *roadmap-row:* `roadmap.md` row 2 "avatars | 0004-avatars | planned | depends on 1", row 1 done-but-PR-open → expect: use row slug, mark in-progress, carry notes into brainstorm, ask once about the unmerged dep (wait / stack / proceed).
  6. *legacy:* `.wi/goals/` exists with two dossiers → expect: `git mv .wi/goals .wi/features` + commit first, dossiers untouched, then normal path.
- [ ] **Step 2:** Compare each answer against the expected behavior (derived from the pre-move text at `627f655`). Any divergence → fix skill/reference wording, re-run that fixture.
- [ ] **Step 3:** Load-alone checks — one subagent per heavily-trimmed file (build, research, rpa, dev, wi-task-runner), each Reading only that file and answering that file's deduped decisions, e.g.: build — "a runner's notification never arrived; what goes in the tokens.md row?" (expect: `unavailable`, never an estimate — reachable via the ledger-rule pointer); task-runner — "your task is `[frontend]`, dispatch didn't name a skill" (expect: check own skills list; report the exact `frontend via …` line); dev — "`python` doesn't resolve on this box" (expect: follow the python-fallback pointer → workflow.md). Every answer must be correct or reach the correct rule via a named pointer.
- [ ] **Step 4:** Record dry-run + load-alone results (1 line each) for the PR body.

### Task 11: Version bump

- [ ] **Step 1:** `.claude-plugin/plugin.json` `"version": "1.7.0"` → `"1.7.1"`; `.claude-plugin/marketplace.json` plugin entry `"version": "1.7.0"` → `"1.7.1"` (top-level `0.1.0` untouched). Check `.codex-plugin/plugin.json` — if it carries a version field, bump it the same way (follow what PR #45 did).
- [ ] **Step 2:** `python scripts/validate.py` → 0; `pytest tests/` green.
- [ ] **Step 3:** Commit: `chore: bump to v1.7.1 (PR C — #39 #40)`.

### Task 12: Review + PR

- [ ] **Step 1:** Full-diff review pass (fresh eyes / code-review) over `main...prc-39-40` for: lost clauses (against the rules-map), broken cross-references, truncated tails.
- [ ] **Step 2:** Push branch; open PR titled `PR C: relocate dev step 2 branches + dedup restated rules (#39 #40) (v1.7.1)`; body = summary, the rules-map table, #39's six-branch inventory result, dry-run + load-alone results, grep-assertion results, `Closes #39, Closes #40`. **No AI attribution.**
- [ ] **Step 3:** Watch PR checks green (`gh pr checks --watch`).

## Out of scope (recorded for #41/#42)

- Dossier-lifecycle prose consolidation (research §3 / build §1 / rpa §5 / build-uipath §1 / ship §6 / wi-directory internal) — #41.
- Ship §8 report-side honesty wording; integrations.md ship-row log strings — #41 (ship pass).
- Resolve-once trigger phrasing at the five dispatch sites — deliberate #38 placement, stays.
