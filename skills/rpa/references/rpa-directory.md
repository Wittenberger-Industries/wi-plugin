# The `.wi/` layout for RPA

`wi:rpa` reuses the `.wi/` model with an extra tier: **project → run (a PDD/solution) → process**. One
`/wi:rpa` run is one goal folder for the whole solution, with **one SDD** covering its 1..N processes.

```
.wi/
├── rpa-constitution.md      # project: RPA house standards (REFramework, connectors-over-UI, naming, gate)
├── sdd-template.md          # project (OPTIONAL): a client/house SDD ToC override — used if present
├── inputs.md                # project: input/asset registry (API refs, CSVs, samples) — see ingest.md
├── components.md            # project: reusable components registry — reuse before build
├── orchestrator.md          # project: Orchestrator resource manifest (link, agents, queues, assets, buckets, processes, triggers)
├── glossary.md              # project: domain terms
├── learnings/               # project: compounded non-obvious knowledge
└── goals/
    └── <run-slug>/          # one /wi:rpa run = one PDD -> solution
        ├── progress.md      # state machine for the run (single source of truth)
        ├── pdd.md           # the ingested PDD (faithful to source .docx)
        ├── architecture.md  # the whole-solution Runtime diagram (SDD §2): dispatcher + all performers
        ├── sdd.md           # ONE Solution Design Document (§7.1.x repeated per process)
        ├── process-inventory.md   # the N processes + dependencies
        ├── assumptions.md   # gap/assumption register (per-process sections) + PDD->SDD trace
        ├── tasks.md         # the multi-process build DAG (components -> processes -> sub-workflows)
        ├── tokens.md        # token ledger
        ├── PR.md            # PR description
        └── processes/
            └── <process>/
                └── tobe.md  # refined TO-BE (from the PDD's ToBe) + the per-process flow diagram (SDD §7.1.3)
```

## Conventions

- **Project-level files persist & compound** across runs: `rpa-constitution.md`, `sdd-template.md` (if
  present), `inputs.md`, `components.md`, `orchestrator.md`, `glossary.md`, `learnings/`. Never pruned. Build + compound write
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

## `progress.md` template (run-level)

```markdown
# RPA run: <PDD / solution name>

- **Slug:** <run-slug>
- **PDD:** <source .docx path>
- **Created:** <YYYY-MM-DD>
- **Phase:** ingest   <!-- bootstrap | ingest | brainstorm | plan | design-gate | build | ship | done -->
- **Gate mode:** interactive   <!-- interactive | auto-approve (/wi:rpa --auto) -->
- **Build paradigm:** xaml-only   <!-- xaml-only (pure activities, NO Invoke Code) | coded-allowed (.cs) — user-approved at the design gate -->
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
