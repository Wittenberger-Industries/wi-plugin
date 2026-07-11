---
type: Reference
title: "RPA prerequisites: bootstrap"
description: "`wi:rpa` is thin: it produces the spec and delegates the build."
timestamp: 2026-06-08
tags: [rpa, reference]
---

# RPA prerequisites: bootstrap

`wi:rpa` is thin: it produces the spec and delegates the build. Two prerequisites make it work; check for
them and **offer** to install what's missing (never hard-fail silently; say which mode you're in).

## 1. markitdown (mandatory: parses the PDD)

Microsoft's doc→Markdown converter. Used to turn a `.docx`/`.pdf`/`.pptx` PDD into `pdd.md`.

- **Check:** `markitdown --version` (or `python -c "import markitdown"`; python fallback:
  `references/workflow.md` "Script invocation").
- **Install:** `pip install 'markitdown[docx,pdf,pptx]'` (or `[all]`). Python 3.10+. If `pip` isn't
  available, `uv pip install 'markitdown[docx,pdf,pptx]'` in a venv.
- If the PDD is already Markdown, markitdown isn't strictly needed for that file, but install it anyway
  for the other supporting docs (a PDD often ships with `.docx`/`.xlsx` annexes).

## 2. UiPath skills (mandatory: the build engine)

UiPath ships its skills as a **Claude Code plugin marketplace**. They generate the XAML, know the
activity packages, and include a project-discovery agent.

wi delegates by **capability**, never by a hard-coded name: upstream can rename a slug, so resolve each
capability through this table (the single source of truth the other rpa references point back to):

| Capability wi delegates | UiPath skill (slug) | Verified as of |
|---|---|---|
| `.xaml`/`.cs` RPA workflow authoring: the REFramework build engine | `uipath-rpa` | 2026-07 |
| `.flow` Maestro flow authoring | `uipath-maestro-flow` | 2026-07 |
| Orchestrator / platform ops via the `uip` CLI (queues, assets, credentials, Integration Service connectors, validate/analyze) | `uipath-platform` | 2026-07 |
| Project discovery: auto-document an existing UiPath project's structure/conventions | `uipath-project-discovery-agent` *(an agent, not a skill)* | 2026-07 |

- **Check (by capability):** is the `uipath` plugin installed, i.e. are the table's skills present in the
  available skills list? Match each **capability**, not the literal string: the build half needs the skill
  that owns `.xaml`/`.cs` authoring (`uipath-rpa` as of 2026-07), so a future upstream rename degrades to a
  table lookup instead of a false "not installed".
- **Install (Claude Code):**
  ```
  /plugin marketplace add https://github.com/UiPath/skills
  /plugin install uipath@uipath-marketplace
  ```
  (Alternatively the UiPath CLI wizard: `npm i -g @uipath/cli` then `uip skills install`.)

If the UiPath skills are absent, wi:rpa can still do the front half (ingest → SDD → architecture +
assumptions) and stop with a complete spec pack, but it cannot build the XAML. Tell the user that and
offer to install.

## 3. .NET 8 runtime (the UiPath CLI + build need it)

Every UiPath CLI package and every `uip rpa build` require **.NET 8**; a host without it fails the build (or
limps on a roll-forward). Check at bootstrap and **offer to install**, same as the others.

- **Check:** `dotnet --list-runtimes`: look for `Microsoft.WindowsDesktop.App 8.` (UiPath's Windows XAML
  projects) and/or `Microsoft.NETCore.App 8.`. (`dotnet --info` also works.)
- **Install (Windows):** `winget install Microsoft.DotNet.DesktopRuntime.8` (the **Desktop Runtime 8**, needed
  for the Windows projects). To compile from source as well, `winget install Microsoft.DotNet.SDK.8` (the SDK
  includes the runtime). No winget → the official installer at https://dotnet.microsoft.com/download/dotnet/8.0.
- **Stop-gap** (a newer .NET is present but not 8): set `DOTNET_ROLL_FORWARD=Major` for the build, but prefer
  installing 8 properly; roll-forward is a workaround, not a fix.
- Like the UiPath skills, .NET 8 is a **build-half** prerequisite: the front half (ingest → SDD) runs without
  it. If it's missing and can't be installed, say so and stop at the SDD pack.

## Existing UiPath project → delegate discovery

If the repo already contains a UiPath project (`project.json`, a `Framework/` folder, `.xaml` files),
**delegate structure discovery to `uipath-project-discovery-agent`** rather than re-deriving it, and
capture its output into `.wi/` (repo conventions, existing workflows, the components already present →
seed `.wi/components.md`). This is the RPA analog of `wi:scan`; borrow it, don't reinvent it.

## Record the outcome

Note in the run log which prerequisites were present vs installed (e.g. "markitdown installed; uipath
plugin present; discovery delegated"), so the run is auditable and the next run starts informed.
