---
type: Template
title: Project constitution — template
description: Template for an OKF-conformant .wi/constitution.md (the project's ground rules).
timestamp: 2026-06-14
tags: [constitution, template, okf, scan]
---

# Project constitution — template

Copy this to `.wi/constitution.md`, fill in from what `scan` detected, and ask the user to confirm the
lines marked `(confirm)`. This file is the project's ground rules. **Every phase reads it**, so it is the
cheapest possible place to encode "how we build here" — write it once, and you stop re-explaining
conventions in every plan and every build subagent.

Keep it short and declarative. If a rule isn't worth enforcing, don't write it.

```markdown
---
type: Constitution
title: Constitution — <project name>
description: The project's ground rules — read by every wi phase.
timestamp: <YYYY-MM-DD>
---

# Constitution — <project name>

> The rules wi follows for this repo. Edit freely; this overrides wi's defaults.

## Language & tooling
- **Primary language:** <e.g. Python 3.12>   (confirm)
- **Package manager / runner:** <uv>   (confirm)
- **Canonical commands:** see .wi/repo-map.md (do not duplicate here)

## Code style
- Format with <ruff format>; lint with <ruff check>. Lint must pass before ship.   (confirm)
- Type checking: <mypy strict on src/> — new code must type-check.   (confirm)
- Prefer small, pure functions; isolate side effects; no dead code or commented-out blocks.
- Naming follows existing files; match the surrounding module, don't import a new style.

## Simplicity  (build the least that works)
- Before building, ask whether it needs to exist at all. Speculative need = skip it, say so in one line. (YAGNI)
- Reach in order: stdlib → native platform feature → already-installed dep → a few lines → and only then new code or a new dependency.
- Deletion over addition. No abstraction until a second caller exists (no interface-of-one, no config for a value that never changes). Fewest files, shortest working diff.
- Lazy, not negligent: never simplify away input validation at trust boundaries, error handling that prevents data loss, security, or accessibility.
- Mark a deliberate shortcut with a comment naming its ceiling and the upgrade path — e.g. `# shortcut: global lock; per-account locks if throughput matters`.

## Testing  (this is enforced, not optional)
- New behavior ships with tests. Default to TDD: write the failing test first.   (confirm)
- Tests live in <tests/>, named <test_*.py>. A change isn't done until the relevant tests pass.
- Don't weaken or delete a test to make the suite green — fix the code or change the test deliberately
  with a noted reason.

## Architecture & dependencies
- Respect existing module boundaries and layering; don't reach across them for convenience.
- Adding a dependency is a decision — clear the Simplicity ladder first, then justify it in the goal's spec.
- Any hard-to-reverse decision (datastore, framework, public API shape, auth model) requires an ADR.

## Git & shipping
- One goal → one branch/worktree → one focused PR. Small, reviewable commits.
- Conventional-ish commit subjects (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`).   (confirm)
- The ship gate (tests + lint + typecheck) must pass before opening a PR.

## Safety
- Never commit secrets. Read config from the environment.
- Don't run destructive commands (force-push, db drops, mass deletes) without explicit user confirmation.

## Out of scope by default
- <list things this project deliberately avoids, e.g. "no new microservices", "no ORM swaps">
```

## Defaults wi assumes when a rule is left blank

If the user doesn't override, wi applies these (Python-leaning) defaults, because an opinionated
baseline beats no opinion:

- Test before merge; prefer TDD for non-trivial logic.
- Lint + typecheck are part of "done".
- New dependency = justify it; prefer stdlib / native / existing.
- Build the least that works — skip speculative work (YAGNI), prefer deletion, mark deliberate shortcuts with their ceiling.
- Hard-to-reverse decision = write an ADR.
- One goal = one branch = one PR.
