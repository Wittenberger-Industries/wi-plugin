---
type: Reference
title: "Ingest — parse the PDD, register inputs & components"
description: "Before any design, capture the *whole* input surface."
timestamp: 2026-06-08
tags: [rpa, reference]
---

# Ingest — parse the PDD, register inputs & components

Before any design, capture the *whole* input surface. The build can only use what you register here, so
this step is what makes the later UiPath handoff complete.

## 1. Derive the run-slug, then convert the PDD → `pdd.md`

- **Derive `<run-slug>` first** — it's the feature-folder name used everywhere below: a kebab name from the
  PDD/solution, **prefixed with the next global 4-digit ordinal** (`NNNN-<name>`, e.g. `0001-invoices`),
  mirroring `ADR-NNNN`: global across `.wi/features/`, monotonic, assigned once at creation, never renumbered.
  Next = highest existing `.wi/features/` ordinal + 1 (else `0001`); legacy unnumbered runs are left as-is.
- If the PDD is `.docx`/`.pdf`/`.pptx`: `markitdown <pdd> -o .wi/features/<run-slug>/pdd.md`.
- If it's already `.md`: copy/reference it as `pdd.md` as-is (don't re-process).
- **Prepend OKF frontmatter** so `pdd.md` is a typed concept like the rest of the bundle: open the file
  with `type: PDD` (+ `title`, `description`, `feature: <run-slug>`, `timestamp` — stub in `rpa-directory.md`)
  above the converted body. The frontmatter is metadata; the body stays faithful to the source.
- Keep `pdd.md` faithful to the source — it is the record of *what the business actually wrote*. Refinement
  happens later in `tobe.md`, not by editing `pdd.md`.
- **Check for dropped images.** markitdown can't render embedded diagrams — they become empty
  `![](data:image/...)`. Grep the output for `](data:`; if any, flag how many and which sections. A dropped
  *AS-IS* diagram is usually fine; a dropped *To-Be / architecture / matrix* diagram is not — re-run
  markitdown with LLM image description, or ask the user to export those diagrams as files.

## 2. Register supporting inputs → `.wi/inputs.md` (project-level)

PDDs travel with annexes the automation needs: API references, data dictionaries, CSV/Excel mapping
tables, sample inputs, screenshots, business-rule sheets, credential lists (names only). Catalog every
one — the build and the UiPath handoff reference this registry.

```markdown
---
type: Input Registry
title: Inputs registry — <project>
description: Registry of inputs/assets (API refs, CSVs, samples) the build and UiPath handoff reference.
timestamp: <YYYY-MM-DD>
---

# Inputs registry — <project>

| File | Type | Purpose | Used by |
|------|------|---------|---------|
| docs/SystemX_API.pdf | API reference | endpoints/auth for SystemX | connector/HTTP steps |
| data/vendor_mapping.csv | mapping table | maps vendor codes -> GL accounts | Process transaction |
| samples/invoice_email.eml | sample input | example trigger payload | tobe + tests |
```

Large/binary annexes are referenced by path, not inlined. If an annex is a `.docx`/`.xlsx` whose *content*
the design needs, markitdown it into a sibling `.md` and note that.

- **Large data files (CSV/XLSX — many rows / >~1 MB):** register them, sample **header + row count only**
  (`head -1` + `wc -l`), and **never read them into context.** Note the delimiter and encoding. The SDD
  and build must treat them as a **lookup/index** (DB, dictionary, or filtered read), not load-into-memory.
- **Referenced-but-missing inputs:** scan `pdd.md` for links and 'see <file>' references; if a referenced
  doc (mapping xlsx, template, API spec) isn't in the drop, surface it as a gap/assumption — don't silently
  assume it. (It may turn out to be already distilled into another input, e.g. a template file.)

## 3. Detect reusable components → `.wi/components.md` (project-level)

A project is 1..N processes; do **not** rebuild what already exists. Scan the repo (and the
discovery-agent output) for reusable workflows / UiPath **Library** projects / shared sub-workflows, and
register them with their interface so later processes invoke instead of recreate.

```markdown
---
type: Component Registry
title: Components registry — <project>
description: Reusable components registry — build reads it first (reuse) and registers new ones.
timestamp: <YYYY-MM-DD>
---

# Components registry — <project>

| Component | Kind | Purpose | Interface (in -> out) | Location |
|-----------|------|---------|-----------------------|----------|
| SendNotification | workflow | standard email/Teams notify | (to, subject, body) -> () | Shared/SendNotification.xaml |
| LoginSystemX | workflow | authenticate to SystemX | (config) -> (session) | Shared/LoginSystemX.xaml |
| Common.Activities | Library (.nupkg) | org-wide helpers | (various) | feed/Common.Activities |
```

This registry is **project-level and persists across runs** — build reads it first (reuse), and registers
any new reusable component it creates. That is how the second process in a project starts ahead of the
first.

## Output

`pdd.md` (per run), and the project-level `inputs.md` + `components.md` created/updated. Report a 3-5 line
summary: PDD pages/sections found, N supporting inputs registered, M reusable components found.
