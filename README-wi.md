# wi

An opinionated, low-token engineering loop for Claude Code. Three commands:

- **`/wi:scan`** — understand & bootstrap a project. It documents existing code (`.wi/overview.md` + a mermaid `.wi/architecture.md`), records
  the stack and the exact commands (`.wi/repo-map.md`), writes the project's ground rules
  (`.wi/constitution.md`), and offers to install the plugins wi works best with (superpowers,
  frontend-design). For an empty/new project it runs a short **guided setup** to define the stack.
- **`/wi:dev "<feature>"`** — brainstorm a feature with you, then build it. wi researches the approach
  (parallel researchers), drafts the design, **confirms architecture + design with you once at the design
  gate**, then builds in an isolated worktree — tasks dispatched to subagents in parallel waves — and
  opens a pull request with no further input. Add `--auto` to auto-approve the design gate (recorded,
  not asked) for a fully hands-off run.
- **`/wi:rpa "<pdd>"`** — turn a UiPath PDD into a built REFramework solution. Parses the PDD (markitdown),
  refines the TO-BE (filling the gaps PDDs leave), writes an SDD + architecture + assumptions, confirms at
  the design gate (where you approve the build paradigm — XAML-only or coded), then delegates the build to
  the UiPath skills. One run per PDD (1..N processes).

```
/wi:scan            (once per project)
/wi:dev "idea"  ->  brainstorm -> research -> plan -> DESIGN GATE -> build -> ship -> PR
```

It's deliberately light: almost nothing stays in context. State lives in a committed `.wi/` folder, heavy
work runs in subagents and git worktrees, and wi **borrows** existing skills (superpowers,
frontend-design) rather than reimplementing them.

## The `.wi/` directory

```
.wi/
├── constitution.md      # project rules — written once, read by every phase
├── repo-map.md          # cached scan: stack + exact commands + conventions + frontend/backend
├── overview.md          # readable docs of an existing project (skipped for greenfield)
├── architecture.md      # mermaid architecture diagram (scan; kept current by ship)
├── glossary.md          # project domain terms (brainstorm): canonical names + aliases
├── adr/                 # project-wide decision log: ADR-0001, ADR-0002, ... (+ index.md)
├── learnings/           # non-obvious knowledge harvested at ship — compounds across goals
├── roadmap.md           # optional: ordered goals for a larger effort
└── goals/<slug>/
    ├── progress.md      # the goal's state machine (source of truth)
    ├── brief.md         # brainstorm output: what you want
    ├── research/        # researcher notes + the chosen approach
    ├── spec.md          # plan: what/why + testable acceptance criteria
    ├── tasks.md         # plan: small ordered tasks (files + verification)
    ├── pitfalls.md      # plan: failure modes for this change
    └── tokens.md        # token ledger: the per-run cost report
```

## Skills & agents

| Skill | Invoke | Role |
|-------|--------|------|
| `scan` | `/wi:scan` | Document an existing project and bootstrap wi |
| `dev` | `/wi:dev "idea"` | The interactive entry: brainstorm, then hand off |
| `rpa` | `/wi:rpa "pdd"` | RPA entry: ingest PDD (markitdown) -> refine TO-BE -> SDD -> REFramework build via UiPath skills -> PR |
| `brainstorm` | via `dev` | The requirements dialogue (the one interactive phase) + glossary upkeep |
| `research` | via `dev` | The design half: research -> plan -> design gate (your confirmation) |
| *(built-in)* `/goal` | you, at handoff | Claude Code's keep-alive loop — wi prints the exact line to paste; build/ship supply the method |
| `plan` | via `research` | spec + tasks + pitfalls (+ ADR) |
| `build` | post-gate | worktree + parallel waves of task subagents (TDD) |
| `ship` | post-gate | gate -> review -> docs-sync -> learnings -> open PR |

Agents: **task-runner** (executes one build task in isolation) and **researcher** (picks the approach in
the autonomous phase). Every skill is also reachable directly as `/wi:<name>` and auto-triggers from
natural language.

## Install

```
/plugin marketplace add <path-or-git-url-of-the-wi-repo>
/plugin install wi@wi
```

Then `/wi:scan` once, and `/wi:dev "your feature"`.

## Setup & conventions

- **No required env vars or MCP servers.** `/wi:scan` offers to install the optional skills wi delegates to.
- **Python-first** defaults (uv · pytest · ruff · mypy), stack-agnostic — `scan` records whatever the repo
  uses, and `constitution.md` is where you override.
- Opening the PR uses `gh` if available; otherwise wi pushes the branch and leaves the PR command for you.

## Plays well with (optional, auto-detected)

- **obra/superpowers** — brainstorming, writing-plans, subagent-driven-development, using-git-worktrees,
  test-driven-development, requesting-code-review, verification-before-completion,
  finishing-a-development-branch. Used when present, with light fallbacks when not.
- **anthropics/skills:frontend-design** (+ `pbakaus/impeccable`, `leonxlnx/taste-skill`) for `[frontend]`
  tasks.

If none are installed, wi still runs the whole loop on its own.

## Philosophy

Two conversations: brainstorm (scope) and the design gate (architecture + design). Between and after
them, wi is autonomous all the way to a PR.
State on disk, heavy work in parallel subagents, a real verification gate that never weakens to go green,
and one feature -> one branch -> one PR. Every goal ends by compounding what it learned back into the
project's memory, so the next one starts smarter.
