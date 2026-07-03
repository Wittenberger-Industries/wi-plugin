---
type: Skill
name: rpa
description: >
  Turn a UiPath PDD into a built RPA solution — REFramework or Maestro. Use this skill when the user
  types "/wi:rpa", points at a PDD/SDD/.docx, or says "build a UiPath workflow/automation from this PDD",
  "build a Maestro flow from this PDD", "automate <process>", "follow PDD.docx". One run handles a
  multi-process PDD. Add "--auto" for a hands-off run.
---

# /wi:rpa "<pdd path | describe the process>" — PDD → SDD → built RPA solution (REFramework or Maestro)

`wi:rpa` is the rigorous **front half** of an RPA build: it does the thinking (ingest → TO-BE → SDD) and
hands a high-fidelity spec to UiPath's own skills for the build. wi owns the method, the gate, and the
artifacts; **`uipath-rpa` owns the build** (XAML or coded — the delegated-skill slugs live in the table in
`uipath-bootstrap.md`) — borrow, don't reinvent.

Defaults (set in the rpa-constitution, overridable): **REFramework**, build paradigm **approved at the design
gate (XAML-only default, or coded)**, build to an **open PR**, gate =
**Workflow Analyzer clean + `uip` validate**, **prefer Integration Service connectors/APIs over UI** where
one exists (UI is a fine answer when it doesn't).

It has the same two interactions as `wi:dev`: the **brainstorm** (here, the deep TO-BE refinement) and the
**design gate** (sign off the SDD + assumptions). `--auto` collapses everything after brainstorm.

## Procedure

1. **Bootstrap the prerequisites.** Follow `${CLAUDE_PLUGIN_ROOT}/skills/rpa/references/uipath-bootstrap.md`:
   ensure **markitdown**, the **UiPath skills** plugin, and the **.NET 8 runtime** (the `uip` CLI + build need
   it) are installed (offer to install if absent), and on an existing UiPath repo delegate structure discovery
   to UiPath's `uipath-project-discovery-agent`.
2. **Register inputs & components, ingest the PDD.** Follow
   `${CLAUDE_PLUGIN_ROOT}/skills/rpa/references/ingest.md`: a repo whose work units still live under the
   pre-rename folder gets a one-time `git mv .wi/goals .wi/features` before anything else; then derive the **numbered run-slug**
   (`NNNN-<name>` — the next global 4-digit ordinal, mirroring `ADR-NNNN`; see ingest.md §1); catalog the
   supporting files in the repo (API refs, CSV/mapping tables, sample data, screenshots) into
   `.wi/inputs.md`; detect reusable components into `.wi/components.md`; convert the PDD to `pdd.md` with
   markitdown (skip if it's already Markdown). Run the **MoA first-run setup** here too
   (`${CLAUDE_PLUGIN_ROOT}/references/moa.md`): `.wi/moa.md` absent → one preset question (`--auto` →
   simple preset, logged); present → apply, warn once on an orchestrator-tier mismatch. The config's
   `wi-task-runner` tier then rides every build delegation (agent `rpa-build`), and at ship the
   cross-provider diff review layers on top of wi-code-checker's result-mode pass, per the same rules as
   `wi:ship`. The project-level `.wi/` outputs of steps 1–3 (`inputs.md`, `components.md`,
   `orchestrator.md`, `moa.md`, a first-run `rpa-constitution.md`) are **committed where written**
   (`chore(wi): …` — the project-level rule in `wi-directory.md`), so the post-gate worktree carries them.
3. **Brainstorm — refine the TO-BE (the one conversation).** Follow
   `${CLAUDE_PLUGIN_ROOT}/skills/rpa/references/brainstorm-protocol.md`: take the PDD's **existing ToBe as
   the baseline**, refine it (gaps, missing/redundant steps, branches, exceptions), clarify each open step
   as UI activity / API / connector **inline** (no bias — UI is valid), decompose the PDD into its **1..N
   processes**, **propose the framework** (`reframework` | `maestro`) from the process shape (heuristic in
   `brainstorm-protocol.md` / the constitution) and record it in `progress.md` (`Framework:`), and for each
   define the transaction + dispatcher/performer shape (REFramework) **or** the flow's node shape (Maestro),
   and **elicit the Orchestrator
   provisioning** (org/tenant/folder link, UiPath Agent name(s), and the queue / asset / storage-bucket /
   published-process names) into `.wi/orchestrator.md`. **Stamp the brainstorm mode** in `progress.md`
   (`brainstorm via superpowers:brainstorming` | `via wi fallback`). Log every gap you fill as an assumption.
   Parse `--auto` here (Gate mode).
4. **Plan — write the artifacts** (layout + OKF frontmatter stubs:
   `${CLAUDE_PLUGIN_ROOT}/skills/rpa/references/rpa-directory.md` — each file opens with its `type`):
   - **`architecture.md`** — framework-aware, validated with
     `${CLAUDE_PLUGIN_ROOT}/skills/scan/scripts/check_mermaid.py`: **REFramework** → the Runtime diagram
     (Dispatcher + every Performer + queues + systems + Orchestrator; see `references/refr-architecture.md`);
     **Maestro** → the flow diagram (trigger + nodes + systems/agents; see `references/maestro-architecture.md`).
   - **`sdd.md`** — one Solution Design Document. **Choose the ToC** per the precedence in
     `references/sdd-template.md` (an existing project SDD's ToC wins → `.wi/sdd-template.md` → the bundled
     base ToC) — and **shape it to the `Framework`** (REFramework vs Maestro sections, per that template).
     §7.1.x repeats per process; §7.1.3 is each process's flow diagram (kept in its `tobe.md`);
     §1.3/§3.1/§7.2–7.6 are filled from `.wi/orchestrator.md` (the elicited resource names).
   - per process: **`tobe.md`** (refined from the PDD's ToBe + its flow diagram); `assumptions.md` and
     `process-inventory.md` at run level.
   - **`tasks.md`** = the multi-process build DAG: shared components first, then processes, then each
     process's independent sub-workflows — parallel where the DAG allows.
5. **Design gate.** **Pre-gate check (checker · plan mode):** before rendering the gate, dispatch the
   **checker** (`${CLAUDE_PLUGIN_ROOT}/agents/wi-code-checker.md`) in `plan` mode over `sdd.md` (its
   acceptance-criteria section — §10 in the base ToC — plus locked decisions), `tasks.md`, `assumptions.md`,
   `orchestrator.md`, `rpa-constitution.md`, and any
   Runtime State Inventory rows — it builds a feature-backward coverage matrix and returns BLOCKER/WARNING/INFO,
   writing `verification.md`. A BLOCKER (an uncovered SDD criterion, a silently down-scoped decision, an
   unresolved open dep) loops back to plan, then the checker re-checks (**max 2 rounds**); whatever remains is
   carried into the gate summary with its severity.

   Render the SDD summary + architecture + the assumptions register **and the open
   dependencies `D1..Dn`** inline (use the same gate format as `wi:research` — including its **Leaner path** and **Checker (plan mode)** lines, mapped to the RPA artifacts); the user must **resolve or
   knowingly defer each open dep** — no silent "later". Confirm: approve / amend / stop — **and have the user approve the build
   paradigm: XAML-only (pure activities, default) or coded `.cs`** (a HARD binary — **no Invoke-Code middle
   ground**) — **first confirm the framework** (`reframework` | `maestro`, proposed in brainstorm, recorded
   in `progress.md` as `Framework:`); the **build paradigm applies only when `Framework: reframework`**,
   recorded in `progress.md` (`Build paradigm:`). **Also approve the publish decision** —
   `Publish: none | feed | deploy` (+ target folder for `deploy`): `none` = build to PR only; `feed` =
   pack + publish the package(s) to the connected tenant's feed; `deploy` = `feed` + deploy/activate as a
   Process in that folder; a **prod** folder must be explicitly approved here (never auto-selected),
   recorded in `progress.md` (`Publish:`). `--auto` records and proceeds on the constitution defaults
   (paradigm XAML-only; publish per the constitution, default `none`). On
   approval, **harvest the design-phase learnings** into `.wi/learnings/<run-slug>.md` (+ its line in the
   `.wi/learnings.md` index) — non-obvious decisions,
   gap resolutions, and domain rules surfaced in the brainstorm, marked *candidate (pre-build)*. wi:rpa's
   front and back halves often run in **different environments**, so without a gate-time harvest a
   front-half-only run leaves no compounded knowledge; ship later confirms these against the build and
   promotes the general ones to `.wi/rpa-constitution.md` / `.wi/glossary.md`.
6. **Build.** Create the worktree
   (`${CLAUDE_PLUGIN_ROOT}/skills/build/references/worktrees-and-subagents.md`;
   `superpowers:using-git-worktrees` if installed) and — the same first step as `wi:build`,
   **framework-neutral** — move `.wi/features/<run-slug>/` into it and commit it as the branch's first
   commit (`chore(<run-slug>): feature dossier`); skip the move if it's already there (resume). Then
   **reuse components from `.wi/components.md` before building new**, and build per the **`Framework`**:
   **REFramework** → `${CLAUDE_PLUGIN_ROOT}/skills/rpa/references/build-uipath.md`,
   delegating to `uipath-rpa`; **Maestro** → `${CLAUDE_PLUGIN_ROOT}/skills/rpa/references/build-maestro.md`,
   delegating to `uipath-maestro-flow`. **On the REFramework path,** delegate **low-code XAML REFramework**
   generation to `uipath-rpa` per process/sub-workflow in **parallel waves** (state the paradigm in
   the prompt — the **approved paradigm**: XAML-only → pure drag-drop activities, **no Invoke Code and no `.cs`**;
   coded-allowed → `.cs` workflows ok; scaffold each unit as REFramework per the SDD, never Blank),
   append each unit's tokens to `tokens.md` (scaffold it first if absent:
   `python ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/check_tokens.py --init .wi/features/<run-slug>/tokens.md` —
   `python` assumed on PATH; where it does not resolve, fall back to `py -3` on Windows or `python3` on
   Linux/macOS), and register any new reusable component back into `.wi/components.md`.
7. **Verify & ship.** Gate = `${CLAUDE_PLUGIN_ROOT}/skills/rpa/references/verification-gate.md`, **branched on
   `Framework`**: REFramework → approved paradigm + Workflow Analyzer + `uip` validate; Maestro →
   `uip maestro flow validate` (+ `eval` if eval sets exist). Both → `tokens.md` passes `check_tokens.py`
   + the **feature-level checker · result mode** over the SDD's acceptance-criteria section. Then reuse the **ship**
   skill (`wi:ship`) for the docs-sync, PR (`PR.md` committed, then `gh pr create --body-file`), close-out
   checklist, **compound/learnings** (confirm + promote the candidate `.wi/learnings/<run-slug>.md` written at
   the gate; update its `.wi/learnings.md` index line), and the **token report (`tokens.md` — finalized
   before the dossier commit, mandatory)**.
   **Publish to the tenant (if approved) — after the PR is open.** If `progress.md` `Publish: ≠ none` and
   `uip` is authenticated to the `orchestrator.md` tenant, delegate to **`uipath-solution`**: `pack` +
   `publish` the package(s) to the feed, and for `deploy` also `deploy` + `activate` as a Process in the
   gate-approved folder. **Not connected** → skip, and record in `progress.md` that publish was approved
   but no tenant is connected (recovery: `uip cloud login`) — not a failure; the PR shipped. **On error** →
   record the exact recovery `uip` command in `progress.md` and report; never fail the run over publish. A
   **prod** target needs the gate's explicit approval, and publish is **post-gate** — it never runs on a
   red build. Record the published package name + version (+ folder) into `orchestrator.md` and the final
   report.
   **Ship is dev-shaped — map its artifacts to the RPA ones:** gate → the RPA verification gate above;
   `spec.md` (acceptance criteria, review) → **`sdd.md`** (acceptance + §7 process details); `pitfalls.md` →
   the **`assumptions.md`** register; `brief.md` → **`pdd.md`**; `repo-map.md` → n/a. The dev dossier
   tidy becomes the **RPA dossier** (rpa-directory.md's run manifest): `progress.md`, `pdd.md`, `sdd.md`,
   `architecture.md`, `assumptions.md`, `process-inventory.md`, per-process `tobe.md`, `tasks.md`,
   `tokens.md`, `PR.md` — `orchestrator.md` is project-level (updated in place, never swept). One PR
   per run by default (per-process PRs are an option for large solutions).

## What carries over from the wi spine

The design gate, isolated worktrees, **parallel build waves**, the ship PR + **docs-sync** (architecture
diagrams kept current), **compound/learnings**, the **token report**, `check_mermaid.py`, and
plugin-bootstrap all work unchanged — `wi:rpa` swaps the *domain* (UiPath/SDD/PDD) into the same machine.
