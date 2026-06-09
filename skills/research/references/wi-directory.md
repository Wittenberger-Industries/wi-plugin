# The `.wi/` directory — WI's on-repo state

All WI state lives in a single `.wi/` folder at the repo root. It is plain Markdown, meant to be
**committed** so the team (and your future self) can see how a feature was reasoned about. Keep every file
small and current; these are working artifacts, not essays.

```
.wi/
├── constitution.md         # project ground rules. Written once by scan, read by every phase.
├── repo-map.md             # cached scan facts: stack, commands, conventions, frontend/backend.
├── overview.md             # readable docs of an EXISTING project (scan; absent for greenfield).
├── architecture.md         # mermaid architecture diagram (scan; kept current by ship's docs-sync).
├── glossary.md             # project domain terms (brainstorm): canonical names + aliases to avoid.
├── adr/                    # project-wide decision log: ADR-0001, ADR-0002, ... + index.md
├── learnings/              # per-goal non-obvious knowledge harvested at ship (compounds across goals).
├── roadmap.md              # optional. Ordered list of goals for a larger effort.
└── goals/
    └── <slug>/             # one folder per goal (feature), slug is kebab-case
        ├── progress.md     # the state machine for this goal — single source of truth
        ├── brief.md        # brainstorm output: desired behavior, scope, constraints
        ├── research/       # researcher notes + the chosen-approach rationale (autonomous phase)
        ├── spec.md         # plan output: what/why + testable acceptance criteria
        ├── tasks.md        # plan output: small ordered tasks, each with files + verification
        ├── pitfalls.md     # plan output: known failure modes for this change
        └── tokens.md       # token ledger: exact subagent usage + orchestrator estimate
```

## Conventions

- **Slugs** are short, kebab-case, derived from the feature: "Add Stripe webhooks" -> `stripe-webhooks`.
- **Commit `.wi/`.** It is documentation. Gitignore `research/` only if it gets large or holds scraped
  material — leave a one-line summary in the ADR/spec instead.
- **Keep files lean.** Past ~150 lines a file is doing too much; split or summarize. Cheap handoff is the
  whole point.
- **One writer per phase.** A phase owns its outputs; later phases read but don't silently rewrite them.
- **No strays.** Everything goal-specific lives under `goals/<slug>/` — never loose in `.wi/`. If a phase
  needs a scratch file, it goes in the slug folder (ship sweeps and deletes strays at close-out).
- **`research/` is ephemeral.** Working notes exist to produce the ADR and spec; ship prunes the folder
  before the PR (unless the constitution says keep it). After `done`, a goal folder holds exactly the
  seven-file dossier: progress, brief, spec, tasks, pitfalls, tokens, PR.
- **Project-level memory persists & compounds.** `constitution.md`, `repo-map.md`, `overview.md`,
  `architecture.md`, `glossary.md`, `adr/`, `roadmap.md`, and `learnings/` belong to the project — never pruned.
  Each goal reads them at the start and ship writes back into them, so the project gets smarter per goal.

## `progress.md` template

Seed it when the goal is created (by `dev`):

```markdown
# Goal: <one-line feature title>

- **Slug:** <slug>
- **Created:** <YYYY-MM-DD>
- **Phase:** brainstorm        <!-- brainstorm | research | plan | design-gate | build | ship | done -->
- **Gate mode:** interactive   <!-- interactive | auto-approve (set by /wi:dev --auto) -->
- **Worktree:** <path or "-">
- **Branch:** <branch or "-">

## Log
- <YYYY-MM-DD> created goal, phase = brainstorm

## Tasks (mirrored from tasks.md once planned)
- [ ] 1. <task>
- [ ] 2. <task>

## Decisions / blockers
- <approach chosen, ADR links, anything that blocked the autonomous run>
```

Update the **Phase** field and append to **Log** at every transition. During build, the **goal
branch's copy is canonical** — tick tasks and log in the worktree's `.wi/` so updates ride the PR;
`main`'s copy catches up on merge. The build phase ticks the task
checkboxes here, so a resumed (or handed-off) run knows exactly what's left. Record the chosen approach and
any blocker here too — it's what the user reads after a hands-off run.

## `tokens.md` template

Append a row the **moment** each subagent's completion notification arrives — the token figure exists
only in that notification. goal compiles the totals at Done and `dev` includes the table in the final
report.

```markdown
# Token ledger: <goal title>

| Phase | Source | Tokens | Basis |
|-------|--------|--------|-------|
| research | researcher: <topic> | <n> | exact (completion notification) |
| build W1 | task-runner: task 1 | <n> | exact |
| build W1 | task-runner: task 2 | <n> | exact |
| orchestrator | main thread, all phases | `ship/scripts/token_report.py` (parses the session transcript) | the only reliable measure; **unavailable** if the parse fails — never substitute or estimate |

**Subagents (exact): <sum>.** For the orchestrator/main-thread total, run
`python3 ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/token_report.py` — it parses the session transcript (the
harness records per-turn `usage`) and reports the token consumption (output, fresh input, cache write/read). That parsed
figure is the **only** reliable orchestrator measure; if the parse fails, report it **unavailable** — never
substitute an unreliable source, and never invent a number or a percentage of the subagents.
```

## `roadmap.md` template (optional, multi-goal efforts)

```markdown
# Roadmap: <project / epic name>

| # | Goal | Slug | Status | Depends on |
|---|------|------|--------|-----------|
| 1 | <goal> | <slug> | done | - |
| 2 | <goal> | <slug> | in-progress | 1 |
| 3 | <goal> | <slug> | planned | 1 |

## Notes
- Sequencing rationale, parking-lot ideas, things explicitly out of scop