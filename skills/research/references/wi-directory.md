---
type: Reference
title: The `.wi/` directory — WI's on-repo state
description: Layout, conventions, and OKF frontmatter for the .wi/ knowledge store wi writes per repo.
timestamp: 2026-06-14
tags: [wi-directory, okf, conventions, state]
---

# The `.wi/` directory — WI's on-repo state

All WI state lives in a single `.wi/` folder at the repo root. It is an
[OKF](/docs/specs/2026-06-14-okf-knowledge-format.md) knowledge bundle: plain Markdown with YAML
frontmatter, meant to be **committed** so the team (and your future self) can see how a feature was
reasoned about. Keep every file small and current; these are working artifacts, not essays.

```
.wi/
├── index.md                # OKF root index (optional): directory listing + okf_version. No frontmatter.
├── constitution.md         # project ground rules. Written once by scan, read by every phase.
├── repo-map.md             # cached scan facts: stack, commands, conventions, frontend/backend.
├── overview.md             # readable docs of an EXISTING project (scan; absent for greenfield).
├── architecture.md         # mermaid architecture diagram (scan; kept current by ship's docs-sync).
├── glossary.md             # project domain terms (brainstorm): canonical names + aliases to avoid.
├── adr/                    # project-wide decision log: ADR-0001, ADR-0002, ... + index.md
├── learnings.md            # INDEX of learnings: one line + hook per feature (ship). Read this, not the dir.
├── learnings/              # substantial per-feature learnings, each its own .md (ship; indexed above).
├── roadmap.md              # optional. Ordered list of features for a larger effort.
├── moa.md                  # MoA model assignments (optional; references/moa.md) — written+committed at first dev/rpa run
└── features/
    └── 0001-<slug>/        # one folder per feature; NNNN- global ordinal (creation order) + kebab slug
        ├── progress.md     # the state machine for this feature — single source of truth
        ├── brief.md        # brainstorm output: desired behavior, scope, constraints
        ├── research/       # questions.md + researcher notes + chosen-approach (+ runtime-state-inventory.md for rename/migration features) — EPHEMERAL
        ├── spec.md         # plan output: what/why + testable acceptance criteria
        ├── tasks.md        # plan output: small ordered tasks, each with files + verification
        ├── pitfalls.md     # plan output: known failure modes for this change
        ├── verification.md # checker output (plan mode pre-gate, result mode at ship) — EPHEMERAL; verdict folds into PR.md, pruned at ship's dossier tidy
        ├── moa-review.md   # cross-provider diff review (ship; only when configured) — EPHEMERAL, pruned with verification.md
        ├── tokens.md       # token ledger: exact subagent usage + orchestrator (finalized by ship pre-PR)
        └── PR.md           # the PR description (ship §5) — committed, consumed by gh pr create
```

## Conventions

- **Slugs** are short, kebab-case, derived from the feature, **prefixed with a global 4-digit ordinal
  assigned at creation**: "Add Stripe webhooks" -> `0001-stripe-webhooks`. The prefix mirrors `ADR-NNNN`
  (global across `.wi/features/`, monotonic, **never renumbered**) so `.wi/features/` lists in implementation
  order; next number = highest existing `.wi/features/` ordinal + 1 (else `0001`). Legacy features — unnumbered or with a non-numeric prefix — are left as-is and
  ignored by the next-number scan (they contribute nothing to the max).
- **Commit `.wi/`.** It is documentation. Feature-folder lifecycle: untracked in the main checkout through
  brainstorm/research/plan; build moves it into the feature worktree and commits it as the branch's first
  commit (`chore(<slug>): feature dossier`); main's copy arrives when the branch merges. **Project-level
  files are committed where they're written, by the phase that writes them** — scan its docs (+ the
  greenfield `.gitignore`), brainstorm glossary updates, research the ADR + its index row, dev/rpa
  `moa.md` / `roadmap.md`, ship the docs-sync — `chore(wi): …` / `docs(wi): …` subjects; **only the
  feature folder defers** to build's first branch commit. That is what puts ADRs on the branch (committed
  on main before build branches from HEAD) and lets every post-worktree phase read the same tracked
  copies. A team that doesn't want wi committing to main overrides this in the constitution. Gitignore
  `research/` only if it gets large or holds scraped material — leave a one-line summary in the ADR/spec
  instead.
