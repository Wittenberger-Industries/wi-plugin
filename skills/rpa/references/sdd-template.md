---
type: Template
title: SDD template
description: Base ToC + precedence rules for an OKF-conformant Solution Design Document (.wi/goals/<run>/sdd.md).
timestamp: 2026-06-14
tags: [sdd, template, okf, rpa]
---

# SDD template

The Solution Design Document is the high-fidelity spec handed to `uipath-rpa-workflows` — the "robust
prompt" meant to one-shot the build. **One SDD per solution**, with §7 repeated per process. Pull from
`tobe.md`, `.wi/inputs.md`, `.wi/components.md`, the rpa-constitution, and the assumptions. Reference,
don't duplicate. Fill §1.3, §3.1 and §7.2–7.6 from `.wi/orchestrator.md` (the resource manifest elicited in
the brainstorm) — concrete names, not placeholders.

## Choosing the structure (ToC) — precedence

Clients have different SDD standards, so the structure is **overridable**. Pick the ToC in this order:

1. **An existing SDD in the project wins.** If the repo already has an `sdd.md` (or a delivered SDD doc)
   with a Table of Contents, **mirror that ToC** — match the client's house standard, don't impose ours.
2. **A project override.** Else, if `.wi/sdd-template.md` exists (a per-project ToC) or the
   `rpa-constitution.md` names an SDD structure, use it.
3. **The base ToC below** otherwise.

Whichever you use, fill every section from the design; if a section can't be filled, that's a brainstorm
gap to resolve, not a TODO to leave.

**The ToC is framework-aware** (`progress.md` → `Framework:`). The base ToC below is the **REFramework**
shape. On the **Maestro** path, reshape these sections: **§2** becomes the **flow diagram** (from
`maestro-architecture.md`); **§3.1** the Maestro project/flow layout (the `.flow` files, not REFramework);
**§7.1.x** the flow's **nodes** (each node's type — connector / approval / script / subflow / agent / ixp —
its inputs/outputs, and the connection/agent it uses), **not** a transaction + queue-item schema; **§7.2–7.6**
become Maestro **connections, triggers, and agent registrations** — Orchestrator **queues** and `Config.xlsx`
do not apply. §7.1.3 stays the per-process flow diagram for both.

## Base ToC (UiPath enterprise standard)

Copy to `.wi/goals/<run>/sdd.md` (or the client's structure):

```markdown
---
type: SDD
title: Solution Design Document — <solution / project name>
description: <the solution this SDD specifies, one line>
goal: <run-slug>
timestamp: <YYYY-MM-DD>
---

# Solution Design Document — <solution / project name>

## 1. Introduction
### 1.1 Purpose of the document
### 1.2 Infrastructure requirements for development
<dev machines, Studio version, licenses, access>
### 1.3 Infrastructure requirements for production
<robots/runtimes, machine type (unattended), Orchestrator tenant/folder, network/firewall>

## 2. Runtime diagram
<the WHOLE-SOLUTION architecture: Dispatcher + every Performer (2nd/3rd if present) + queues + systems
 + Orchestrator. Embed architecture.md's mermaid here. This is the detailed solution view, not one process.>

## 3. Automation details
### 3.1 Solution Package
<package name(s), REFramework, project layout, naming, source control location>

## 4. Data Service Details
<UiPath Data Service entities/fields if used, or "not used">

## 5. Libraries used
<reusable Library projects / shared components (from .wi/components.md) + activity packages & versions>

## 6. Applications Used
<each application/system the automation touches, version, environment, and how (UI / API / connector)>
### 6.1 Postman collections for Applications automated through APIs
<for API-automated apps: the Postman collection / endpoint list (ref .wi/inputs.md API references)>

## 7. Process details
### 7.1 <Process name>            <!-- repeat 7.1.x for each process in the solution -->
#### 7.1.1 Process (development) details
<the refined TO-BE: trigger, transaction definition + queue-item schema, step-by-step logic,
 business vs system exceptions, retries. Link tobe.md.>
#### 7.1.2 Production details
<schedule/trigger, SLA, volumes, robot allocation, environment specifics>
#### 7.1.3 Process Diagram
<this process's TO-BE flow diagram (mermaid) — the per-process zoom-in>
### 7.2 Orchestrator Storage Buckets
<buckets + purpose, or "none">
### 7.3 Orchestrator Queues
<queue name(s), item schema, SLA/retry, references>
### 7.4 Orchestrator Assets
<asset names, type, scope (global/per-folder), what they hold — never the secret value>
### 7.5 Orchestrator Triggers
<time/queue triggers, schedule>
#### 7.5.1 Other settings for triggers
<concurrency, execution target, runtime arguments>
### 7.6 Agents
<any UiPath Agent a process calls (e.g. a document-extraction agent): name, where it runs, its input and
 output schema (ref the sample in .wi/inputs.md), and how the Performer invokes/awaits it — or "none">

## 8. Other remarks
<assumptions, open questions, risks, manual fallbacks, anything for sign-off — link assumptions.md
 + the PDD->SDD traceability>

## 9. UiPath Apps Details
<any UiPath Apps front-ends, or "none">
```

A good SDD lets a fresh builder (the UiPath skill or a human) implement the solution without re-reading the
PDD. §2 is the whole-solution architecture; §7.1.3 is per-process flow.
