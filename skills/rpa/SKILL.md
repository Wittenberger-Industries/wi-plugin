---
type: Skill
name: rpa
description: >
  Turn a UiPath PDD into a built RPA solution (REFramework or Maestro). Use this skill when the user
  types "/wit:rpa", points at a PDD/SDD/.docx, or says "build a UiPath workflow/automation from this PDD",
  "build a Maestro flow from this PDD", "automate <process>", "follow PDD.docx". One run handles a
  multi-process PDD. Add "--auto" for a hands-off run.
---

# /wit:rpa "<pdd path | describe the process>": PDD → SDD → built RPA solution (REFramework or Maestro)

wit owns the method, the gate, and the artifacts; **`uipath-rpa` owns the build**, XAML or coded (the
delegated-skill slugs live in the table in `uipath-bootstrap.md`). Borrow, don't reinvent.

Defaults (set in the rpa-constitution, overridable): **REFramework**; build paradigm **approved at the
design gate (XAML-only default, or coded)**; build to an **open PR**; gate =
**Workflow Analyzer clean + `uip` validate**; **prefer Integration Service connectors/APIs over UI** where
one exists (UI is a fine answer when it doesn't).

Same two interactions as `wit:dev`: the **brainstorm** (here, the deep TO-BE refinement) and the
**design gate** (sign off the SDD + assumptions). `--auto` collapses everything after brainstorm.

Design rationale for this skill lives in the wit repo's `docs/design-notes/rpa.md` (maintainer doc,
never loaded at runtime).

## Procedure

1. **Bootstrap the prerequisites.** Follow `${CLAUDE_PLUGIN_ROOT}/skills/rpa/references/uipath-bootstrap.md`:
   ensure **markitdown**, the **UiPath skills** plugin, and the **.NET 8 runtime** are installed (offer to
   install if absent), and on an existing UiPath repo delegate structure discovery to UiPath's
   `uipath-project-discovery-agent`.
