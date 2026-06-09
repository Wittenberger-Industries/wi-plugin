# WI — Claude Code plugin suite

`wi` is a marketplace containing the **`wi`** plugin: an opinionated, low-token development loop. You scan a
project once, then drive each feature with a single command that talks to you twice — brainstorm and a design gate —
and otherwise runs to a pull request on its own.

| Command | Status | What it does |
|---------|--------|--------------|
| **`/wi:scan`** | ✅ available | Documents an existing project — incl. a mermaid architecture diagram — and bootstraps wi (constitution + optional plugin installs). |
| **`/wi:dev "idea"`** | ✅ available | Brainstorms a feature with you, designs, confirms architecture + design at one gate, then builds and ships hands-off to an open PR. Add `--auto` to auto-approve the gate. |
| **`/wi:rpa "pdd"`** | ✅ available | Parses a PDD (markitdown), refines the TO-BE, writes an SDD + architecture + assumptions, then builds a REFramework solution via the UiPath skills — XAML-only or coded, your choice at the design gate — to a PR. One run per PDD (1..N processes); `--auto` supported. |

## Install

```
/plugin marketplace add <path-or-git-url-of-this-repo>
/plugin install wi@wi
```

`wi` is the marketplace name (from `.claude-plugin/marketplace.json`); `wi` is also the plugin. Its skills
then invoke as `/wi:scan`, `/wi:dev`, etc., and also auto-trigger from natural language.

## Updating after edits (local marketplace)

1. Edit the plugin source; bump `version` in `plugins/wi/.claude-plugin/plugin.json` (+ the marketplace entry).
2. `/plugin marketplace update wi`   (local marketplaces don't auto-update by default)
3. `/reload-plugins` when prompted — or restart Claude Code.
4. Stale anyway? `/plugin uninstall wi@wi` then `/plugin install wi@wi`. Optionally enable auto-update
   for the `wi` marketplace in the `/plugin` UI.

## Validating (before publishing)

From the repo root, run `python3 scripts/validate.py` — it checks the manifests are valid JSON, every skill
and agent has valid YAML frontmatter (`name` + `description`), and every `${CLAUDE_PLUGIN_ROOT}` reference
resolves. `pip install pyyaml` enables the full frontmatter parse.

## Structure

```
.
├── .claude-plugin/
│   └── marketplace.json      # lists the wi plugin
├── plugins/
│   └── wi/
│       ├── .claude-plugin/plugin.json
│       ├── skills/           # scan, dev, brainstorm, research, plan, build, ship, rpa
│       ├── agents/           # task-runner, researcher
│       └── README.md
├── scripts/
│   └── validate.py           # pre-release check (frontmatter, JSON, cross-refs)
└── README.md                 # you are here
```

## How it flows

```
/wi:scan            once per project — documents it, bootstraps wi
/wi:dev "idea"            ->  brainstorm (you) -> research -> plan -> DESIGN GATE (you) -> build -> ship -> PR
/wi:dev "idea" --auto  ->  same, gate auto-approved & recorded — fully hands-off
/wi:rpa "PDD.docx"      ->  ingest(markitdown) -> refine TO-BE (you) -> SDD -> DESIGN GATE (you) -> REFramework build via UiPath -> PR
(at handoff, wi prints a ready-made line for Claude Code's BUILT-IN /goal — paste it and the run
 keeps going across turns until the PR condition is met)
```

## Design principles (shared across the suite)

1. **State on disk, not in context.** A `.wi/` folder of small Markdown files lets phases hand off cheaply
   and survive a fresh context window.
2. **Two conversations, two gates.** Brainstorm sets scope; the design gate confirms architecture +
   design; everywhere else wi is autonomous.
3. **Delegate and summarize — in parallel.** Subagents do the heavy reading/editing and return short
   reports, dispatched concurrently in waves wherever the dependency graph allows.
4. **Borrow, don't reinvent.** Detect installed skills (superpowers, frontend-design) and
   hand off; ship light fallbacks so it still works standalone.
5. **An opinionated baseline beats no opinion.** Sensible defaults (Python-first), overridable per project
   in `constitution.md`.
6. **Compounds across goals.** Each goal reads the project's memory (constitution, glossary, learnings)
   and writes back what it learned, so the next one starts smarter.

## Roadmap

- **`/wi:rpa`** shipped (v0.7.0): PDD -> SDD -> REFramework build via the UiPath skills, with the build
  **paradigm chosen at the design gate — XAML-only (default) or coded `.cs`**. Next: a dry-run to harden it,
  Flow/non-REFramework targets, and deeper Orchestrator provisioning.
