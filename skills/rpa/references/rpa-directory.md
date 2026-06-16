---
type: Reference
title: The `.wi/` layout for RPA
description: The RPA tier of the .wi/ knowledge store (project → run → process) and its OKF frontmatter.
timestamp: 2026-06-14
tags: [rpa, wi-directory, okf, conventions]
---

# The `.wi/` layout for RPA

`wi:rpa` reuses the `.wi/` model — same [OKF](/docs/specs/2026-06-14-okf-knowledge-format.md) frontmatter
profile — with an extra tier: **project → run (a PDD/solution) → process**. One `/wi:rpa` run is one goal
folder for the whole solution, with **one SDD** covering its 1..N processes.

```
.wi/
├── rpa-constitution.md      # project: RPA house standards (REFramework, connectors-over-UI, naming, gate)
├── sdd-template.md          # project (OPTIONAL): a client/house SDD ToC override — used if present
├── inputs.md                # project: input/asset registry (API refs, CSVs, samples) — see ingest.md
├── components.md            # project: reusable components registry — reuse before build
├── orchestrator.md          # project: Orchestrator resource manifest (link, agents, queues, assets, buckets, processes, triggers)
├── glossary.md              # project: domain terms
├── learnings.md             # project: learnings INDEX — one line + hook per run; read this, not the dir
├── learnings/               # project: substantial learnings, each its own .md (indexed above)
└── goals/
    └── 0001-<run-slug>/     # one /wi:rpa run = one PDD -> solution; NNNN- global ordinal (creation order)
        ├── progress.md      # state machine for the run (single source of truth)
        ├── pdd.md           # the ingested PDD (faithful to source .docx)
        ├── architecture.md  # the whole-solution Runtime diagram (SDD §2): dispatcher + all performers
        ├── sdd.md           # ONE Solution Design Document (§7.1.x repeated per process)
        ├── process-inventory.md   # the N processes + dependencies
        ├── assumptions.md   # gap/assumption register (per-process sections) + PDD->SDD trace
        ├── tasks.md         # the multi-process build DAG (components -> processes -> sub-workflows)
        ├── verification.md  # checker output (plan mode pre-gate, result mode at ship) — EPHEMERAL; verdict folds into PR.md
        ├── tokens.md        # token ledger
        ├── PR.md            # PR description
        └── processes/
            └── <process>/
                └── tobe.md  # refined TO-BE (from the PDD's ToBe) + the per-process flow diagram (SDD §7.1.3)
```

## Conventions

- **Run-slugs are numbered** — `NNNN-<name>` (a global 4-digit ordinal assigned at creation, mirroring
  `ADR-NNNN`; next = highest existing `.wi/goals/` ordinal + 1, else `0001`, never renumbered), so runs
  list in implementation order. Same convention as the dev flow (`wi-directory.md`).
- **Project-level files persist & compound** across runs: `rpa-constitution.md`, `sdd-template.md` (if
  present), `inputs.md`, `components.md`, `orchestrator.md`, `glossary.md`, `learnings.md`, `learnings/`. Never pruned. Build + compound write
  back (especially new reusable components → `components.md`).
- **The SDD structure is overridable** (clients differ): an existing project `sdd.md`'s ToC wins; else
  `.wi/sdd-template.md`; else the bundled base ToC (see `references/sdd-template.md`).
- **`architecture.md` is the whole-solution Runtime diagram** — dispatcher + every performer (2nd/3rd) +
  queues + systems + Orchestrator. Per-process flow diagrams live in each `tobe.md` (and feed SDD §7.1.3).
- **`orchestrator.md` is the resource manifest** — the concrete Orchestrator names (folder, processes,
  queues, assets, buckets, agents, triggers) elicited in brainstorm; SDD §1.3/§3.1/§7.2–7.6 are filled from
  it, and the back-half build provisions from it. Secret/credential **names** only, never values.
- **Faithful `pdd.md`.** Don't edit it to "fix" the process — refinement lives in `tobe.md`.
- ADRs for hard-to-reverse choices (REFramework vs coded, dispatcher split, queue model) go in the
  project-wide `.wi/adr/` log, same as `wi:dev`.

## OKF frontmatter (RPA types)