- **Keep files lean.** Past ~150 lines a file is doing too much; split or summarize. Cheap handoff is the
  whole point.
- **One writer per phase.** A phase owns its outputs; later phases read but don't silently rewrite them.
- **No strays.** Everything feature-specific lives under `features/<slug>/` — never loose in `.wi/`. If a phase
  needs a scratch file, it goes in the slug folder (ship sweeps and deletes strays at the dossier tidy).
- **`research/`, `verification.md`, and `moa-review.md` are ephemeral.** Working notes exist to produce
  the ADR and spec; the checker's `verification.md` feeds the design gate (plan mode) and the ship review
  (result mode); `moa-review.md` is the cross-provider diff review's output (ship, only when configured).
  Their verdicts + any waived findings fold into `PR.md` (ship §5), then the dossier tidy (§6) prunes all
  three before the PR (unless the constitution says keep them). After `done`, a feature folder holds
  exactly the seven-file dossier: progress, brief, spec, tasks, pitfalls, tokens, PR.
- **Project-level memory persists & compounds.** `constitution.md`, `repo-map.md`, `overview.md`,
  `architecture.md`, `glossary.md`, `adr/`, `roadmap.md`, `moa.md`, `learnings.md`, and `learnings/` belong to the
  project — never pruned. Each feature reads them at the start and ship writes back into them, so the project
  gets smarter per feature.
- **Learnings recall is via the index.** Phases read `.wi/learnings.md` (one line + hook per feature) and
  open a `learnings/<slug>.md` detail file only when its hook is relevant to the current feature — never
  bulk-read the directory.

## OKF frontmatter & conventions

Every `.wi/` file is an [OKF](/docs/specs/2026-06-14-okf-knowledge-format.md) concept: it opens with a
YAML frontmatter block whose only required key is `type`. The full profile lives in that spec; the short
version:

- **Frontmatter.** `type` (required) + `title`, `description`, `timestamp` (ISO 8601), optional `tags`,
  plus wi extensions `feature` / `status` / `resource` where they apply. Keep the body's `# Title` H1 and
  `##` sections as they are.
- **`type` per file:** `constitution.md` → `Constitution`, `repo-map.md` → `Repo Map`, `overview.md` →
  `Overview`, `architecture.md` → `Architecture`, `glossary.md` → `Glossary`, `adr/ADR-*.md` → `ADR`,
  `learnings.md` → `Learnings Index`, `learnings/<slug>.md` → `Learning`, `roadmap.md` → `Roadmap`,
  `moa.md` → `MoA Config`; per
  feature: `progress.md` → `Feature Progress`, `brief.md` → `Brief`, `spec.md` → `Spec`, `tasks.md` →
  `Task List`, `pitfalls.md` → `Pitfalls`, `verification.md` → `Verification`, `tokens.md` →
  `Token Ledger`, `PR.md` → `PR Description`, `research/*.md` → `Research Note`,
  `research/runtime-state-inventory.md` → `Runtime State Inventory`.
- **Index files** carry no frontmatter — except the optional root `.wi/index.md`, which may declare
  `okf_version: "0.1"`. `learnings.md` and `adr/index.md` are typed indexes whose entries reuse each
  concept's `description`.
- **Log.** `progress.md`'s `## Log` uses ISO dates and a leading bold keyword (`**Created**`,
  `**Update**`, `**Decision**`); it stays append-order as a resumable run timeline.
- **Citations.** External sources go under a numbered `## Citations` heading at the foot of the doc.
- **Links.** Prefer bundle-relative `/features/<slug>/spec.md`; a broken link (not-yet-written knowledge) is
  normal, never an error.

