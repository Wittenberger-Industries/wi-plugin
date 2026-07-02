---
type: Reference
title: "Build — delegate XAML generation to the UiPath skills"
description: "Build runs after the design gate."
timestamp: 2026-06-08
tags: [rpa, reference]
---

# Build — delegate XAML generation to the UiPath skills

Used when **`Framework: reframework`** (the Maestro path is `build-maestro.md`).

Build runs after the design gate. wi does **not** write XAML — it orchestrates `uipath-rpa-workflows`
(the REFramework generator) with the SDD as the spec, in parallel waves, reusing components. Same
discipline as `wi:build`: isolate in a worktree, delegate, summarize, commit small.

Precondition: the design gate passed (SDD + assumptions confirmed, or `--auto`), recorded in
`progress.md`. First act: append `rpa build engaged (wi <version>)` to the log.

## 1. Isolate

Create the worktree + branch (`wi/<run-slug>`) exactly as `wi:build` does
(`${CLAUDE_PLUGIN_ROOT}/skills/build/references/worktrees-and-subagents.md`; use
`superpowers:using-git-worktrees` if installed). Record path + branch.

## 2. Execute the build DAG in waves (from `tasks.md`)

The DAG is: **shared components → per-process scaffolds → sub-workflows → wire-up**. Run it as wide as the
DAG allows (independent processes and independent sub-workflows in parallel):

1. **Reuse first.** Before generating anything, check `.wi/components.md`. If a needed capability already
   exists (a shared workflow or Library), **invoke/reference it** — do not regenerate. Reuse is logged.
2. **Delegate generation — low-code XAML REFramework, explicitly.** For each new workflow/process, hand
   `uipath-rpa-workflows` the relevant SDD section + `tobe.md` + the input refs (`.wi/inputs.md`) + the
   constitution rules. **State the output paradigm in every delegation prompt** (the UiPath skill may default
   to coded otherwise): a **low-code XAML REFramework** project — `project.json` on the **REFramework
   template**, `Main.xaml` (state machine), `Framework/` (`InitAllSettings`, `GetTransactionData`, `Process`,
   `SetTransactionStatus`, …) and `Process.xaml` as **`.xaml`** files, `Data/Config.xlsx`. **Honor the build paradigm the user
   approved at the design gate** (`progress.md` → `Build paradigm:`): **XAML-only** → every step is a real
   drag-drop XAML **activity** — **no `.cs` / `.codedworkflows` AND no Invoke Code activity** (no procedural VB/C#
   code blocks, ever; **HARD rule, no middle ground**). Normal **VB expressions** in Assign / If / conditions /
   BuildDataTable etc. are expected and fine — the ban is only the *Invoke Code activity*. State this explicitly to `uipath-rpa-workflows`. If a
   step genuinely can't be built from activities, that's the signal to pick the **coded** paradigm at the gate
   — never to smuggle code into an Invoke Code. **coded-allowed** → a REFramework project with coded `.cs`
   workflows is fine. Any `.cs` **or any Invoke Code** when the user approved **XAML-only** is **wrong and
   fails the gate**. **Scaffold each unit with the framework the SDD names — REFramework by default, never a
   Blank project.** **Lay the process's sub-workflows out under a `Process/` folder, organized into subfolders
   by system/concern** (`Process/DocuWare/`, `Process/MasterData/`, `Process/IDoc/`, …), each holding that
   area's `.xaml`/`.cs` — not flat at the project root (the REFramework `Framework/` stages stay where they
   are). Dispatch independent units in parallel (one delegation each).

   **House rules — restate each in every delegation prompt** (the generator won't infer them; the
   verification gate's house-rules sweep checks each):
   - **Email approach:** any unit that sends mail/notifications uses **only the gate-confirmed approach**
     (recorded in the SDD / assumptions at the gate — IMAP/SMTP, desktop Outlook, Microsoft 365, Exchange,
     or an IS connector). Name it in the prompt; the generator must not substitute another email tech, and
     if none was confirmed the send is a **mock** (open dep), not a silently chosen framework.
   - **Explicit activity names:** every activity — containers included — gets a DisplayName that says what
     the step does in process terms; no activity ships with its default name ("Assign", "If", "Sequence",
     "Log Message", …).
   - **Multiple Assign for grouped assignments:** assignments that happen together go in **one Multiple
     Assign** activity; a lone assignment stays a single Assign. A vertical chain of consecutive single
     Assigns is a gate finding.
3. **Per-unit verify.** After each unit, the work isn't done until it at least validates (see the
   verification gate); a generated `Process.xaml` must reflect the SDD steps.
4. **Commit small + record tokens.** One workflow/process per focused commit (`feat(<process>): ...`); tick
   `progress.md`. **Append each delegated unit's token count to `tokens.md`** the moment that subagent
   reports completion (the only point the count exists) — `tokens.md` is **mandatory**, not optional;
   initialize it on the first delegation if absent
   (`python3 ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/check_tokens.py --init .wi/goals/<slug>/tokens.md`),
   and ship finalizes it (`token_report.py --write`) under a `check_tokens.py` close-out gate.
5. **Register new components.** If the build created something reusable (a generic login, a notifier),
   add it to `.wi/components.md` so the next process inherits it.

## 3. Orchestrator wire-up (if in scope)

For queues/assets/credentials/triggers, delegate to `uipath-platform` (it owns the `uip` CLI + Orchestrator
APIs). Names come from the SDD §7 resource manifest. Never hardcode secrets — create assets/credentials.

## 4. Scope & safety

Stay within the confirmed SDD; new scope becomes a logged task/assumption, not a silent addition. Never
commit secrets or local robot artifacts; respect `.gitignore` for `.local`, `*.user`, etc.

**Shared-worktree git landmines** (the parallel build waves share one worktree, same as `wi:build`): **no
`git stash`** (the stash stack is shared across worktrees via `refs/stash` — a `pop` can apply a sibling
wave's WIP), **no `git clean`** (it deletes another wave's generated `.xaml`/`.cs` it sees as untracked), and
**no `reset --hard` / `checkout` of shared or protected branches**. Need to park WIP? Commit it to a
throwaway branch you own. The orchestrator commits per unit (step 2.4); a delegated build never runs
destructive git.

## Notes

- If `uipath-rpa-workflows` isn't installed, build can't proceed — stop with the complete SDD pack and say
  so (the front-half artifacts are still a deliverable).
- Keep `Main.xaml`/`Config.xlsx` edits serialized (shared files) even when sub-workflows parallelize.
