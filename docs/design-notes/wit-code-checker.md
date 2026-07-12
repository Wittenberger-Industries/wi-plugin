---
type: Design Notes
title: "wit-code-checker: design rationale (maintainer notes)"
description: The "why" behind agents/wit-code-checker.md's rules, relocated out of the loaded charter by #41 (the charter rides into every checker dispatch and carries rules only); each entry is anchored to the charter section it explains.
timestamp: 2026-07-11
tags: [wit-code-checker, agents, design-notes, context-budget]
---

# wit-code-checker: design rationale (maintainer notes)

`agents/wit-code-checker.md` is the checker's dispatch charter. It is loaded into every checker dispatch
(plan mode, result mode, and every MoA proposer and aggregator instance), so it carries rules only; the
rationale lives here, anchored by section. When editing the charter, keep this file in sync: a rule whose
"why" is deleted instead of relocated loses its guard against future "simplification".

## Frontmatter

- **Why `model: inherit` ships as the default:** a dispatch may pin a cheaper tier via the
  `wit-code-checker` row of `.wit/models.md` (resolved per `references/models.md`); `inherit` is the
  portable default when no routing is configured. The inline comment on the `model:` line is deliberate
  and stays; it is what stops a tidy-minded edit from dropping the "why" of the default.

## Intro

- **Why read-only, adversarial, never the author:** verification is only trustworthy under fresh-context
  isolation; an author reviewing its own work inherits its own blind spots. Isolation holds at the
  checker level, not the pass level, which is why the line-level review runs INLINE in result mode: the
  checker never authored the diff, so carrying the review inside the same dispatch preserves the
  reviewer-isolation property. Re-splitting the review into a second agent adds a dispatch without adding
  isolation, hence the charter's "not an improvement" line (kept there as the anti-split guard).
- **Why the design gate stays human:** the checker feeds the gate and never replaces it; the gate is
  where a human weighs whatever the bounded loop could not resolve.
- **Why the compact-reasoning carve-out exists:** over-compressed scrutiny is the named failure mode of
  the compact-reasoning rule (`references/compact-reasoning.md`); the rule trims meta-narration between
  steps, never the adversarial depth of coverage tracing, refutation, or evidence-hunting.

## Modes

- **Why the line-review template is read at runtime and never copied into wit's tree:** wit complements
  superpowers; reading `superpowers:requesting-code-review`'s reviewer template from its installed path
  means upstream template improvements are picked up automatically, with no vendored copy to drift.
- **Why the external-severity mapping is stated in the charter:** the superpowers template grades in its
  own vocabulary (Critical/Important/Minor); without the explicit mapping, external findings would leak a
  second taxonomy into `verification.md`.

## How you verify

- **(3) Why a stub-downgrade is always a BLOCKER:** a decision quietly downgraded to a stub is the most
  insidious failure there is; it looks like progress while shipping a hole. That is why the charter says
  "never a soft note".
- **(4) Why over-build is WARNING, not BLOCKER:** over-building is a judgment call the design gate
  weighs, not a feature failure. Down-scoping (3) and over-building (4) point in opposite directions, so
  the two hunts never tension against each other.
- **(6) Why the context-window ceiling matters:** oversized task-units are where build drifts from spec;
  splitting work into units a fresh context can hold is wit's whole premise.

## Severity

- **Why "Do not issue a WARNING for what is really a BLOCKER" is called out:** under-grading severity is
  the named soft-failure that makes verification worthless; a checker that grades everything WARNING
  never blocks anything.

## Bounded loop

- **Why the loop is capped at 2 rounds:** the gate decides; the checker does not loop forever.
  Escalating leftovers with their severity keeps the human deciding with eyes open instead of the loop
  burning budget chasing convergence.

## Output

- **Why the exists-check before returning:** a report about a file you never actually wrote is the exact
  failure wit exists to prevent; it is "evidence before assertions" applied to the checker itself.
- **Why `verification.md` is ephemeral:** ship folds the verdict and any waived findings into `PR.md`
  (ship:5), then the dossier tidy (ship:6) prunes it like research notes, so the flow's fixed dossier
  manifest is preserved.
- **Why the verdict marker sits on its own last line:** the orchestrator and the keep-alive loop detect
  the outcome without parsing prose. Known wrinkle (recorded in the 2026-07-10 dry-run comparison): the
  two parentheticals overlap on an INFO-only report (no BLOCKERs, yet one or more findings), which in
  practice returns `## ISSUES FOUND`; anything keying on `## CHECK PASSED` as "all clear" should know.
- **The template's title line uses a plain hyphen** ("Verification - <feature title>"): switched from an
  em-dash by #41's dash removal. The hyphen form is now the contract string; update any consumer in
  lockstep rather than "fixing" it back.

## MoA dispatches

- **Why plan mode never carries a marker:** MoA applies at wit's two judgment points only (see
  `references/moa.md`), and the checker's point is the result-mode review at ship; the plan-mode pre-gate
  check is a single dispatch by design.
- **Why proposers skip the file-write but keep the console-report discipline:** parallel writers would
  race on `verification.md`; the aggregator as sole writer keeps one authoritative artifact, while
  identical report discipline keeps proposals mergeable.
- **Why the single-CONTRACT guard is repeated in the charter** even though `references/moa.md` (its
  review-point section) is canonical: the charter is the one file every dispatched instance actually
  reads, so an instance tempted to "fix" the design by proposing a second reviewer agent meets the guard
  in its own charter.