## `progress.md` template

Seed it when the feature is created (by `dev`):

```markdown
---
type: Feature Progress
title: <one-line feature title>
description: <what this feature delivers, one line>
feature: <slug>
status: brainstorm   # brainstorm | research | plan | design-gate | build | ship | done
timestamp: <YYYY-MM-DD>
---

# Feature: <one-line feature title>

- **Slug:** <slug>
- **Created:** <YYYY-MM-DD>
- **Phase:** brainstorm        <!-- brainstorm | research | plan | design-gate | build | ship | done -->
- **Gate mode:** interactive   <!-- interactive | auto-approve (set by /wi:dev --auto) -->
- **Flow:** dev                <!-- dev | rpa — ship keys its dossier manifest + sweep whitelist on it; a missing line means dev -->
- **Worktree:** <path or "-">
- **Branch:** <branch or "-">

## Log
- <YYYY-MM-DD> created feature, phase = brainstorm

## Tasks (mirrored from tasks.md once planned)
- [ ] 1. <task>
- [ ] 2. <task>

## Decisions / blockers
- <approach chosen, ADR links, anything that blocked the autonomous run>
```

Update the **Phase** field and append to **Log** at every transition. During build, the **feature
branch's copy is canonical** — build committed the dossier into the worktree as the branch's first
commit, so tick tasks and log in the worktree's `.wi/` and the updates ride the PR;
`main`'s copy catches up on merge. The build phase ticks the task
checkboxes here, so a resumed (or handed-off) run knows exactly what's left. Record the chosen approach and
any blocker here too — it's what the user reads after a hands-off run.

## `tokens.md` template

Append a row the **moment** each subagent's completion notification arrives — the token figure exists
only in that notification. ship compiles the totals at the dossier tidy and `dev` includes the table in the final
report. The scaffold is written by `check_tokens.py --init` from `_ledger.TEMPLATE` (the source of truth
for the exact bytes); the block below is illustrative.

```markdown
---
type: Token Ledger
title: <feature title>
feature: <slug>
timestamp: <YYYY-MM-DD>
---

# Token ledger: <feature title>

| Phase | Source | Tokens | Basis |
|-------|--------|--------|-------|
| research | researcher: <topic> | <n> | exact (completion notification) |
| build W1 | task-runner: task 1 | <n> | exact |
| build W1 | task-runner: task 2 | <n> | exact |
| orchestrator | main thread, all phases | `ship/scripts/token_report.py` (parses the session transcript) | the only reliable measure; **unavailable** if the parse fails — never substitute or estimate |

**Subagents (exact): <sum>.**

## Orchestrator

_PENDING — the ledger is scaffolded by `check_tokens.py --init` (research §0), rows appended live, and
ship replaces this section during the dossier tidy (BEFORE the dossier commit and the PR) by running
`python ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/token_report.py --write <this file>`, which parses the
session transcript (per-turn `usage`: output, fresh input, cache write/read) and recomputes the Subagents
sum. That parsed figure is the **only** reliable orchestrator measure; if the parse fails it writes
`Orchestrator: unavailable for this run` — never a substitute, estimate, or invented figure. At close-out
`check_tokens.py <this file>` gates `Phase = done`: a tokens.md still reading PENDING (or missing rows) is
a defect that blocks the PR._
```

## `roadmap.md` template (optional, multi-feature efforts)

```markdown
---
type: Roadmap
title: <project / epic name>
description: <one-line epic summary>
timestamp: <YYYY-MM-DD>
---

# Roadmap: <project / epic name>

| # | Feature | Slug | Status | Depends on |
|---|---------|------|--------|-----------|
| 1 | <feature> | <slug> | done | - |
| 2 | <feature> | <slug> | in-progress | 1 |
| 3 | <feature> | <slug> | planned | 1 |

## Notes
- Sequencing rationale, parking-lot ideas, things explicitly out of scope.
```
