---
type: Readme
title: WI — a cross-platform agentic dev loop
description: An opinionated, low-token dev loop (scan/dev/rpa) that runs on Claude Code, Codex CLI, and Copilot CLI from one source.
timestamp: 2026-06-14
tags: [wi, readme, overview]
---

# WI — a cross-platform agentic dev loop

`wi` is an opinionated, low-token development loop that runs on **Claude Code**, **Codex CLI**, and
**GitHub Copilot CLI** from one source. You scan a project once, then drive each feature with a single
command that talks to you twice — brainstorm and a design gate — and otherwise runs to a pull request on
its own.

| Command | What it does |
|---------|--------------|
| **`/wi:scan`** | Documents an existing project — incl. a mermaid architecture diagram — and bootstraps wi (constitution + optional plugin installs). |
| **`/wi:dev "idea"`** | Brainstorms a feature with you, designs, confirms architecture + design at one gate, then builds and ships hands-off to an open PR. Add `--auto` to auto-approve the gate. |
| **`/wi:rpa "pdd"`** | Parses a PDD (markitdown), refines the TO-BE, writes an SDD + architecture + assumptions, then builds a REFramework solution via the UiPath skills — XAML-only or coded, your choice at the design gate — to a PR. One run per PDD (1..N processes); `--auto` supported. |

On Claude the commands are `/wi:scan`, `/wi:dev`, …; on Codex/Copilot the skills invoke as `/scan`, `/dev`,
… or auto-trigger from natural language.

## Install

**Claude Code**
```
/plugin marketplace add Wittenberger-Industries/wi-plugin
/plugin install wi@wi
```

**Codex CLI** — Codex reads this repo's `.claude-plugin/marketplace.json` and `.codex-plugin/plugin.json`;
add the repo via Codex's plugin flow (`/plugins`) and enable `wi`. Native `/goal` and `CLAUDE_PLUGIN_ROOT`
compatibility work out of the box.

**GitHub Copilot CLI** — clone the repo and register the whole skills dir (recommended — wi's skills are
interdependent, so install them together, not one at a time):
```
git clone https://github.com/Wittenberger-Industries/wi-plugin
# then, in Copilot CLI:
/skills add <path-to-clone>/skills
```
Persistence uses Autopilot instead of `/goal`: wi's hands-off handoff prints
`copilot --autopilot --max-autopilot-continues <N> --no-ask-user --allow-all …`. ⚠️ That runs **fully
unattended** (prompts suppressed, all tools/paths granted) — drop `--allow-all` to keep risky-action
confirmations.

## Platform differences

wi is one source across three harnesses; only the autonomy spine differs:

| | Claude Code | Codex CLI | Copilot CLI |
|---|---|---|---|
| Skills | plugin (`.claude-plugin/`) | `.codex-plugin/` (+ reads `.claude-plugin/marketplace.json`) | whole-repo `/skills add` |
| Keep-alive | built-in `/goal` | native `/goal` | Autopilot flags |
| Command namespace | `/wi:dev` | `$dev` / `/skills` | `/dev` |
| `${CLAUDE_PLUGIN_ROOT}` | native | compat var | the cloned repo root |
| Subagents | Agent/Task | `spawn_agent` | `task` / `/fleet` |

Tool-name mappings live in `references/codex-tools.md` and `references/copilot-tools.md`; the
cross-platform bootstrap is `AGENTS.md`.

## How it flows

```
/wi:scan                  once per project — documents it, bootstraps wi
/wi:dev "idea"         -> brainstorm (you) -> research -> plan -> check -> DESIGN GATE (you) -> build -> check -> ship -> PR
/wi:dev "idea" --auto  -> same, gate auto-approved & recorded — fully hands-off
/wi:rpa "PDD.docx"     -> ingest(markitdown) -> refine TO-BE (you) -> SDD -> check -> DESIGN GATE (you) -> REFramework build -> check -> PR
```

The **check** steps are wi's read-only **checker** agent. In *plan mode* (before the gate) it builds a
coverage matrix — every acceptance criterion, locked decision, glossary term, and pitfall mapped to a
covering task — and flags silent scope-reduction or over-build as BLOCKER / WARNING / INFO for the gate to
weigh. In *result mode* (at ship) it confirms each criterion and locked decision was actually delivered and
**wired**, not just present. It feeds the gate and the ship review; it doesn't replace line-level code
review.

At handoff wi arms a keep-alive loop so the run continues across turns until the PR condition holds —
Claude Code & Codex use their built-in `/goal`; Copilot uses Autopilot. wi works without it too, just less
robustly through a stalled turn.

## The `.wi/` directory

