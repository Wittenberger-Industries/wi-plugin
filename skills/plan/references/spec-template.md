# Spec — template

Copy to `.wi/goals/<slug>/spec.md`. The spec answers *what* and *why* and *how we'll know it's done* —
not *how to build it* (that's `tasks.md`). Keep it tight; every section earns its place.

```markdown
# Spec: <goal title>

## Summary
<2-4 sentences: what this delivers and why now. A reviewer should grok the change from this alone.>

## Goals
- <user- or system-visible outcome 1>
- <outcome 2>

## Non-goals
- <explicitly out of scope — borrowed/confirmed from the brief>

## Acceptance criteria  (each must be testable)
1. <Given/When/Then or a crisp checkable statement>  →  verified by: <test/command>
2. ...
3. ...

## Design
<the shape of the solution: key modules/functions/endpoints, data flow, and where it plugs into the
existing code from repo-map.md. Diagrams optional; prose is fine. Reference any ADR as ADR-NNNN.>

## Interfaces & data changes
- **APIs / signatures:** <new or changed endpoints, function/CLI signatures>
- **Data / schema:** <new tables/fields, migrations — flag if irreversible>
- **Config / env:** <new settings, secrets (names only)>
- **Dependencies:** <added libs + one-line justification each>

## Test plan
- **Unit:** <what gets unit-tested>
- **Integration / e2e:** <if applicable>
- **Edge cases:** <the ones worth an explicit test — pull from pitfalls.md>

## Rollout & back-out
- <feature flag? migration order? how to revert if it goes wrong?>

## Open questions
- <anything still unresolved that the user must decide before/at the gate>
```

## Quality bar

- Every acceptance criterion names how it's verified. If it can't, it's a wish, not a criterion.
- The design references real files/modules from `repo-map.md`, not hypothetical ones.
- Irreversible data or interface changes are called out explicitly and (if significant) backed by an ADR.
