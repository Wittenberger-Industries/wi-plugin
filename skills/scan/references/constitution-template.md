# Project constitution — template

Copy this to `.wi/constitution.md`, fill in from what `scan` detected, and ask the user to confirm the
lines marked `(confirm)`. This file is the project's ground rules. **Every phase reads it**, so it is the
cheapest possible place to encode "how we build here" — write it once, and you stop re-explaining
conventions in every plan and every build subagent.

Keep it short and declarative. If a rule isn't worth enforcing, don't write it.

```markdown
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

## Testing  (this is enforced, not optional)
- New behavior ships with tests. Default to TDD: write the failing test first.   (confirm)
- Tests live in <tests/>, named <test_*.py>. A change isn't done until the relevant tests pass.
- Don't weaken or delete a test to make the suite green — fix the code or change the test deliberately
  with a noted reason.

## Architecture & dependencies
- Respect existing module boundaries and layering; don't reach across them for convenience.
- Adding a dependency is a decision — justify it in the goal's spec, and prefer the stdlib / existing deps.
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
- New dependency = justify it.
- Hard-to-reverse decision = write an ADR.
- One goal = one branch = one PR.
