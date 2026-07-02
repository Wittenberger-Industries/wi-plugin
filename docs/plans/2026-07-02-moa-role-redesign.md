# MoA role redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename `.wi/moa.md`'s confusing `orchestrator`/`execution`/`checker`/`reviewer` roles to the
three real dispatch targets (`wi-code-checker`, `wi-researcher`, `wi-task-runner`), fold the standalone
cross-provider "reviewer" into `wi-code-checker`'s own result-mode path, and give every role tier a
non-arbitrary default.

**Architecture:** `skills/ship/scripts/moa_review.py` is the single source of truth for parsing
`.wi/moa.md` and resolving a dispatch's model (`model_for`) — it is stdlib-only, unit-tested, and imported
by nothing else at runtime (skills describe its contract in prose, they don't import it). Every other
touch point is documentation: `references/moa.md` (the schema + presets + dispatch rule), and five
`skills/*/SKILL.md` files that describe *when* to call `model_for` and what role name to pass. Rename the
schema in `moa_review.py` + its tests first (that's the only code with a test suite), then propagate the
new names through the docs.

**Tech Stack:** Python 3 stdlib (`unittest`), Markdown/OKF frontmatter docs.

## Global Constraints

- No back-compat parsing of the old `execution`/`checker`/`reviewer` schema — clean break (spec
  Non-goals/Migration; `docs/specs/2026-07-02-moa-role-redesign-design.md`).
- Do not change cross-provider call mechanics (`_call_openai`/`_call_anthropic`, exit codes 0/1/2/3, the
  BLOCKER/WARNING/INFO fallback ladder, the 2-round cap) — only the config names/keys that route to them.
- Test runner in this repo: `python -m unittest tests.test_moa_config -v` (no pytest installed).
- Every edited `.md`/`.py` file keeps its existing line-wrap style (~95-100 col soft wrap for the skill
  docs) — match surrounding paragraphs, don't reflow unrelated lines.
- Commit after each task (small, reviewable diffs) with a `<type>(moa): <subject>` message.

---

### Task 1: Rename the schema in `moa_review.py` + `tests/test_moa_config.py`

**Files:**
- Modify: `skills/ship/scripts/moa_review.py`
- Modify: `tests/test_moa_config.py`

**Interfaces:**
- Produces: `parse_moa_config(text) -> {"preset", "roles", "cross_provider", "overrides"}` — key
  `reviewer_provider` renamed `cross_provider`. `cross_provider_configured(cfg) -> bool` (was
  `reviewer_enabled`). `model_for(agent, cfg) -> str` — now a flat `overrides → roles[agent] → "inherit"`
  lookup (no more `wi-code-checker`/`checker` special-case; bare `"checker"` alias dropped).
- Consumes: nothing from other tasks — this is the base layer everything else's prose describes.

- [ ] **Step 1: Update the test fixtures and write the new-schema assertions (still failing)**

Replace the full contents of `tests/test_moa_config.py` with:

```python
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "ship" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import moa_review  # noqa: E402


FULL_CONFIG = """---
type: MoA Config
title: MoA model assignments — demo
description: Per-role model assignments for wi-dispatched agents.
preset: smart
timestamp: 2026-07-02
---

# MoA model assignments

## Roles
| Role | Model | Notes |
|------|-------|-------|
| orchestrator | fable | informational — session model |
| wi-code-checker | fable | same-family fallback tier |
| wi-researcher | opus | one tier below orchestrator |
| wi-task-runner | sonnet | default for wi-task-runner dispatches |

## Cross-provider config
| Key | Value |
|-----|-------|
| provider | openai |
| base_url | https://api.openai.com/v1 |
| model | gpt-5 |
| api_key_env | OPENAI_API_KEY |
| check_points | at-finish |

## Per-agent overrides
| Agent | Model |
|-------|-------|
| wi-researcher | haiku |
"""

SIMPLE_CONFIG = """---
type: MoA Config
title: MoA model assignments — demo
description: Per-role model assignments for wi-dispatched agents.
preset: simple
timestamp: 2026-07-02
---

# MoA model assignments

## Roles
| Role | Model | Notes |
|------|-------|-------|
| orchestrator | opus | informational |
| wi-code-checker | opus | matches orchestrator tier |
| wi-researcher | sonnet | one tier below orchestrator |
| wi-task-runner | sonnet | default |

## Cross-provider config
| Key | Value |
|-----|-------|
| provider | none |
"""


class ParseConfigTest(unittest.TestCase):
    def test_roles_parsed(self):
        cfg = moa_review.parse_moa_config(FULL_CONFIG)
        self.assertEqual(cfg["preset"], "smart")
        self.assertEqual(cfg["roles"]["orchestrator"], "fable")
        self.assertEqual(cfg["roles"]["wi-code-checker"], "fable")
        self.assertEqual(cfg["roles"]["wi-researcher"], "opus")
        self.assertEqual(cfg["roles"]["wi-task-runner"], "sonnet")

    def test_cross_provider_parsed(self):
        cfg = moa_review.parse_moa_config(FULL_CONFIG)
        cp = cfg["cross_provider"]
        self.assertEqual(cp["provider"], "openai")
        self.assertEqual(cp["base_url"], "https://api.openai.com/v1")
        self.assertEqual(cp["model"], "gpt-5")
        self.assertEqual(cp["api_key_env"], "OPENAI_API_KEY")
        self.assertEqual(cp["check_points"], "at-finish")

    def test_overrides_parsed(self):
        cfg = moa_review.parse_moa_config(FULL_CONFIG)
        self.assertEqual(cfg["overrides"]["wi-researcher"], "haiku")

    def test_provider_none_means_disabled(self):
        cfg = moa_review.parse_moa_config(SIMPLE_CONFIG)
        self.assertEqual(cfg["cross_provider"]["provider"], "none")
        self.assertFalse(moa_review.cross_provider_configured(cfg))

    def test_cross_provider_configured_with_provider(self):
        cfg = moa_review.parse_moa_config(FULL_CONFIG)
        self.assertTrue(moa_review.cross_provider_configured(cfg))

    def test_missing_sections_default(self):
        cfg = moa_review.parse_moa_config(SIMPLE_CONFIG)
        self.assertEqual(cfg["overrides"], {})
        # provider defaults exist even when api_key_env/model/base_url rows are absent
        self.assertEqual(cfg["cross_provider"]["api_key_env"], "OPENAI_API_KEY")


class ModelForTest(unittest.TestCase):
    def test_override_beats_role(self):
        cfg = moa_review.parse_moa_config(FULL_CONFIG)
        self.assertEqual(moa_review.model_for("wi-researcher", cfg), "haiku")

    def test_task_runner_uses_its_own_role(self):
        cfg = moa_review.parse_moa_config(FULL_CONFIG)
        self.assertEqual(moa_review.model_for("wi-task-runner", cfg), "sonnet")

    def test_checker_uses_its_own_role(self):
        cfg = moa_review.parse_moa_config(FULL_CONFIG)
        self.assertEqual(moa_review.model_for("wi-code-checker", cfg), "fable")

    def test_unknown_agent_inherits(self):
        cfg = moa_review.parse_moa_config(FULL_CONFIG)
        self.assertEqual(moa_review.model_for("some-other-agent", cfg), "inherit")

    def test_no_config_inherits(self):
        self.assertEqual(moa_review.model_for("wi-task-runner", None), "inherit")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to confirm they fail against the old `moa_review.py`**

Run: `python -m unittest tests.test_moa_config -v`
Expected: multiple `FAIL`/`ERROR` — `KeyError: 'cross_provider'`, `AttributeError:
module 'moa_review' has no attribute 'cross_provider_configured'`, and `model_for` mismatches (old code
still keys `roles` by `execution`/`checker`, not `wi-code-checker`/`wi-researcher`/`wi-task-runner`).

- [ ] **Step 3: Rewrite `moa_review.py`'s config surface to the new schema**

Apply these edits to `skills/ship/scripts/moa_review.py`:

Module docstring (lines 2-7) — update "reviewer" framing to "checker":
```python
"""MoA cross-provider check — wi-code-checker's result-mode independent review (issue #12).

Reads the goal project's `.wi/moa.md` (the MoA model-assignment config), and — when a second
provider is configured — sends the diff + spec context to that model, possibly a different
provider/architecture than the session (e.g. GPT via OPENAI_API_KEY), as wi-code-checker's
result-mode check. Writes the findings to a file. Stdlib only; no third-party deps.
```

`PROVIDER_DEFAULTS` (lines 29-35) — rename key `review_points` → `check_points`:
```python
PROVIDER_DEFAULTS = {
    "provider": "openai",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-5",
    "api_key_env": "OPENAI_API_KEY",
    "check_points": "at-finish",
}
```

`parse_moa_config` (lines 71-103) — read `## Cross-provider config` instead of `## Reviewer provider`,
return key `cross_provider` instead of `reviewer_provider`:
```python
def parse_moa_config(text):
    """Parse `.wi/moa.md` into {preset, roles, cross_provider, overrides}."""
    preset = "custom"
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            body = parts[2]
            m = re.search(r"^preset:\s*(\S+)", parts[1], re.MULTILINE)
            if m:
                preset = m.group(1)

    roles = {}
    for cells in _parse_table(_section(body, "Roles")):
        if len(cells) >= 2:
            roles[cells[0].strip("*` ")] = cells[1].strip("*` ")

    provider = dict(PROVIDER_DEFAULTS)
    for cells in _parse_table(_section(body, "Cross-provider config")):
        if len(cells) >= 2 and cells[1]:
            provider[cells[0].strip("*` ")] = cells[1].strip("*` ")

    overrides = {}
    for cells in _parse_table(_section(body, "Per-agent overrides")):
        if len(cells) >= 2:
            overrides[cells[0].strip("*` ")] = cells[1].strip("*` ")

    return {
        "preset": preset,
        "roles": roles,
        "cross_provider": provider,
        "overrides": overrides,
    }
```

`reviewer_enabled` → `cross_provider_configured` (lines 106-109), read the new key:
```python
def cross_provider_configured(cfg):
    """wi-code-checker's cross-provider result-mode path runs only when a provider is named."""
    provider = (cfg or {}).get("cross_provider", {}).get("provider", "none")
    return provider not in ("", "none", "off", "disabled")
```

`model_for` (lines 112-121) — flat role lookup, no more checker special-case:
```python
def model_for(agent, cfg):
    """Model for a wi-dispatched agent: per-agent override > its own role > inherit."""
    if not cfg:
        return "inherit"
    if agent in cfg.get("overrides", {}):
        return cfg["overrides"][agent]
    return cfg.get("roles", {}).get(agent, "inherit")
```

`run_review` (line 169-170) and `main` (lines 213-215) — update the two remaining
`reviewer_provider`/`reviewer_enabled` references:
```python
def run_review(cfg, diff_text, context_blobs, out_path):
    provider = cfg["cross_provider"]
    ...
```
```python
    if not cross_provider_configured(cfg):
        print("moa_review: cross-provider not configured — nothing to run", file=sys.stderr)
        return 2
```

Leave `_call_openai`, `_call_anthropic`, `REVIEW_SYSTEM_PROMPT`, exit codes, and `argparse` setup
untouched — only the config-surface names change.

- [ ] **Step 4: Run the tests to confirm they pass**

Run: `python -m unittest tests.test_moa_config -v`
Expected: `Ran 11 tests in ...s` / `OK`

- [ ] **Step 5: Commit**

```bash
git add skills/ship/scripts/moa_review.py tests/test_moa_config.py
git commit -m "refactor(moa): rename config schema to wi-code-checker/wi-researcher/wi-task-runner roles"
```

---

### Task 2: Rewrite `references/moa.md`

**Files:**
- Modify: `references/moa.md` (full rewrite of the body — frontmatter `timestamp` bumps to today)

**Interfaces:**
- Consumes: the schema names finalized in Task 1 (`Roles` rows `orchestrator`/`wi-code-checker`/
  `wi-researcher`/`wi-task-runner`; `## Cross-provider config` with `check_points`).
- Produces: the canonical spec every `SKILL.md` in Tasks 3-6 links back to.

- [ ] **Step 1: Replace `references/moa.md` in full**

Write the complete file as:

```markdown
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
```

- [ ] **Step 2: Diff-read the new file against the design spec to confirm parity**

Run: `git diff --stat references/moa.md` (should show the file changed, no unrelated files touched) and
re-read `docs/specs/2026-07-02-moa-role-redesign-design.md` Design §1-§3 side by side with the new
`references/moa.md` — confirm the Roles table, preset table, and Cross-provider config section match the
spec exactly (role names, tier values, `check_points` key name).

- [ ] **Step 3: Commit**

```bash
git add references/moa.md
git commit -m "docs(moa): rewrite role table to wi-code-checker/wi-researcher/wi-task-runner"
```

---

### Task 3: Update `skills/research/SKILL.md`'s researcher dispatch line

**Files:**
- Modify: `skills/research/SKILL.md:59-60`

**Interfaces:**
- Consumes: `references/moa.md`'s dispatch rule from Task 2 (per-agent override → agent's own role →
  inherit).

- [ ] **Step 1: Edit the dispatch sentence**

In `skills/research/SKILL.md`, replace (currently lines 59-60):

```
`repo-map.md` + any relevant learning. One small question = one researcher; never fan out for the sake
of it. When `.wi/moa.md` exists, dispatch each researcher on its MoA model (override `wi-researcher` →
`execution` role → inherit; `${CLAUDE_PLUGIN_ROOT}/references/moa.md`).
```

with:

```
`repo-map.md` + any relevant learning. One small question = one researcher; never fan out for the sake
of it. When `.wi/moa.md` exists, dispatch each researcher on its MoA model (override → `wi-researcher`
role → inherit; `${CLAUDE_PLUGIN_ROOT}/references/moa.md`).
```

- [ ] **Step 2: Confirm no other MoA role references remain in this file**

Run: `grep -n "execution\|reviewer\|MoA" skills/research/SKILL.md`
Expected: only the line just edited (now reading `wi-researcher` role) and any unrelated hits (there are
none today per the earlier repo-wide grep).

- [ ] **Step 3: Commit**

```bash
git add skills/research/SKILL.md
git commit -m "docs(research): use wi-researcher role name in MoA dispatch line"
```

---

### Task 4: Update `skills/build/SKILL.md`'s task-runner dispatch + per-wave check wording

**Files:**
- Modify: `skills/build/SKILL.md:48-51` and `skills/build/SKILL.md:76-79`

**Interfaces:**
- Consumes: `references/moa.md`'s dispatch rule and `check_points` key from Task 2.

- [ ] **Step 1: Edit the task-runner dispatch sentence (lines 48-51)**

Replace:

```
   relevant constitution rules, and the repo commands. Fresh agents keep context from rotting across a
   long build; parallel dispatch keeps wall-clock short. **Model per dispatch (MoA):** when `.wi/moa.md`
   exists, resolve each runner's model as per-agent override → `execution` role → `inherit`
   (`${CLAUDE_PLUGIN_ROOT}/references/moa.md`) and pass it on the dispatch; a model that errors as
   unavailable → re-dispatch on `inherit` and note it in `progress.md`. No config → inherit, as always.
```

with:

```
   relevant constitution rules, and the repo commands. Fresh agents keep context from rotting across a
   long build; parallel dispatch keeps wall-clock short. **Model per dispatch (MoA):** when `.wi/moa.md`
   exists, resolve each runner's model as per-agent override → `wi-task-runner` role → `inherit`
   (`${CLAUDE_PLUGIN_ROOT}/references/moa.md`) and pass it on the dispatch; a model that errors as
   unavailable → re-dispatch on `inherit` and note it in `progress.md`. No config → inherit, as always.
```

- [ ] **Step 2: Edit the per-wave cross-provider check sentence (lines 76-79)**

Replace:

```
Two scheduling refinements proven in dry runs: (a) **wave-end gate** — at each wave boundary run the full
lint + test commands once, serially, before dispatching the next wave — and when `.wi/moa.md` sets
`review_points: per-wave`, also run the **MoA review** over the wave's diff there
(`${CLAUDE_PLUGIN_ROOT}/references/moa.md`, same bounded 2-round loop as at ship); (b) **sole-runner exception** —
```

with:

```
Two scheduling refinements proven in dry runs: (a) **wave-end gate** — at each wave boundary run the full
lint + test commands once, serially, before dispatching the next wave — and when `.wi/moa.md` sets
`check_points: per-wave`, also run **wi-code-checker's cross-provider check** over the wave's diff there
(`${CLAUDE_PLUGIN_ROOT}/references/moa.md`, same bounded 2-round loop as at ship); (b) **sole-runner exception** —
```

- [ ] **Step 3: Confirm no stale references remain**

Run: `grep -n "execution\` role\|review_points\|MoA review" skills/build/SKILL.md`
Expected: no matches.

- [ ] **Step 4: Commit**

```bash
git add skills/build/SKILL.md
git commit -m "docs(build): use wi-task-runner role name and check_points key in MoA wording"
```

---

### Task 5: Restructure `skills/ship/SKILL.md`'s MoA sections into one wi-code-checker section

**Files:**
- Modify: `skills/ship/SKILL.md:43-59`

**Interfaces:**
- Consumes: Task 2's merged PLAN/RESULT-mode contract (`references/moa.md` "wi-code-checker's two modes").

- [ ] **Step 1: Replace the two separate subsections with one merged section**

In `skills/ship/SKILL.md`, replace (currently lines 43-59, the `**MoA review (independent,
cross-provider).**` paragraph through the `**Goal-level check (checker · result mode).**` paragraph,
ending before `Address findings before proceeding; note anything deliberately deferred.`):

```
**MoA review (independent, cross-provider).** If `.wi/moa.md` names a reviewer (role ≠ `none`), run the
independent review per `${CLAUDE_PLUGIN_ROOT}/references/moa.md`: full goal diff + `spec.md` through
`skills/ship/scripts/moa_review.py` → `.wi/goals/<slug>/moa-review.md`. Findings are handled like checker
findings — BLOCKER loops back to build, **max 2 review→fix rounds**, whatever remains goes with its
severity into `PR.md`'s Verification. Exit 3 (no API key) or 2 (config/API error) → **fall back** to a
checker-tier Claude agent with the same review charter and log `moa review via fallback (<reason>)`. This
is a layer on top of the reviews above, never a replacement; `moa-review.md` is ephemeral (pruned in §5).

**Goal-level check (checker · result mode).** Dispatch the **checker** (`agents/wi-code-checker.md`) in `result`
mode — on the `checker` role's model when `.wi/moa.md` exists —
against `spec.md`'s acceptance criteria + locked decisions (ADRs, constitution); it confirms each is
delivered and **wired**, not just present, refreshing `verification.md`. This is goal/coverage-level,
distinct from the line-level review above. A result-mode **BLOCKER** — an unmet criterion, or a decision
silently reduced to a stub — sends the goal **back to build**; ship never opens the PR on a goal the
checker says isn't met.
```

with:

```
**Goal-level check (wi-code-checker · result mode).** Dispatch **wi-code-checker**
(`agents/wi-code-checker.md`) in `result` mode against `spec.md`'s acceptance criteria + locked decisions
(ADRs, constitution); it confirms each is delivered and **wired**, not just present, refreshing
`verification.md`. If `.wi/moa.md`'s `## Cross-provider config` names a provider (≠ `none`) and its API
key is present, this pass runs as an **independent cross-provider check** per
`${CLAUDE_PLUGIN_ROOT}/references/moa.md`: full goal diff + `spec.md` through
`skills/ship/scripts/moa_review.py` → `.wi/goals/<slug>/moa-review.md`. Otherwise (unconfigured, or exit 2
config/API error, or exit 3 missing API key) it falls back to dispatching `wi-code-checker` on the
`wi-code-checker` role's model — log `checker cross-provider via fallback (<reason>)` when that fallback
fires. Findings are handled uniformly: BLOCKER — an unmet criterion, a decision silently reduced to a
stub — sends the goal **back to build**, **max 2 review→fix rounds**; whatever remains goes with its
severity into `PR.md`'s Verification. `moa-review.md` is ephemeral (pruned in §5). Ship never opens the PR
on a goal wi-code-checker says isn't met.
```

- [ ] **Step 2: Confirm no stale role/section names remain**

Run: `grep -n "reviewer\|\`checker\` role\|checker-tier" skills/ship/SKILL.md`
Expected: no matches (the merged paragraph above uses `wi-code-checker` throughout).

- [ ] **Step 3: Re-read the file's §5 pruning line to confirm it still matches**

Read `skills/ship/SKILL.md` around line 149 (`**the MoA reviewer's `moa-review.md`**, **and the checker's
`verification.md`**`) — this line already names the two files by filename, not role, so it needs no edit;
just confirm it still reads correctly next to the rewritten §2 section (no dangling "the MoA reviewer"
noun phrase implying a separate agent). If it does read as implying a separate agent, adjust it to `**the
cross-provider check's `moa-review.md`**, **and wi-code-checker's `verification.md`**` for consistency.

- [ ] **Step 4: Commit**

```bash
git add skills/ship/SKILL.md
git commit -m "docs(ship): merge MoA reviewer into wi-code-checker's result-mode section"
```

---

### Task 6: Update `skills/rpa/SKILL.md`'s MoA wording

**Files:**
- Modify: `skills/rpa/SKILL.md:40-43`

**Interfaces:**
- Consumes: Task 2's role names (`wi-task-runner`, `wi-code-checker`'s cross-provider check).

- [ ] **Step 1: Edit the first-run-setup paragraph**

Replace (currently lines 40-43):

```
   supporting files in the repo (API refs, CSV/mapping tables, sample data, screenshots) into
   `.wi/inputs.md`; detect reusable components into `.wi/components.md`; convert the PDD to `pdd.md` with
   markitdown (skip if it's already Markdown). Run the **MoA first-run setup** here too
   (`${CLAUDE_PLUGIN_ROOT}/references/moa.md`): `.wi/moa.md` absent → one preset question (`--auto` →
   simple preset, logged); present → apply, warn once on an orchestrator-tier mismatch. The config's
   execution tier then rides every build delegation (agent `rpa-build`) and the ship-phase MoA review.
```

with:

```
   supporting files in the repo (API refs, CSV/mapping tables, sample data, screenshots) into
   `.wi/inputs.md`; detect reusable components into `.wi/components.md`; convert the PDD to `pdd.md` with
   markitdown (skip if it's already Markdown). Run the **MoA first-run setup** here too
   (`${CLAUDE_PLUGIN_ROOT}/references/moa.md`): `.wi/moa.md` absent → one preset question (`--auto` →
   simple preset, logged); present → apply, warn once on an orchestrator-tier mismatch. The config's
   `wi-task-runner` tier then rides every build delegation (agent `rpa-build`) and wi-code-checker runs its
   ship-phase cross-provider check per the same rules as `wi:ship`.
```

- [ ] **Step 2: Confirm no stale references remain**

Run: `grep -n "execution tier\|MoA review" skills/rpa/SKILL.md`
Expected: no matches.

- [ ] **Step 3: Commit**

```bash
git add skills/rpa/SKILL.md
git commit -m "docs(rpa): use wi-task-runner role name and wi-code-checker cross-provider wording"
```

---

### Task 7: Full-repo verification sweep

**Files:**
- None modified — verification only.

**Interfaces:**
- Consumes: the completed state of Tasks 1-6.

- [ ] **Step 1: Run the full test suite**

Run: `python -m unittest discover -s tests -v 2>&1 | tail -40`
Expected: all tests pass, including the 11 in `test_moa_config.py` from Task 1.

- [ ] **Step 2: Repo-wide grep for anything still using the old schema**

Run:
```bash
grep -rn "execution.*role\|\`checker\` role\|Reviewer provider\|review_points\|reviewer_provider\|reviewer_enabled" skills/ agents/ references/ tests/ --include="*.md" --include="*.py"
```
Expected: no output. If anything matches, fix that file with the same rename pattern used in its task
above before proceeding (do not leave a stray old-schema reference).

- [ ] **Step 3: Validate `references/moa.md` and `docs/specs/2026-07-02-moa-role-redesign-design.md` agree**

Read both files side by side one more time — Roles table values, preset table values, and the
`Cross-provider config` field names must match exactly between the spec and the reference doc (the spec is
frozen intent; the reference doc is what agents actually follow — a mismatch here is a plan bug, not a
future cleanup).

- [ ] **Step 4: Final commit (only if Step 2 required fixes; otherwise skip — nothing to commit)**

```bash
git add -A
git commit -m "docs(moa): fix remaining old-schema references"
```
