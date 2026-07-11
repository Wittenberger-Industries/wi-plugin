---
type: Design Notes
title: "wi-researcher: design rationale (maintainer notes)"
description: The "why" behind agents/wi-researcher.md's rules, relocated out of the loaded charter by issue 41; the runtime never reads this file; each entry is anchored to the charter section it explains.
timestamp: 2026-07-11
tags: [wi-researcher, agents, design-notes, context-budget]
---

# wi-researcher: design rationale (maintainer notes)

`agents/wi-researcher.md` is loaded on every researcher dispatch, often several in parallel per feature,
so it carries rules only. The rationale lives here, anchored by the charter section it explains. When
editing the charter, keep this file in sync; a rule whose "why" is deleted instead of relocated loses its
guard against future "simplification".

## Your loop, step 1: anchor on the brief

- **Why the Responsibility Map exists:** on a split frontend/backend repo it stops the planner misplacing
  work (auth in the client, a secret in the bundle). The charter keeps the artifact rule and the checker
  hook; this is the failure it prevents.
- **Where "fits *this* project, not the trendiest" went:** the principle survives once, in step 3's
  "Newest ≠ best" paragraph (fit with the repo and constitution trumps trendiness). Stating it again in
  step 1 was a restatement, not a second rule.

## Your loop, step 2: look inward

- **Why inward first:** reusing the codebase's own conventions usually beats importing something new. The
  decision rule that enforces this lives in step 3: the existing pattern wins unless it's measurably
  worse.

## Your loop, step 3: look outward

- **Why the tech-choice survey is mandatory, not optional:** the model's training data is a starting
  hypothesis about the ecosystem, not the answer; without a forced outward pass the researcher recommends
  whatever was current at training time. The per-claim form of the same principle stays in the charter as
  the first evidence rule (official docs beat your training-data hypothesis).
- **Why "verify against the version this repo pins":** advice for v2 silently breaks on v5; the lockfile
  defines what the build actually runs, not the latest docs.
- **Why queries must not be dated:** injecting a year (e.g. "2026") into a search biases retrieval toward
  stale pages someone happened to date; checking the publication date on the results catches staleness
  without skewing what comes back.
- **Why WebSearch/WebFetch stay the fallback:** a `tools:` allowlist can strip MCP tools from an agent on
  some Claude Code builds, so a charter that leaned on a docs-lookup MCP (e.g. Context7) alone would
  silently lose its web access. The bundled tools are the floor that is always present.
- **Why a tech-choice charter may spend most of its budget outward:** that is what the mode exists for;
  the repo-question mode is the cheap counterpart, so the mode pair prices research effort by question
  type.

## Your loop, step 4: the bounded spike

- **Why spike at all:** for one load-bearing uncertainty a throwaway probe beats an hour of doc-reading.
  The hard bounds (one spike per charter, minutes not hours, scratch deleted, never inside the repo tree)
  exist because an unbounded spike turns research into implementation.

## Tag every claim by provenance

- **Why load-bearing `[ASSUMED]` rows are promoted to spec Open questions and the ADR Citations:** so the
  design gate surfaces them for the user, instead of an unverified claim slipping through as settled fact.

## Runtime State Inventory

- **Why the sweep exists and is mandatory:** after every file in the repo is updated, the old name or
  shape usually still lives in datastores, live service config, OS-registered state, secret names, and
  built artifacts, and production breaks there; no `git diff` will ever surface it. The charter keeps the
  one-line scope statement ("a grep audit finds *files*, not runtime state") and the five categories.
- **Why a blank answer is banned:** a blank can't tell "checked, found nothing" from "never checked";
  "None - verified by `<check>`" forces the distinction. (The answer string is deliberately plain-hyphen
  so it stays greppable; `skills/rpa/references/brainstorm-protocol.md` quotes the same form.)
- **Why "code edit ≠ data migration" is its own rule:** "change how new records are written" leaves the
  million existing records keyed on the old value untouched; only a separate migration task per found
  item makes that work visible to the plan and to the checker's coverage matrix.
- **Why load-bearing rows are promoted into spec/tasks/pitfalls:** the durable record lives in the typed
  dossier; once promoted, the inventory note itself can be pruned with the rest of `research/` at ship.

## Output

- **Why `valid_until`:** so a later feature knows when the research has gone stale; the windows (about
  30 days for a stable area, about 7 for a fast-moving one) stay in the charter as the operative
  thresholds.
- **Why "research depth should land in the notes file, not in exploration sprawl" was trimmed:** it
  restated the standing norm the charter keeps one sentence earlier ("depth goes in the notes file; the
  report is the decision"), which `references/compact-reasoning.md` also cites as the canonical form.

## MoA dispatches

- Nothing relocated; the section was already terse. The proposer/aggregator protocol's canonical home is
  `references/moa.md`; the charter keeps the researcher-side duties (commit to one approach, no hedging,
  the proposal file paths, aggregator synthesis, report discipline) because a dispatched agent sees only
  its own charter, never the reference.
