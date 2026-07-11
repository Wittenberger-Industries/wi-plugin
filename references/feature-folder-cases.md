---
type: Reference
title: "Feature-folder cases: the rare branches of opening a feature"
description: "On-demand handling for the non-default cases hit when opening a feature folder (ordinal edge cases, resume, in-flight overlap, done-slug collision, roadmap rows), factored verbatim out of dev:2; loaded only when the classifier lands on one."
timestamp: 2026-07-11
tags: [dev, feature-folder, resume, roadmap, reference]
---

# Feature-folder cases: the rare branches of opening a feature

dev:2 classifies every idea (**new / resume / in-flight-overlap / done-collision / roadmap-row**) and
opens this file for anything but a plain new feature. Each case carries its detection tell and its
handling, factored verbatim out of the skill so nothing changes in substance; the common path (derive
slug, assign the next global ordinal, create the folder, seed `progress.md`) stays in the skill and never
needs this file; the numbering rule itself is wi-directory.md's **Slugs bullet**, and each case below
carries its own numbering note. Cases compose (a roadmap row may also be a resume; a roadmap row still
gets an ordinal), so apply every case whose tell fires, in the order below.

## Resume detection

**Tell:** an in-flight feature (`.wi/features/*/progress.md` with Phase ≠ `done`) reads as this same idea.

Scan `.wi/features/*/progress.md` for Phase ≠ `done`. One matches this idea (same/near slug, or a title
that reads as the same feature)? Then this is a **resume, not a new feature**: re-read its progress.md,
announce the phase and what's left (ticked tasks, recorded decisions), and re-enter that phase;
research/build/ship all re-enter from progress.md (workflow.md). Never seed a second folder for the same
feature; never overwrite an existing dossier. A resumed feature keeps its number.

## In-flight overlap

**Tell:** the idea is new, but other features are in flight.

Idea is new but other features are in flight: say so in one line (slug + phase each). If their `tasks.md`
files overlap this idea's likely surface, run sequentially: two features editing the same module trades
merge conflicts for wall-clock.

## Done-slug collision

**Tell:** the derived kebab name collides with a **done** feature's.

Slug collides with a **done** feature: the global ordinal already makes the new folder unique (it gets
the next number), so the kebab name may safely repeat across ordinals; only add a `-2` suffix to
disambiguate identical names when scanning. A finished dossier is history, not a scratch folder.

## Roadmap match & dependency stacking

**Tell:** `.wi/roadmap.md` exists and this idea is one of its rows.

If `.wi/roadmap.md` exists and this idea is one of its rows, use the row's slug, mark it `in-progress`,
and carry the row's notes + sequencing rationale into brainstorm as seed context: the WHAT was
part-captured when the roadmap was written, so brainstorm gets shorter, not skipped. The row's name is
numbered when its folder is first created (the next global ordinal, wi-directory.md's Slugs bullet). Check its
**Depends on**: a dependency that is done-but-unmerged (PR still open) means this feature would build
against code `main` doesn't have; ask once (inside the brainstorm stop, like the preflight): wait for
the merge, **stack** this branch on the dependency's branch (record it in progress.md; retarget the PR
after the dep merges), or proceed off `main` deliberately.