```
.wi/
├── constitution.md      # project rules — written once, read by every phase
├── repo-map.md          # cached scan: stack + exact commands + conventions + frontend/backend
├── overview.md          # readable docs of an existing project (skipped for greenfield)
├── architecture.md      # mermaid architecture diagram (scan; kept current by ship)
├── glossary.md          # project domain terms (brainstorm): canonical names + aliases
├── adr/                 # project-wide decision log: ADR-0001, ADR-0002, ... (+ index.md)
├── learnings.md         # learnings index: one line + hook per goal — phases read this, not the dir
├── learnings/           # substantial per-goal learnings in their own .mds — compounds across goals
├── roadmap.md           # optional: ordered goals for a larger effort
└── goals/<slug>/
    ├── progress.md      # the goal's state machine (source of truth)
    ├── brief.md         # brainstorm output: what you want
    ├── research/        # researcher notes + the chosen approach
    ├── spec.md          # plan: what/why + testable acceptance criteria
    ├── tasks.md         # plan: small ordered tasks (files + verification)
    ├── pitfalls.md      # plan: failure modes for this change
    ├── verification.md  # checker output (plan + result mode) — ephemeral; verdict folds into PR.md
    ├── tokens.md        # token ledger: the per-run cost report (finalized before the PR)
    └── PR.md            # the PR description — committed, used by gh pr create
```

Every file above is a typed **OKF** knowledge doc: it opens with YAML frontmatter carrying a `type` (plus
title / description / timestamp), so each phase — and `validate.py` — can parse the dossier mechanically.

## Skills & agents

| Skill | Invoke (Claude) | Role |
|-------|-----------------|------|
| `scan` | `/wi:scan` | Document an existing project and bootstrap wi; `--refresh` = drift check + learnings consolidation |
| `dev` | `/wi:dev "idea"` | The interactive entry: brainstorm, then hand off |
| `rpa` | `/wi:rpa "pdd"` | RPA entry: ingest PDD -> refine TO-BE -> SDD -> REFramework build via UiPath skills -> PR |
| `brainstorm` | via `dev` | The requirements dialogue (the one interactive phase) + glossary upkeep |
| `research` | via `dev` | The design half: research -> plan -> design gate (your confirmation) |
| `plan` | via `research` | spec + tasks + pitfalls (+ ADR) |
| `build` | post-gate | worktree + parallel waves of task subagents (TDD) |
| `ship` | post-gate | gate -> review -> docs-sync -> learnings -> tokens -> PR.md -> open PR -> checklist |

Agents: **task-runner** (executes one build task in isolation), **researcher** (picks the approach in the
autonomous phase), and **checker** (read-only goal-backward verification — the **check** steps above). The
GSD-derived hardening that ships with these: the researcher tags every claim `[VERIFIED]` / `[CITED]` /
`[ASSUMED]` and runs a **Runtime State Inventory** on rename/migration goals (the runtime state a `grep`
can't see); the task-runner follows a typed deviation taxonomy (auto-fix small bugs, STOP-and-ask on
architectural changes), self-checks before claiming done, and respects worktree git-safety rules. Every
skill auto-triggers from natural language too.

## Structure

```
.
├── .claude-plugin/
│   ├── marketplace.json   # marketplace (Claude; Codex reads this too)
│   └── plugin.json        # the wi plugin manifest
├── .codex-plugin/
│   └── plugin.json        # Codex plugin manifest
├── skills/                # scan, dev, brainstorm, research, plan, build, ship, rpa
├── agents/                # task-runner, researcher, checker
├── references/            # codex-tools.md, copilot-tools.md (tool-name maps)
├── scripts/validate.py    # pre-release check (frontmatter, JSON, cross-refs, OKF)
├── docs/                  # specs & plans
├── AGENTS.md              # cross-platform bootstrap (Codex + Copilot)
└── README.md              # you are here
```

## Setup & conventions

- **No required env vars or MCP servers.** `/wi:scan` offers to install the optional skills wi delegates to.
- **Python-first** defaults (uv · pytest · ruff · mypy), stack-agnostic — `scan` records whatever the repo
  uses, and `constitution.md` is where you override.
- Opening the PR uses `gh` if available; otherwise wi pushes the branch and leaves the PR command for you.

## Plays well with (optional, auto-detected)

- **obra/superpowers** — brainstorming, writing-plans, subagent-driven-development, using-git-worktrees,
  test-driven-development, requesting-code-review, verification-before-completion,
  finishing-a-development-branch. Installable on Claude, Codex, and Copilot; used when present, with light
  fallbacks when not.
- **anthropics/skills:frontend-design** (+ `pbakaus/impeccable`, `leonxlnx/taste-skill`) for `[frontend]`
  tasks.

If none are installed, wi still runs the whole loop on its own.

## Design principles

1. **State on disk, not in context.** A `.wi/` folder of small Markdown files lets phases hand off cheaply
   and survive a fresh context window.
