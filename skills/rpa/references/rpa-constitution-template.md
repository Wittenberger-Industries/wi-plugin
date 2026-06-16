---
type: Template
title: "RPA constitution — template"
description: "Copy to `.wi/rpa-constitution.md`, fill in from what bootstrap/discovery found, and confirm the lines marked `(confirm)`."
timestamp: 2026-06-08
tags: [rpa, reference]
---

# RPA constitution — template

Copy to `.wi/rpa-constitution.md`, fill in from what bootstrap/discovery found, and confirm the lines
marked `(confirm)`. Every phase reads this. It is the cheapest place to encode "how we build automations
here." Keep it short and declarative.

```markdown
---
type: RPA Constitution
title: RPA constitution — <project>
description: RPA house standards (REFramework, connectors-over-UI, naming, gate).
timestamp: <YYYY-MM-DD>
---

# RPA constitution — <project>

## Framework & approach
- **Framework (default `reframework`):** **`reframework`** (state machine, queue-based) or **`maestro`** (a
  UiPath Maestro flow — orchestration of connector/approval/script/subflow/agent/ixp nodes, built via
  `uipath-maestro-flow`). The design gate confirms it each run; `--auto` uses this default. Maestro suits
  approvals/HITL + connectors + agents + long-running work; REFramework suits high-volume queue batches.   (confirm)
- **Maestro specifics (when `maestro`):** prefer Integration Service **connectors** over script nodes; make
  **approval/HITL** points explicit; no `Config.xlsx`/queues (connections + Orchestrator assets by name); if
  eval sets exist, the gate runs `uip maestro flow eval`.
- **Build paradigm (HARD — two options, no middle ground):** **XAML-only** = every step a real drag-drop
  activity, with **NO Invoke Code activity (no VB/C# code blocks) and no `.cs` / `.codedworkflows`** — none,
  ever. **coded-allowed** = `.cs` coded workflows. There is **no Invoke-Code 'hybrid'** in either. The **design
  gate asks the user to approve** which, each run (default **XAML-only**); the build honors it, the gate
  enforces it.   (confirm)
- **Expressions are fine — that's not "code".** Under XAML-only, activities use **full VB expressions**
  normally (Assign, If, conditions, BuildDataTable, …). The ban is *only* the **Invoke Code** activity (a block
  of procedural VB/C#) — not the expressions every activity already uses.
- **Prefer Integration Service connectors / APIs over UI** where one exists — for maintainability
  (selectors break, APIs are stable). **UI automation is valid** when there's no API or the interaction is
  inherently UI; flag UI steps in the SDD as higher-maintenance.   (confirm)
- **Publish (default `none`):** after a green build + PR, wi can publish to a connected Orchestrator tenant
  — `none` (no push, default), `feed` (publish the package to the tenant feed), or `deploy` (`feed` +
  deploy/activate as a Process in a folder). The design gate confirms it each run; `--auto` uses this
  default. **No production-folder deploy without explicit approval at the gate.**   (confirm)

## Naming & structure
- Workflows: PascalCase, descriptive (GetTransactionData, Process). Annotation on every workflow.
- Arguments: `in_/out_/io_` prefixes; variables camelCase, meaningful.
- **Prefer a Multiple Assign over a chain of single Assign activities** — group related assignments into
  one block; it reads far cleaner than a vertical stack of separate Assigns.
- Standard REFramework folders (Framework/, Data/, Tests/). **Process sub-workflows live under `Process/`,
  grouped into subfolders by system/concern** (`Process/DocuWare/`, `Process/MasterData/`, `Process/IDoc/`, …),
  each holding that area's workflows — not flat at the project root.
- **Orchestrator resources** named `<Solution>_<Process>_<Queue|Asset|Bucket>`, recorded in
  `.wi/orchestrator.md`; assets/credentials referenced by **name** only.

## Configuration & secrets
- All settings/assets in `Config.xlsx` (Settings/Constants/Assets). Secrets are Orchestrator
  assets/credentials referenced by name — **never hardcoded**.

## Exceptions & logging
- Business rejects → `BusinessRuleException` (no retry; route to exception queue / notify).
- System errors → retry per Config (default 3); screenshot on error.
- Log Message at each major step + Add Log Fields (transaction id, ...); business → Warn, system → Error.

## Locale & data formats
- Source files may not be UTF-8 (German data is often **latin-1 / Windows-1252**) and CSVs may be
  `;`-delimited — read with the correct encoding/culture, don't assume UTF-8/comma.
- German number format = comma decimal (`119,00`); dates often `DD.MM.YYYY`. Target systems (e.g. SAP IDoc)
  usually need dot decimals and `YYYYMMDD` — make these **transforms explicit** in the SDD, not implicit.

## Transactions & Orchestrator
- Default to **queue-based** transactions when work is a batch of independent items; dispatcher/performer
  when items must be collected first.
- Orchestrator: queues for transactions, assets for config, folders per environment (dev/test/prod).

## Reuse
- Check `.wi/components.md` before building any capability; reuse shared workflows / Library projects.
  Register new reusable components after building them.

## Simplicity  (build the least that works)
- Before building a workflow/component, ask whether it needs to exist — reuse `.wi/components.md` or a
  Library first; a speculative handler the PDD never asked for = skip it, note it in one line. (YAGNI)
- Reach in order: an existing component → an Integration Service **connector / API** → a standard activity →
  a small VB expression → only then a new sub-workflow (a coded `.cs` only if the gate approved coded).
- Fewest workflows that deliver the SDD. No abstraction for a single caller (no generic wrapper with one
  user, no Config asset for a value that never changes). Prefer deleting a step to adding one.
- Lazy, not negligent: never simplify away REFramework exception handling, retries, transaction logging, or
  credential-by-name — those are load-bearing.
- Mark a deliberate shortcut with an annotation naming its ceiling (e.g. "stub: folder-drop mock; real SAP
  query when D3 resolves").

## Gate (definition of done)
- Output matches the **gate-approved paradigm** — always REFramework XAML; `.cs` / `.codedworkflows` only if the user approved **coded-allowed**.
- `uip` restore + validate succeed; **Workflow Analyzer: zero error-level violations**.   (confirm)
- `tokens.md` (token ledger) passes `check_tokens.py` — rows + filled sum + resolved Orchestrator.
- Every SDD acceptance criterion verified; every assumption confirmed or logged for sign-off.

## Out of scope by default
- <e.g. no production Orchestrator changes without approval; no UI automation of Citrix without CV>
```

## Defaults wi:rpa assumes when a rule is blank

REFramework; connectors/APIs preferred over UI (but UI is fine where needed); secrets as Orchestrator
assets; business vs system exceptions with 3 retries; Workflow Analyzer error-clean as the gate; reuse
before build; **build the least that works** (YAGNI, connectors/components over new code, mark shortcuts). An opinionated baseline beats no opinion — the constitution is where a project overrides it.