Same profile as `wi:dev` (see [wi-directory](/skills/research/references/wi-directory.md) and the
[OKF spec](/docs/specs/2026-06-14-okf-knowledge-format.md)); the RPA-specific `type` values are:
`rpa-constitution.md` → `RPA Constitution`, `inputs.md` → `Input Registry`, `components.md` →
`Component Registry`, `orchestrator.md` → `Orchestrator Manifest`; per run: `progress.md` →
`RPA Run Progress`, `pdd.md` → `PDD`, `architecture.md` → `Architecture`, `sdd.md` → `SDD`,
`process-inventory.md` → `Process Inventory`, `assumptions.md` → `Assumption Register`, `tasks.md` →
`Task List`, `verification.md` → `Verification` *(ephemeral — checker output, pruned at close-out)*,
`tokens.md` → `Token Ledger`, `PR.md` → `PR Description`; per process:
`processes/<p>/tobe.md` → `TO-BE`. `orchestrator.md` SHOULD carry a `resource:` pointing at the
Orchestrator folder URL (names only, never secret values).

For a **rename/rebrand** run, the researcher's **Runtime State Inventory** (the five-category sweep) maps
onto the existing RPA registries rather than a new file: Orchestrator **queue/asset/process names** and
**in-flight queue items** → `orchestrator.md` (live config + stored data), credential **names** →
`orchestrator.md` (names only, per the rpa-constitution), the **published package name** → a build
artifact. Each load-bearing row still becomes its own migration task in `tasks.md`.

## Frontmatter stubs (the prose-generated run files)

`progress.md` has its full template below; `sdd.md`, `orchestrator.md`, `inputs.md`, `components.md`, and
`rpa-constitution.md` carry templates in their reference docs. The remaining run files are written from
prose — open each with its OKF frontmatter, then the body:

```markdown
---
type: PDD
title: <solution / process name> — PDD
description: The ingested Process Definition Document, faithful to the source.
goal: <run-slug>
timestamp: <YYYY-MM-DD>
---
```

```markdown
---
type: Architecture
title: Runtime diagram — <solution name>
description: Whole-solution runtime diagram — dispatcher, every performer, queues, systems, Orchestrator.
goal: <run-slug>
timestamp: <YYYY-MM-DD>
---
```

```markdown
---
type: Process Inventory
title: Process inventory — <solution name>
description: The N processes in this solution and their dependencies.
goal: <run-slug>
timestamp: <YYYY-MM-DD>
---
```

```markdown
---
type: Assumption Register
title: Assumptions — <solution name>
description: Gap/assumption register (per-process) plus the PDD->SDD traceability.
goal: <run-slug>
timestamp: <YYYY-MM-DD>
---
```

```markdown
---
type: TO-BE
title: <process name> — TO-BE
description: The refined TO-BE flow for this process (feeds SDD §7.1.3).
goal: <run-slug>
timestamp: <YYYY-MM-DD>
---
```

`tasks.md` uses the same `type: Task List` frontmatter as `wi:dev` (see the plan skill's `tasks.md` format).

## `progress.md` template (run-level)

```markdown
---
type: RPA Run Progress
title: <PDD / solution name>
description: <what this solution automates, one line>
goal: <run-slug>
status: ingest   # bootstrap | ingest | brainstorm | plan | design-gate | build | ship | done
timestamp: <YYYY-MM-DD>
---

# RPA run: <PDD / solution name>

- **Slug:** <run-slug>
- **PDD:** <source .docx path>
- **Created:** <YYYY-MM-DD>
- **Phase:** ingest   <!-- bootstrap | ingest | brainstorm | plan | design-gate | build | ship | done -->
- **Gate mode:** interactive   <!-- interactive | auto-approve (/wi:rpa --auto) -->
- **Build paradigm:** xaml-only   <!-- xaml-only (pure activities, NO Invoke Code) | coded-allowed (.cs) — user-approved at the design gate -->
- **Publish:** none   <!-- none | feed (publish package to tenant feed) | deploy (feed + deploy/activate to a folder) — approved at the design gate; prod folder needs explicit approval -->
- **SDD ToC source:** base | project sdd.md | .wi/sdd-template.md
- **Worktree:** <path or ->   **Branch:** <branch or ->

## Processes
- [ ] <process A>   (transaction: <unit>; shape: dispatcher+performer | performer)
- [ ] <process B>

## Log
- <date> bootstrap: markitdown present; uipath plugin installed; discovery delegated
- <date> brainstorm via superpowers:brainstorming   <!-- or: via wi fallback -->
- ...

## Decisions / assumptions / blockers
- <approach, ADR links, sign-off items>
```
