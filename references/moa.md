---
type: Reference
title: "MoA — tiered model assignments for wi's dispatched agents"
description: "Configurable Mixture-of-Agents: each wi-dispatched sub-agent (wi-code-checker, wi-researcher, wi-task-runner) gets its own tiered default, with wi-code-checker running an independent cross-provider check at result time when a second provider is configured. Config in .wi/moa.md, set up on first run."
timestamp: 2026-07-02
tags: [moa, models, reference]
---

# MoA — tiered model assignments for wi's dispatched agents

wi dispatches three kinds of sub-agents — **wi-researcher**, **wi-task-runner**, **wi-code-checker** — plus
the **orchestrator**, which is just the session itself (the agent reading this file, planning and routing
the run). MoA lets a project tune what each of the three sub-agents runs on, and gives wi-code-checker an
**independent cross-provider check** — ideally a *different provider/architecture* (different training,
different blind spots) — for its result-mode verification. Scope: **wi-dispatched agents only**
(wi-researcher, wi-task-runner, wi-code-checker, RPA build delegations); wi never re-models other plugins'
or the user's own agents.

**The orchestrator model is informational.** A plugin cannot set the session model — the user picks it
with `/model`. wi records the intended tier and, at run start, **warns once** if the session model is
below it (e.g. config says `fable`, session runs `haiku`); it never blocks.

## The config file — `.wi/moa.md`

Project-level, persisted, read at every dispatch point. Template (fill from a preset, then let the user
override any cell):

```markdown
---
type: MoA Config
title: MoA model assignments — <project>
description: Per-role model assignments for wi-dispatched agents (preset: smart | simple | custom).
preset: <smart | simple | custom>
timestamp: <YYYY-MM-DD>
---

# MoA model assignments

## Roles
| Role | Model | Notes |
|------|-------|-------|
| orchestrator | <fable\|opus\|sonnet\|haiku> | informational — session model, set via /model; wi warns on mismatch |
| wi-code-checker | <fable\|opus\|sonnet\|haiku\|inherit> | same-family fallback tier — never below orchestrator's tier |
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

- **`wi-code-checker`** is the same-family fallback tier and is **never weaker than the orchestrator** —
  smart's orchestrator is already top-tier (`fable`), so checker matches it there; simple's orchestrator
  is `opus`, so checker matches that (not a downgrade to `sonnet`/`haiku`). Verification is the one place
  not to cut corners.
- **`wi-researcher`** is one Claude tier below the orchestrator (`fable→opus→sonnet→haiku`, floor at
  `haiku`) — cheaper exploratory work doesn't need the top tier.
- **`wi-task-runner`** scales with the preset directly (smart → `opus`, simple → `sonnet`) — it's the
  highest-volume dispatch (one per plan task), so its cost profile should track the preset's overall
  intent.

**smart** = top-tier checker + strong researcher/task-runner + cross-architecture check. **simple** = lean
pass-through, no cross-provider check. Presets only *pre-fill* the table — every cell stays individually
overridable.

## First-run setup (dev / rpa entry points)

When `.wi/moa.md` is **absent** at a wi entry skill (dev step 2, rpa step 2): **interactive** → ask once
— *"MoA models: smart, simple, or custom?"* — pre-fill from the chosen preset (`wi-researcher`'s literal
is computed once as one tier below the chosen orchestrator tier), confirm the per-role rows (and any
per-agent override), write the file. **`--auto`** → write the **simple** preset and log it as an
assumption. Either way the file persists and is **never re-asked** (edit `.wi/moa.md` to change it). When
the file exists, skip setup entirely — just apply it.

## Dispatch rule (build, research, ship, rpa)

At every wi Agent dispatch, resolve the model as **per-agent override → the agent's own role → `inherit`**
(`wi-code-checker` reads the `wi-code-checker` role, `wi-researcher` reads `wi-researcher`, `wi-task-runner`
reads `wi-task-runner`) and pass it as the dispatch's model parameter. No `.wi/moa.md` → everything
inherits, exactly wi's pre-MoA behavior. **Fallback:** a configured model that errors as unavailable at
dispatch time → re-dispatch with `inherit` and note it in `progress.md`; never stall a run on a model
assignment.

## wi-code-checker's two modes

`wi-code-checker` (`agents/wi-code-checker.md`) runs in two modes, and only one of them can go
cross-provider:

- **PLAN mode** (pre-gate, before a diff exists — verifies spec/task coverage): always dispatched via the
  Agent tool at the `wi-code-checker` role's Claude tier. There's no diff yet to hand a cross-provider
  script, so this mode is same-family only.
- **RESULT mode** (ship, and — when `check_points: per-wave` — each build wave-end gate): this is where the
  independent cross-provider check happens, described next.

### The cross-provider check (wi-code-checker's result-mode path)

Not a per-tool-call interceptor (rejected as cost-prohibitive — see issue #12's scope revision): it's an
**independent third-party review of the finished work**, run by ship §2 — and, when
`check_points: per-wave`, additionally at each build wave-end gate over that wave's diff. Mechanics:

1. Produce the diff (`git diff <base>...HEAD` for at-finish; the wave's commits for per-wave) to a temp
   file, plus context: `spec.md` (or `sdd.md` §13) and the relevant constitution rules.
2. Run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/moa_review.py --config .wi/moa.md
   --diff <patch> --context <spec> --out .wi/goals/<slug>/moa-review.md`.
3. Exit `0` = `## REVIEW PASSED`; `1` = `## ISSUES FOUND` — treat findings like any checker finding:
   BLOCKER → fix (loop back to build), WARNING/INFO → address or record. **Max 2 review→fix rounds**
   (the issue's revision cap); whatever remains after round 2 is surfaced, with severity, in `PR.md`'s
   Verification section. `3` = no API key in `api_key_env` → **fall back** to dispatching
   `wi-code-checker` at its Roles-table tier with the same review charter (log `checker cross-provider via
   fallback (<reason>)`); `2` = config or API error → same fallback. The cross-provider script works
   alone — the orchestrator hands it the diff and takes back findings; it does not steer the review.
4. `moa-review.md` is **ephemeral** like `verification.md`: distill the verdict into `PR.md`, prune at
   close-out.

`Cross-provider config` `provider: none` (simple preset) → skip the script entirely; RESULT mode still
dispatches `wi-code-checker` at its Roles-table tier, same as PLAN mode — the cross-provider path is a
layer on top of checker, never a replacement.
