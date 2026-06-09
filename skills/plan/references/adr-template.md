# ADR — template

Architecture Decision Record. Write one only for decisions that are **hard to reverse** or that future
contributors will wonder "why did they do it this way?": datastore, framework, external service, public
API/schema shape, auth model, concurrency model, a notable dependency. Trivial choices don't need one.

Save as `.wi/adr/ADR-NNNN-short-title.md` — **one project-wide sequence** (ADR-0001, ADR-0002, ...), not
per-goal: the next number is the highest existing in `.wi/adr/` + 1, zero-padded to four digits. ADRs are
immutable once accepted — to change a decision, write a new ADR that supersedes the old one.

After writing an ADR, **append a row to `.wi/adr/index.md`** (create it from the template below if
absent) so the decision log stays browsable at a glance.

```markdown
# ADR-NNNN: <short imperative title, e.g. "Use Postgres for the event store">

- **Status:** proposed | accepted | superseded by ADR-MMMM
- **Date:** <YYYY-MM-DD>
- **Deciders:** <who signed off — or "wi research (autonomous)" + the gate outcome>
- **Goal:** <slug>  (the wi goal that produced this decision)

## Context
<the forces at play: requirements, constraints, what in the repo or roadmap makes this decision necessary
now. Neutral — state the problem, not the answer.>

## Decision
<the choice, stated plainly and actively: "We will …". Include the key specifics that make it real.>

## Consequences
- **Positive:** <what this buys us>
- **Negative / costs:** <what it costs or constrains; what we're now locked into>
- **Follow-ups:** <new work this creates — migrations, docs, deprecations>

## Alternatives considered
- **<option>** — <why not>.
- **<option>** — <why not>.

## Sources  (optional — required if web research informed the decision)
- <docs/links consulted; research/ notes get pruned at ship, so evidence lives here>
```

## Tips

- Title states the decision, not the topic: "Use X for Y", not "Database choice".
- The "Context" should let someone disagree with the decision on the merits — give them the real forces.
- Link the ADR from `spec.md`'s Design section so the plan and the rationale stay connected.

## `.wi/adr/index.md` template

```markdown
# Architecture decisions — <project>

| ID | Decision | Status | Date | Goal |
|----|----------|--------|------|------|
| [ADR-0001](ADR-0001-use-postgres.md) | Use Postgres for the event store | accepted | 2026-06-07 | event-store |
| [ADR-0002](ADR-0002-tags-child-table.md) | Store tags in a task_tags child table | accepted | 2026-06-07 | task-tags |
```
