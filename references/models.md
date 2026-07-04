---
type: Reference
title: "Tiered model routing — model assignments for wi's dispatched agents"
description: "Configurable tiered model routing: each wi-dispatched sub-agent (wi-code-checker, wi-researcher, wi-task-runner) gets its own tiered default, with an independent cross-provider diff review layered on top of wi-code-checker's result-mode pass when a second provider is configured. Config in .wi/models.md, set up on first run."
timestamp: 2026-07-02
tags: [models, routing, reference]
---

# Tiered model routing — model assignments for wi's dispatched agents

wi dispatches three kinds of sub-agents — **wi-researcher**, **wi-task-runner**, **wi-code-checker** — plus
the **orchestrator**, which is just the session itself (the agent reading this file, planning and routing
the run). Tiered model routing lets a project tune what each of the three sub-agents runs on, and adds an
**independent cross-provider diff review** — ideally a *different provider/architecture* (different training,
different blind spots) — as a layer on top of wi-code-checker's result-mode verification. Scope: **wi-dispatched agents only**
(wi-researcher, wi-task-runner, wi-code-checker, RPA build delegations); wi never re-models other plugins'
or the user's own agents.

**The orchestrator model is informational.** A plugin cannot set the session model — the user picks it
with `/model`. wi records the intended tier and, at run start, **warns once** if the session model is
below it (e.g. config says `fable`, session runs `haiku`); it never blocks. The reverse is **not** a
mismatch and gets no warning: a session running *above* the configured tier (say a `fable` session over
the simple preset) still dispatches every role at its **configured** tier — premium tiers are priced
accordingly, so wi never auto-escalates a dispatch above config. A tier above `opus` enters a run only
when the user put it there: choosing **smart** interactively, or writing it into custom rows / per-agent
overrides.

## The config file — `.wi/models.md`

Project-level, persisted, read at every dispatch point. Template (fill from a preset, then let the user
override any cell):

```markdown
---
type: Model Routing Config
title: Model assignments — <project>
description: Per-role model assignments for wi-dispatched agents (preset: smart | simple | custom).
preset: <smart | simple | custom>
timestamp: <YYYY-MM-DD>
---

# Model assignments

## Roles
| Role | Model | Notes |
|------|-------|-------|
| orchestrator | <fable\|opus\|sonnet\|haiku> | informational — session model, set via /model; wi warns on mismatch |
| wi-code-checker | <fable\|opus\|sonnet\|haiku\|inherit> | the checker's Claude dispatch tier — never below orchestrator's tier |
| wi-researcher | <fable\|opus\|sonnet\|haiku\|inherit> | one Claude tier below orchestrator |
| wi-task-runner | <opus\|sonnet\|haiku\|inherit> | default for every wi-task-runner dispatch |

## Cross-provider config
| Key | Value |
|-----|-------|
| provider | <openai \| anthropic \| none> |
| base_url | <https://api.openai.com/v1> |
| model | <gpt-5> |
| api_key_env | <OPENAI_API_KEY> |
| check_points | <at-finish \| per-wave> |

## Per-agent overrides
| Agent | Model |
|-------|-------|
| <wi-researcher \| wi-task-runner \| wi-code-checker \| rpa-build> | <tier> |
```

Claude tiers are the Agent-dispatch tokens `fable | opus | sonnet | haiku`, plus `inherit` (= the session
model). The cross-provider model is the *provider's* model id, independent of the Claude tier tokens.

## Presets

| Role | **smart** | **simple** |
|------|-----------|------------|
| orchestrator | fable | opus |
| wi-code-checker | fable | opus |
| wi-researcher | opus | sonnet |
| wi-task-runner | opus | sonnet |
| cross-provider | gpt-5 (openai) | none |

Each role's default follows a rule, not an arbitrary pick:

- **`wi-code-checker`** dispatches at this same-family Claude tier and is **never weaker than the orchestrator** —
  smart's orchestrator is already top-tier (`fable`), so checker matches it there; simple's orchestrator
  is `opus`, so checker matches that (not a downgrade to `sonnet`/`haiku`). Verification is the one place
  not to cut corners. The floor is the **configured** orchestrator tier, never the live session model —
  a top-tier session over the simple preset still dispatches the checker at `opus`, by design (pricing;
  see the no-auto-escalation rule above).
- **`wi-researcher`** is one Claude tier below the orchestrator (`fable→opus→sonnet→haiku`, floor at
  `haiku`) — cheaper exploratory work doesn't need the top tier.
- **`wi-task-runner`** scales with the preset directly (smart → `opus`, simple → `sonnet`) — it's the
  highest-volume dispatch (one per plan task), so its cost profile should track the preset's overall
  intent.

**smart** = top-tier checker + strong researcher/task-runner + cross-architecture check — the only preset
that reaches **above `opus`**, and it is never a default: it must be chosen interactively (or written by
hand). **simple** = the `opus`/`sonnet` lean pass-through, no cross-provider check — the `--auto` default;
its ceiling is `opus` **by design** (pricing — top tiers are never a default anywhere in wi). Presets only
*pre-fill* the table — every cell stays individually overridable (a hand-written override may name any
tier, including `fable`).

