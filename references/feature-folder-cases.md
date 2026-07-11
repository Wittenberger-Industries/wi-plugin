---
type: Reference
title: "Feature-folder cases — the rare branches of opening a feature"
description: "On-demand handling for the non-default cases hit when opening a feature folder — legacy migration, ordinal edge cases, resume, in-flight overlap, done-slug collision, roadmap rows — factored verbatim out of dev step 2; loaded only when the classifier lands on one."
timestamp: 2026-07-11
tags: [dev, feature-folder, resume, roadmap, reference]
---

# Feature-folder cases — the rare branches of opening a feature

`dev` step 2 classifies every idea — **new / resume / in-flight-overlap / done-collision / roadmap-row /
legacy-repo** — and opens this file for anything but a plain new feature (`rpa`'s run seed routes its
legacy case here too). Each case carries its detection tell and its handling, factored verbatim out of
the skill so nothing changes in substance; the common path (derive slug, assign the ordinal, create the
folder, seed `progress.md`) stays in the skill and never needs this file. Cases compose — a legacy repo
may also hold a resume; a roadmap row still gets an ordinal — so apply every case whose tell fires, in
the order below.

## Legacy migration

**Tell:** the repo's work units still live under the pre-rename folder (`goals`, not `features`).

A repo whose work units still live under the pre-rename folder gets a one-time
`git mv .wi/goals .wi/features` before proceeding — commit it; the dossiers inside are untouched.

## Ordinal assignment (edge cases of the numbering rule)

**Tell:** applies at every creation; the edge cases in the parenthetical are what this section is for.

Derive a kebab-case name, then prefix the **next global 4-digit ordinal** so `<slug>` = `NNNN-<name>`
(e.g. `0001-stripe-webhooks`) — the full numbering rule (mirroring `ADR-NNNN`: global, monotonic,
assigned **once at creation, never renumbered**; next = highest existing ordinal + 1, else `0001`) is
wi-directory.md's **Slugs bullet**. Case notes: legacy unnumbered features are left as-is and ignored by
the next-number scan; a resumed feature keeps its number; a roadmap row's name is numbered when its
folder is first created.

## Resume detection

**Tell:** an in-flight feature (`.wi/features/*/progress.md` with Phase ≠ `done`) reads as this same idea.

Scan `.wi/features/*/progress.md` for Phase ≠ `done`. One matches this idea (same/near slug, or a title
that reads as the same feature)? Then this is a **resume, not a new feature**: re-read its progress.md,
announce the phase and what's left (ticked tasks, recorded decisions), and re-enter that phase —
research/build/ship all re-enter from progress.md (workflow.md). Never seed a second folder for the same
feature; never overwrite an existing dossier.

## In-flight overlap

**Tell:** the idea is new, but other features are in flight.

Idea is new but other features are in flight: say so in one line (slug + phase each). If their `tasks.md`
files overlap this idea's likely surface, run sequentially — two features editing the same module trades
merge conflicts for wall-clock.

## Done-slug collision

**Tell:** the derived kebab name collides with a **done** feature's.

Slug collides with a **done** feature: the global ordinal already makes the new folder unique (it gets
the next number), so the kebab name may safely repeat across ordinals; only add a `-2` suffix to
disambiguate identical names when scanning. A finished dossier is history, not a scratch folder.

## Roadmap match & dependency stacking

**Tell:** `.wi/roadmap.md` exists and this idea is one of its rows.

If `.wi/roadmap.md` exists and this idea is one of its rows, use the row's slug, mark it `in-progress`,
and carry the row's notes + sequencing rationale into brainstorm as seed context — the WHAT was
part-captured when the roadmap was written, so brainstorm gets shorter, not skipped. Check its
**Depends on**: a dependency that is done-but-unmerged (PR still open) means this feature would build
against code `main` doesn't have — ask once (inside the brainstorm stop, like the preflight): wait for
the merge, **stack** this branch on the dependency's branch (record it in progress.md; retarget the PR
after the dep merges), or proceed off `main` deliberately.
