---
type: Skill
name: brainstorm
user-invocable: false
description: >
  Run the interactive dialogue that pins down WHAT a feature should be, before any autonomous work. Use
  this skill when the user types "/wi:brainstorm", as the interactive phase of "/wi:dev", or when they say
  "I have an idea", "help me think through what I want", or "let's scope a feature". This is the first of
  wi's two conversations — the technical "how" is designed autonomously and confirmed once at the design
  gate.
---

# brainstorm — pin down what the user wants

This is the **first** of two conversations in the wi loop (the second is the design gate). Capture *what* the feature should be — behavior,
boundaries, constraints — clearly enough that the autonomous phases (research → build → ship) can take it from there without
coming back to ask. You decide the WHAT; the research skill decides the HOW, and the build phase implements it.

**This is a real conversation with the USER — not a monologue.** Put the open questions to the user and WAIT
for answers; asking yourself a question and answering it (`… → my answer`), then replaying one bulk brief for
approval, is **not** a brainstorm — it's the failure mode that lets specs drift. Batch related questions into
focused rounds, but the answers come from the user.

## Step 0 — delegation check (mandatory, FIRST action)

Look for `superpowers:brainstorming` in your available skills. **If present, you MUST invoke it** to run
the dialogue — wi's job is then only to capture the outcome into `.wi/features/<slug>/brief.md` in the
format below. Log the mode to `progress.md` either way — engine plus interactivity:
`brainstorm via superpowers:brainstorming` or `brainstorm via wi fallback (superpowers absent)`, suffixed
`, dialogue` | `, self-answered (headless)` (headless rule below). Running the fallback while superpowers
is installed is a defect, not a preference — wi exists to orchestrate the best installed tool, and the
delegation log gets checked after runs. **Either way, the dialogue is with the USER** — if
`superpowers:brainstorming` starts answering its own questions, stop and put them to the user yourself;
"capture the outcome" means capture *the user's* answers, not a self-generated brief.

**Scope of the delegation — wi supersedes the delegate's pipeline.** `superpowers:brainstorming` supplies
the *dialogue method*; its own artifact and handoff contract do not apply under wi. The outcome is
captured in wi's `brief.md` (no `docs/superpowers/specs/` design doc, and no separate spec-review gate
beyond the must-asks below), and its "the only skill you invoke next is writing-plans" ending is replaced
by wi's own pipeline (dev owns the handoff; research/plan fire in their phases — plan's delegation check
invokes writing-plans there). Where the delegate's checklist demands those steps, satisfy them with the wi
equivalents and move on.

## Must-ask before handoff (interactive — never skipped)

Whoever runs the dialogue (superpowers or the fallback), the brief isn't done until the user has answered:
1. **Scope** — what's in, and the explicit **non-goals**.
2. **Behavior** — the load-bearing WHAT decisions, with concrete examples (not abstractions).
3. **Acceptance** — what's observably true when it's done.
4. **Hard constraints** — deadline / performance / compatibility / must-reuse / regulatory.

Capture answers in `brief.md`; if the user genuinely can't answer one, log it under *Open questions for
research* — don't invent it.

**Headless runs** (no user can answer at all — an unattended dispatch: CI, a subagent, a scheduled run):
the must-asks still hold, but each is self-resolved with the smallest reasonable choice and logged as an
assumption in `brief.md`, and the stamp says so (`, self-answered (headless)`). The step-0 delegation
still applies: invoke `superpowers:brainstorming` when present (it structures the questions; its
questions are then self-answered under this rule) and stamp the engine as usual — if the engine cannot
run without a user, fall back and stamp `via wi fallback, self-answered (headless)`. This is a fallback
for *absence*, not a `--auto` behavior — `--auto` collapses the stops *after* brainstorm, never this
conversation: the user who typed the command is present for it.

## Glossary & term-sharpening (both paths)

Whether superpowers ran the dialogue or wi did, sharpen the language and persist it — vague terms are how
specs drift. Maintain project-level `.wi/glossary.md` (shared across features; create it lazily):
- **Sharpen fuzzy/overloaded words.** When the user says something like "service" or "page", propose a
  precise canonical name and confirm: "by 'service' do you mean a route, a catalog entry, or a component?"
- **Cross-check against code.** Grep the repo for the term; if the code already uses it differently,
  surface the contradiction before accepting the premise.
- **Write resolved terms inline** (don't batch), using this format — what the term *is*, plus aliases to
  avoid:

```markdown
---
type: Glossary
title: Glossary — <project>
description: Canonical project domain terms and the aliases to avoid.
timestamp: <YYYY-MM-DD>
---

# Glossary — <project>

**<Term>:** <one or two sentences: what it IS, not what it does.>
_Avoid_: <alias1>, <alias2>
```

Only project-specific domain terms, not general programming words. Be opinionated: pick the best word,
list the rest as aliases. A shared vocabulary makes every future brief and spec sharper.

Glossary updates are committed where written (`docs(wi): glossary` — the project-level rule in
`wi-directory.md`).

## Fallback dialogue (ONLY when superpowers:brainstorming is absent)

1. **Load context.** Read `constitution.md` + `repo-map.md` (and `overview.md` + `.wi/glossary.md` if
   present) so the brief fits the real project, not a generic one.
2. **Talk about the WHAT.** Have a real back-and-forth on:
   - the user-visible behavior / the features they want — concrete examples beat abstractions;
   - boundaries / non-goals — what's explicitly out;
   - hard constraints — deadline, performance, compatibility, must-reuse-X;
   - any approach *preferences* they hold — capture as non-binding preferences, since the research phase decides.
   Use AskUserQuestion for the sharp forks (patterns:
   `${CLAUDE_PLUGIN_ROOT}/skills/brainstorm/references/question-patterns.md`). Ask in focused rounds; stop
   when the WHAT is clear, not when you run out of questions.
3. **Reflect and confirm.** Play the brief back. The user is about to step away — make sure it captures
   their intent; the next check-in is the design gate (architecture + design), and after that nothing
   until the PR.
4. **Write `brief.md`** and let `dev` handle the handoff to the autonomous loop.

Don't do the technical research or choose the approach here — that's the research skill's job. Light
context-gathering to ask good questions is fine; deep approach research is not.

## `brief.md` template

```markdown
---
type: Brief
title: <feature title>
description: What the user wants from this feature, in plain terms (the WHAT, not the HOW).
feature: <slug>
timestamp: <YYYY-MM-DD>
---

# Brief: <feature title>

## What the user wants
<the behavior/features in plain terms, with concrete examples. The WHAT, not the HOW.>

## Acceptance (in the user's words)
- <observable thing that should be true when this is done>
- ...

## Scope & non-goals
- In: <...>
- Out: <explicitly not now>

## Constraints
- <deadline, performance, compatibility, must-reuse, regulatory, ...>

## Approach preferences (optional, non-binding)
- <any leanings the user voiced; the research phase weighs these but decides the approach itself>

## Open questions for research
- <things the user couldn't answer that the research phase should resolve>
```

Keep it under ~120 lines. A good brief is small and clear about intent; the cleverness comes later, on its
own.