2. **Register inputs & components, ingest the PDD.** Follow
   `${CLAUDE_PLUGIN_ROOT}/skills/rpa/references/ingest.md`: derive the **numbered run-slug**
   (`NNNN-<name>`, the next global 4-digit ordinal; ingest:1); catalog the repo's supporting files into
   `.wit/inputs.md`; detect reusable components into `.wit/components.md`; convert the PDD to `pdd.md` with
   markitdown (skip if it's already Markdown). Run the **model routing first-run setup** here too
   (`${CLAUDE_PLUGIN_ROOT}/references/models.md` "First-run setup"), then resolve the routing once per
   that reference and record the `## Model routing (resolved)` block when the run's `progress.md` is
   seeded (rpa-directory.md's template); every build delegation reads the block's `rpa-build` cell (a
   routing role label, resolved per models.md), and at ship the cross-provider diff review layers on top
   of wit-code-checker's result-mode pass, per `wit:ship`. The project-level `.wit/`
   outputs of rpa:1–3 (`inputs.md`,
   `components.md`, `orchestrator.md`, `models.md`, a first-run `rpa-constitution.md`) are **committed
   where written** (`chore(wit): …`, the project-level rule in `wit-directory.md`).
3. **Brainstorm: refine the TO-BE (the one conversation).** Follow
   `${CLAUDE_PLUGIN_ROOT}/skills/rpa/references/brainstorm-protocol.md`: take the PDD's **existing ToBe as
   the baseline**, refine it (gaps, missing/redundant steps, branches, exceptions), clarify each open step
   as UI activity / API / connector **inline** (no bias: UI is valid), decompose the PDD into its **1..N
   processes**, **propose the framework** (`reframework` | `maestro`) from the process shape (heuristic in
   `brainstorm-protocol.md` / the constitution) and record it in `progress.md` (`Framework:`), for each
   define the transaction + dispatcher/performer shape (REFramework) **or** the flow's node shape
   (Maestro), and **elicit the Orchestrator provisioning** (protocol:6) into `.wit/orchestrator.md`.
   **Stamp the brainstorm mode** in `progress.md`, engine + interactivity
   (`brainstorm via superpowers:brainstorming` | `via wit fallback`, suffixed
   `, dialogue` | `, self-answered (headless)`; brainstorm-protocol.md). Log every gap you fill as an
   assumption. Parse `--auto` here (Gate mode).
4. **Plan: write the artifacts** (layout + OKF frontmatter stubs:
   `${CLAUDE_PLUGIN_ROOT}/skills/rpa/references/rpa-directory.md`; each file opens with its `type`):
   - **`architecture.md`**: framework-aware, validated with
     `${CLAUDE_PLUGIN_ROOT}/skills/scan/scripts/check_mermaid.py`: **REFramework** → the Runtime diagram
     (`references/refr-architecture.md`); **Maestro** → the flow diagram
     (`references/maestro-architecture.md`).
   - **`sdd.md`**: one Solution Design Document. **Choose the ToC** per the precedence in
     `references/sdd-template.md` (an existing project SDD's ToC wins → `.wit/sdd-template.md` → the
     bundled base ToC) and **shape it to the `Framework`** (REFramework vs Maestro sections, per that
     template). sdd:7.1.x repeats per process; sdd:7.1.3 is each process's flow diagram (kept in its
     `tobe.md`); sdd:1.3/sdd:3.1/sdd:7.2–7.6 are filled from `.wit/orchestrator.md`.
   - per process: **`tobe.md`** (refined from the PDD's ToBe + its flow diagram); `assumptions.md` and
     `process-inventory.md` at run level.
   - **`tasks.md`** = the multi-process build DAG: shared components first, then processes, then each
     process's independent sub-workflows, parallel where the DAG allows. Include the **dev-verification
     strategy** decided in brainstorm (protocol:5) when the tenant link is an open dep: defer the
     queue-dependent runtime checks with that dep, or the named local substitute as its own task.
   - **ADR(s)**: the hard-to-reverse choices this run locked (framework `reframework` | `maestro`, the
     dispatcher/performer split, the queue model) each go to the project-wide `.wit/adr/` log as the next
     `ADR-NNNN` + its index row, committed where written (`docs(wit): ADR-NNNN <title>`; rpa-directory.md's
     rule, same as the dev flow); the gate's **Approach (ADR-NNNN)** line cites it. Nothing hard to
     reverse → no ADR (plan:2's rule: don't manufacture decisions).
5. **Design gate.** **Pre-gate check (checker · plan mode):** first scaffold the token ledger (idempotent):
   `python ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/check_tokens.py --init .wit/features/<run-slug>/tokens.md`
   (python fallback: workflow.md "Script invocation"). The checker is a subagent: append its `tokens.md`
   row the moment its completion notification arrives, per wit-directory.md's **ledger rule** (exact
   tokens + `Duration`; `unavailable` when unobservable, never an estimate); each checker round appends
   its own row; rpa:6's scaffold-if-absent remains the fallback. Then, before rendering the gate,
   dispatch the **checker** (`${CLAUDE_PLUGIN_ROOT}/agents/wit-code-checker.md`) in `plan` mode over
   `sdd.md` (its acceptance-criteria section, sdd:10 in the base ToC, plus locked decisions), `tasks.md`,
   `assumptions.md`, `orchestrator.md`, `rpa-constitution.md`, and any Runtime State Inventory rows; it
   builds a feature-backward coverage matrix and returns BLOCKER/WARNING/INFO, writing `verification.md`.
   A BLOCKER (an uncovered SDD criterion, a silently down-scoped decision, an unresolved open dep) loops
   back to plan, then the checker re-checks (**max 2 rounds**); whatever remains is carried into the gate
   summary with its severity.

   **Commit the run's dossier on main now**, `docs(<run-slug>): feature dossier (design gate)`: everything
   under `.wit/features/<run-slug>/`, the run folder as it stands. On a **mid-build reopen** skip this main
   commit; the worktree branch already carries the amendments and merges them back.

   Render the SDD summary + architecture + the assumptions register **and the open dependencies `D1..Dn`**
   inline (use the same gate format as `wit:research`, including its **Leaner path** and
   **Checker (plan mode)** lines, mapped to the RPA artifacts; the footer's "Full detail: …" line notes
   the artifacts are committed on main as of this gate); the user must **resolve or knowingly defer each
   open dep**, no silent "later". If the gate is **re-opened mid-build** (amend path), the worktree copy
   is canonical: read and render from the worktree's `.wit/features/<run-slug>/`, and say in the summary
   which copy you rendered from. Confirm: approve / amend / stop. **First confirm the framework**
   (`reframework` | `maestro`, proposed in brainstorm, recorded in `progress.md` as `Framework:`), then
   **have the user approve the build paradigm: XAML-only (pure activities, default) or coded `.cs`**, a
   HARD binary (**no Invoke-Code middle ground**); the build paradigm applies only when
   `Framework: reframework`, recorded in `progress.md` (`Build paradigm:`). **Also approve the publish
   decision**, `Publish: none | feed | deploy` (+ target folder for `deploy`): `none` = build to PR only;
   `feed` = pack + publish the package(s) to the connected tenant's feed; `deploy` = `feed` +
   deploy/activate as a Process in that folder; a **prod** folder must be explicitly approved here (never
   auto-selected), recorded in `progress.md` (`Publish:`). `--auto` records and proceeds on the defaults:
   framework **as proposed at brainstorm** and recorded in `progress.md` (`Framework:`); paradigm
   XAML-only; publish per the constitution, default `none`. On approval, **harvest the design-phase
   learnings** into `.wit/learnings/<run-slug>.md` (+ its line in the `.wit/learnings.md` index):
   non-obvious decisions, gap resolutions, and domain rules surfaced in the brainstorm, marked
   *candidate (pre-build)*; ship later confirms these against the build and promotes the general ones to
   `.wit/rpa-constitution.md` / `.wit/glossary.md`.
6. **Build.** Create the worktree
   (`${CLAUDE_PLUGIN_ROOT}/skills/build/references/worktrees-and-subagents.md`;
   `superpowers:using-git-worktrees` if installed), **framework-neutral**, the same first step as
   `wit:build`. The worktree already contains `.wit/features/<run-slug>/` (committed on main at the design
   gate; the branch starts from main). **Reuse components from `.wit/components.md` before building new**,
   and build per the **`Framework`**: **REFramework** →
   `${CLAUDE_PLUGIN_ROOT}/skills/rpa/references/build-uipath.md`, delegating to `uipath-rpa`;
   **Maestro** → `${CLAUDE_PLUGIN_ROOT}/skills/rpa/references/build-maestro.md`, delegating to
   `uipath-maestro-flow`. **On the REFramework path,** delegate **low-code XAML REFramework** generation
   to `uipath-rpa` per process/sub-workflow in **parallel waves** (state the **approved paradigm** in the
   prompt: XAML-only → pure drag-drop activities, **no Invoke Code and no `.cs`**; coded-allowed → `.cs`
   workflows ok; scaffold each unit as REFramework per the SDD, never Blank), append each unit's tokens
   to `tokens.md` (scaffold it first if absent:
   `python ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/check_tokens.py --init .wit/features/<run-slug>/tokens.md`;
   python fallback: workflow.md "Script invocation"), and register any new reusable component back into
   `.wit/components.md`.
7. **Verify & ship.** Gate = `${CLAUDE_PLUGIN_ROOT}/skills/rpa/references/verification-gate.md`, **branched
   on `Framework`**: REFramework → approved paradigm + Workflow Analyzer + `uip` validate; Maestro →
   `uip maestro flow validate` (+ `eval` if eval sets exist). Both → `tokens.md` passes `check_tokens.py`
   + the **checker · result mode**, one dispatch: the feature-level pass over the SDD's
   acceptance-criteria section plus the inline line-level review (verification-gate.md). Then reuse the
   **ship** skill (`wit:ship`) for the docs-sync, PR (`PR.md` committed, then `gh pr create --body-file`),
   close-out checklist (including the remote-checks gate: ship:8 verifies the PR's remote checks before
   any cleanup), **compound/learnings** (confirm + promote the candidate `.wit/learnings/<run-slug>.md`
   written at the gate; update its `.wit/learnings.md` index line), and the **token report** (`tokens.md`,
   finalized before the dossier commit, mandatory).
   **Publish to the tenant (if approved), after the PR is open and its remote-checks gate has landed**
   (green or none configured; never while checks are pending or red). If `progress.md` `Publish: ≠ none`
   and `uip` is authenticated to the `orchestrator.md` tenant, delegate to **`uipath-solution`**: `pack` +
   `publish` the package(s) to the feed, and for `deploy` also `deploy` + `activate` as a Process in the
   gate-approved folder. **Not connected** → skip, and record in `progress.md` that publish was approved
   but no tenant is connected (recovery: `uip cloud login`); not a failure, the PR shipped. **On error** →
   record the exact recovery `uip` command in `progress.md` and report; never fail the run over publish.
   A **prod** target needs the gate's explicit approval, and publish is **post-gate**: it never runs on a
   red build. Record the published package name + version (+ folder) into `orchestrator.md` and the final
   report.
   **Ship is dev-shaped; map its artifacts to the RPA ones:** gate → the RPA verification gate above;
   `spec.md` (acceptance criteria, review) → **`sdd.md`** (acceptance + sdd:7 process details);
   `pitfalls.md` → the **`assumptions.md`** register; `brief.md` → **`pdd.md`**; `repo-map.md` → n/a. The
   dev dossier tidy becomes the **RPA dossier** (the run manifest in rpa-directory.md); `orchestrator.md`
   is project-level (updated in place, never swept). One PR per run by default (per-process PRs are an
   option for large solutions).

## What carries over from the wit spine

The design gate, isolated worktrees, **parallel build waves**, the ship PR + **docs-sync** (architecture
diagrams kept current), **compound/learnings**, the **token report**, `check_mermaid.py`, and
plugin-bootstrap all work unchanged. So does the **compact-reasoning rule**
(`${CLAUDE_PLUGIN_ROOT}/references/compact-reasoning.md`): essential, decision-bearing thoughts only
across ingest, scheduling, and delegation; the SDD decomposition and the design gate keep full depth (the
note's carve-outs).

**Superpowers precedence** (integrations.md "Who initiates",
`${CLAUDE_PLUGIN_ROOT}/skills/research/references/integrations.md`): delegation points only, never
self-triggered mid-phase; wit's artifact formats always win.