2. **Two conversations, two gates.** Brainstorm sets scope; the design gate confirms architecture +
   design; everywhere else wi is autonomous.
3. **Delegate and summarize — in parallel.** Subagents do the heavy reading/editing and return short
   reports, dispatched concurrently in waves wherever the dependency graph allows.
4. **Borrow, don't reinvent.** Detect installed skills (superpowers, frontend-design) and hand off; ship
   light fallbacks so it still works standalone.
5. **An opinionated baseline beats no opinion.** Sensible defaults (Python-first), overridable per project
   in `constitution.md`.
6. **Compounds across goals.** Each goal reads the project's memory (constitution, glossary, learnings) and
   writes back what it learned, so the next one starts smarter.
7. **Build the least that works.** A Simplicity discipline threads through the loop — YAGNI, prefer the
   stdlib or an existing dep over a new one, deletion over addition. The checker flags over-build, and the
   design gate sees the *leaner path* next to the chosen approach.

## Maintaining

- **Validate before publishing:** from the repo root, `python scripts/validate.py` (or `python3`) — checks
  manifests are valid JSON, every skill/agent has valid `name`+`description` frontmatter, every
  `${CLAUDE_PLUGIN_ROOT}` reference resolves, and every concept doc is **OKF**-conformant (typed YAML
  frontmatter) with no truncated-write signatures — a missing trailing newline or unbalanced code fences.
  `pip install pyyaml` enables the full frontmatter parse.
- **Claude local-marketplace updates:** bump `version` in `.claude-plugin/plugin.json` (+ the marketplace
  entry), then `/plugin marketplace update wi` and `/reload-plugins` (or restart). Codex and Copilot
  re-read the repo through their own install/update flows.
- **Rolling back the rpa parity layer (v0.10.1):** the rpa goal-level verification + Simplicity + Runtime
  State Inventory + worktree-safety wiring is **additive and behavior-only** — no data or migration impact.
  If `/wi:rpa` starts failing because of it, revert the whole layer: `git revert <the v0.10.1 rpa-parity
  squash-merge commit>` (find it via `git log --oneline --grep "rpa flow to parity"`). It touches exactly
  six files — `agents/checker.md`, `skills/rpa/SKILL.md`, and under `skills/rpa/references/`:
  `verification-gate.md`, `brainstorm-protocol.md`, `rpa-constitution-template.md`, `build-uipath.md` — so a
  manual revert of those restores the prior rpa behavior. The dev spine is unaffected.

## Roadmap

- **rpa tenant publish** (v0.11.0) shipped — `wi:rpa` can publish a verified, PR'd build to a connected
  Orchestrator tenant: the design gate approves `Publish: none | feed | deploy` (+ folder, prod-guarded),
  and ship delegates `pack`/`publish`/`deploy`/`activate` to `uipath-solution` — best-effort, hands-off-safe.
  Next: Maestro flow as a build paradigm. Design and plan in `docs/specs/` and `docs/plans/`.
- **Numbered goal directories** (v0.10.5) shipped — new goals get a global 4-digit ordinal prefix as part
  of the slug (`0001-<name>`, mirroring `ADR-NNNN`), so `.wi/goals/` lists in implementation order — visible
  in the directory, the branch name, and the PR. dev + rpa; existing goals untouched. Design and plan in
  `docs/specs/` and `docs/plans/`.
- **tokens.md guardrails** (v0.10.4) shipped — the per-goal token ledger can no longer be silently
  skipped: a deterministic scaffold (`check_tokens.py --init`), `token_report.py --write` finalizes the
  orchestrator total + Subagents sum in place, and a `check_tokens.py` close-out gate blocks the PR on a
  genuine skip (an honest `unavailable` still ships). Dev + rpa flows; design and plan in `docs/specs/`
  and `docs/plans/`.
- **Agent verification layer** (v0.9.2-v0.10.0) shipped — a read-only **checker** (goal-backward
  verification, plan + result modes), researcher provenance + a **Runtime State Inventory**, a task-runner
  deviation taxonomy + self-check, and a **Simplicity** discipline across the loop; distilled from
  GSD-core's agent patterns and recorded in `docs/specs/2026-06-14-agent-upgrades-from-gsd.md`.
- **Cross-platform** (Codex CLI + Copilot CLI) support shipped — one source, per-platform packaging + a
  platform-aware autonomy spine. Design and plan in `docs/specs/` and `docs/plans/`.
- **`/wi:rpa`** (v0.7.0): PDD -> SDD -> REFramework build via the UiPath skills, build paradigm chosen at
  the design gate (XAML-only default, or coded `.cs`). Next: a dry-run to harden it, Flow/non-REFramework
  targets, and deeper Orchestrator provisioning.