## First-run setup (dev / rpa entry points)

When `.wi/models.md` is **absent** at a wi entry skill (dev step 1, rpa step 2): **interactive** → ask once
— *"Model routing: smart, simple, or custom?"* — pre-fill from the chosen preset (`wi-researcher`'s literal
is computed once as one tier below the chosen orchestrator tier), confirm the per-role rows (and any
per-agent override), write the file **and commit it** (`chore(wi): models config` — the project-level rule
in `wi-directory.md`: committed where written, so post-worktree phases read the same tracked copy).
**`--auto`** → write + commit the **simple** preset and log it as an
assumption. Either way the file persists and is **never re-asked** (edit `.wi/models.md` to change it). When
the file exists, skip setup entirely — just apply it. The entry skills also handle the legacy migration: a
pre-1.3 config under the old filename is renamed to `.wi/models.md` with its frontmatter set to
`type: Model Routing Config` — the section format is unchanged.

## Dispatch rule (build, research, ship, rpa)

At every wi Agent dispatch, resolve the model as **per-agent override → the agent's own role → `inherit`**
(`wi-code-checker` reads the `wi-code-checker` role, `wi-researcher` reads `wi-researcher`, `wi-task-runner`
reads `wi-task-runner`; RPA build delegations resolve `rpa-build` override → `wi-task-runner` role →
`inherit` — `rpa-build` is a **role label** for those delegations, not a registered agent; there is no
`agents/rpa-build.md`) and pass it as the dispatch's model parameter. No `.wi/models.md` → everything
inherits, exactly wi's pre-routing behavior. **Fallback:** a configured model that errors as unavailable at
dispatch time → re-dispatch with `inherit` and note it in `progress.md`; never stall a run on a model
assignment.

## wi-code-checker's two modes

`wi-code-checker` (`agents/wi-code-checker.md`) always runs **twice per feature** — plan mode before the
design gate, result mode before shipping — and both are Agent-tool dispatches at the `wi-code-checker`
role's Claude tier:

- **PLAN mode** (pre-gate, before a diff exists — verifies spec/task coverage). There's no diff yet to
  hand a cross-provider script, so this mode is same-family only.
- **RESULT mode** (at ship): confirms every acceptance criterion + locked decision is delivered and
  **wired**, refreshing `verification.md`. When a cross-provider is configured, the independent diff review
  described next runs **beside** this dispatch — never instead of it — and when `check_points: per-wave`,
  that diff-review layer additionally runs at each build wave-end gate over the wave's diff (the checker
  itself still runs twice per feature).

### The cross-provider diff review (a layer beside wi-code-checker's result mode)

Not a per-tool-call interceptor (running every reviewer role cross-provider was rejected as cost-prohibitive; only this independent cross-provider layer at ship survived): it's an
**independent third-party line-level review of the finished diff**, run by ship §2 conceptually beside its
self-review — and, when `check_points: per-wave`, additionally at each build wave-end gate over that
wave's diff. The point is **model diversity**: the checker itself is Claude-family (subagents can only run
Claude models); this script is how another model family gets a look at the diff. It is a different check,
not a substitute — the script only receives the diff + spec text (no Read/Grep/Bash against the repo), so
it cannot verify things are actually wired, and it does not write `verification.md`. Mechanics:

1. Produce the diff (`git diff <base>...HEAD` for at-finish; the wave's commits for per-wave) to a temp
   file, plus context: `spec.md` (or the SDD's acceptance-criteria section) and the relevant
   constitution rules.
2. Run `python ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/cross_review.py --config .wi/models.md
   --diff <patch> --context <spec> --out .wi/features/<slug>/cross-review.md` (`python` assumed on PATH; where it
   does not resolve, fall back to `py -3` on Windows or `python3` on Linux/macOS).
3. Exit `0` = `## REVIEW PASSED`; `1` = `## ISSUES FOUND` — treat findings like any checker finding:
   BLOCKER → fix (loop back to build), WARNING/INFO → address or record. Both layers share the **max 2
   review→fix rounds** budget; whatever remains after round 2 is surfaced, with
   severity, in `PR.md`'s Verification section. `3` = no API key in `api_key_env` and `2` = config or API
   error govern only whether **this layer** runs — log `cross-provider layer skipped (<reason>)` and
   continue; wi-code-checker's result-mode dispatch is unconditional and runs regardless. The
   cross-provider script works alone — the orchestrator hands it the diff and takes back findings; it does
   not steer the review.
4. `cross-review.md` is **ephemeral** like `verification.md`: ship §5 distills the verdict into `PR.md`,
   then the dossier tidy (§6) prunes both.

The cross-provider review is a standalone layer: it needs only the `## Cross-provider config` section and
works even when every role is `inherit` (no tier routing in use). The escalation contract in
`agents/wi-task-runner.md` — architectural decisions stop and ask the orchestrator — is likewise
independent of this file.

`Cross-provider config` `provider: none` (simple preset) → skip the script entirely; RESULT mode still
dispatches `wi-code-checker` at its Roles-table tier, same as PLAN mode — the cross-provider path is a
layer on top of checker, never a replacement.
