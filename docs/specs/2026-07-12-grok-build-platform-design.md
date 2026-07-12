---
type: Design Spec
title: "Grok Build as the fourth wi platform adapter (#43)"
description: "Design for adding Grok Build (grok CLI, grok-4.5) as wi's fourth harness via the thin-adapter pattern: a grok-tools.md capability map with a mandatory plugin-root resolution protocol, a third model-judged keep-alive branch, a platform model resolution layer plus xAI cross-provider in models.md, additive spine pointers, validate.py hard checks, and a blocking live recon spike plus scan+dev E2E merge gate. Additive-only to the Claude/Codex/Copilot branches; MoA cross-vendor (#34) and rpa stay out of scope."
status: accepted
timestamp: 2026-07-12
tags: [grok, platform, portability, keep-alive, models, spec]
---

# Grok Build as the fourth wi platform adapter (#43)

## Summary

wi runs from one source on three harnesses today: Claude Code (native), Codex CLI, and Copilot CLI. Each
non-Claude harness is supported by a thin, uniform adapter: a tool/capability map, a keep-alive branch, an
`AGENTS.md` row, a bootstrap note, and a `models.md` entry. This design adds **Grok Build** (the `grok`
CLI, default model `grok-4.5`) as the fourth harness using that same pattern, without changing any
platform-neutral behavior.

The design is grounded in a live recon of Grok Build `0.2.93` (`docs/plans/2026-07-12-grok-migration.md`)
and corrects three points where issue #43 over-fit Grok to the Claude/Codex model. The task breakdown that
executes this spec is `docs/plans/2026-07-12-43-grok-build-platform.md`.

## Problem and goal

**Goal:** a user on Grok Build can install wi, run `scan` and `dev` to an open PR under Grok's keep-alive,
with parallel subagent waves in an isolated worktree, and every bundled script wi shells out to actually
runs. Claude/Codex/Copilot behavior is byte-for-byte unchanged.

**Non-goals:** cross-vendor MoA proposers (postponed #34); a Grok-specific plugin manifest unless a live
install proves it necessary; `rpa` end-to-end (stretch, depends on the UiPath skill ecosystem and tenant
auth, not a merge gate).

## Design decisions

1. **Keep-alive is a third, model-judged branch, not the Claude/Codex predicate branch.** Grok's
   `/goal <objective>` completes when the agent self-marks `completed: true` via `update_goal`. That is
   model-judged (Copilot-Autopilot class), not a runtime-enforced predicate. wi reuses the exact condition
   line as the **definition of done** and documents it as agent-judged with an unattended-run warning. This
   overrides issue #43's "join the Claude/Codex `/goal` family" framing, and the manifest/marketing copy
   must not reintroduce that conflation.
2. **`${CLAUDE_PLUGIN_ROOT}` resolution is a mandatory runtime protocol on Grok, not a docs note.** Grok
   aliases the env var for hooks only, and it can read empty in a tool shell. wi shells out to
   `python ${CLAUDE_PLUGIN_ROOT}/skills/.../*.py` (for example `cross_review.py`, `check_mermaid.py`,
   `now.py`), so an unresolved variable breaks execution. The adapter ships a resolve-once protocol and the
   merge gate includes a real agent-resolved bundled-script run.
3. **`models.md` gains a platform model resolution layer (routing only).** On a Grok host every dispatch is
   a Grok model, so the canonical tier tokens (`fable | opus | sonnet | haiku`) resolve through a per-host
   model map. Cross-provider diversity flips to OpenAI/Anthropic when the host is Grok (a Grok host
   reviewing with a Grok model is same-family); the xAI cross-provider entry is for the other hosts. This
   is the routing half only. MoA cross-vendor proposers stay #34.
4. **Worktree policy: three mechanisms, one canonical.** The wi feature worktree
   (`git worktree add -b wi/<slug>`) stays canonical with the orchestrator as sole committer; Grok's
   session `-w` is an optional outer shell that is never nested inside a wi feature worktree; the subagent
   `isolation: worktree` is the level-2 escalate only, matching the existing escalation ladder in
   `skills/build/references/worktrees-and-subagents.md`.
5. **Subagent dispatch is inline, Codex-style.** `spawn_subagent` with the built-in `general-purpose` type
   carrying the `agents/wi-task-runner.md` (or researcher/checker) contract inline; never depend on
   named-role registration.
6. **Merge gate is `scan` + `dev` end to end.** `rpa` is stretch.
7. **Hand-authored PR, single minor bump (1.11.1 to 1.12.0).** Not `/wi:dev` dogfooding: this PR modifies
   the platform/adapter layer itself, so building it with the tool-under-change is unsafe.

## Architecture

```
                    +-------------------------------------+
                    |  Platform-neutral wi core           |
                    |  skills/*  agents/*  .wi/ artifacts |
                    +------------------+------------------+
                                       | reads tool maps + keep-alive SSOT
        +------------------------------+------------------------------+
        |                    |                    |                   |
     Claude Code          Codex CLI          Copilot CLI          Grok Build
     Agent + predicate    spawn_agent +      task/fleet +         spawn_subagent +
     /goal                predicate /goal    Autopilot            model-judged /goal
                                                                  (grok-tools.md)
```

The autonomy spine (keep-alive, subagent dispatch, worktrees, model tokens, usage) is platform-conditional.
Grok is treated as **Claude-compatible packaging + Copilot-class (model-judged) completion + a first-class
subagent/worktree CLI**. Nothing in `skills/*` phase algorithms or `.wi/` artifact formats changes.

## Components

### 1. Packaging and install

Primary: `grok plugin install Wittenberger-Industries/wi-plugin --trust`, then enable if plugins are
disabled by default (exact flags confirmed on the live spike, S3). Grok loads Claude marketplace plugins
(skills, agents, hooks, `AGENTS.md`) with zero config; clone + `--plugin-dir` is the fallback. Publishing
to the official catalog is a separate PR to `xai-org/plugin-marketplace`, out of scope here. A
`.grok-plugin/plugin.json` is **deferred** until a live install proves the Claude-plugin layout alone does
not load wi; if added it joins the manifest parity set (four-way).

### 2. references/grok-tools.md (capability map)

New portability reference mirroring `references/codex-tools.md` and `references/copilot-tools.md`.

**Plugin-root resolution protocol (mandatory, the core of decision 2).** `${CLAUDE_PLUGIN_ROOT}` means the
wi plugin root (the directory holding `skills/`, `agents/`, `.claude-plugin/`). Because Grok may leave the
variable empty in a tool shell, wi resolves it rather than trusting it:

1. Resolve once at the start of any wi entry skill (scan / dev / rpa), before the first
   `${CLAUDE_PLUGIN_ROOT}` script call.
2. Never pass an unexpanded `${CLAUDE_PLUGIN_ROOT}` into the shell. Resolution order: (a) `$CLAUDE_PLUGIN_ROOT`
   if non-empty and it contains `skills/` + `.claude-plugin/`; (b) `$GROK_PLUGIN_ROOT` / `$PLUGIN_ROOT` if
   they look like the wi root; (c) the loaded wi plugin path from `grok inspect` / plugin list; (d) walk up
   from cwd for a dir holding both `skills/scan/SKILL.md` and `.claude-plugin/plugin.json`.
3. Use that absolute path in every `python <root>/skills/.../*.py` call for the rest of the run. If the
   spike shows `export` does not persist across Grok shell tool calls (S2 = no), absolute-path-per-call is
   the only guarantee; if it does persist, a one-time `export CLAUDE_PLUGIN_ROOT=<resolved>` is a
   convenience, not a substitute for step 3.

This is the same root rule Copilot uses (`references/copilot-tools.md` "${CLAUDE_PLUGIN_ROOT}"), promoted to
a hard protocol because Grok shells out. The script-invocation fallback is `references/workflow.md`
"Script invocation".

**Tool table (provisional: every id is verified against `grok inspect` on the spike, S3/S7, before
`grok-tools.md` ships).** The names below are the expected ids; the ones flagged `?` are the ones most
likely to differ across Grok Build versions:

| wi/skill says | Grok equivalent (confirm on spike) |
|---|---|
| Read a file | `read_file` |
| Write / create a file | `write` (some builds `create_file`) |
| Edit a file | `search_replace` |
| Bash / run a command | `run_terminal_command` |
| Grep / Glob | `grep` / file search via `run_terminal_command` |
| dispatch a subagent | `spawn_subagent` (types `general-purpose | explore | plan`, depth limit 1; `isolation`, `background`, `capability_mode` optional) |
| TodoWrite | `todo_write` |
| WebSearch | `web_search` |
| WebFetch | `web_fetch` or the build's fetch-style tool, if present; else `web_search` with a URL |

**Dispatch recipe (inline, Codex-style, decision 5):** `wi-task-runner` to `general-purpose` with the
`agents/wi-task-runner.md` contract inlined and a shared feature worktree (`isolation: none`);
`wi-researcher` to `explore` or read-only `general-purpose`; `wi-code-checker` to `general-purpose`. The
named `agents/*.md` files are never edited and never assumed to resolve as registered Grok agents.

**Worktree policy (decision 4)**, **keep-alive pointer** to the Grok branch in `keep-alive.md`, **models**
pointer to `models.md` "Platform model resolution", **usage** (`/usage`; `token_report.py`'s Claude
transcript parse does not apply, durations come from wi's own stamps, same as the Copilot ledger note), and
**permissions** (`--always-approve` / `--yolo` and headless `-p` / `--max-turns` / `--continue` run
unattended; `--check` is optional and is not wi's keep-alive) round out the file.

### 3. Keep-alive third branch (references/keep-alive.md)

An additive third bullet after the Copilot block; the Claude/Codex `/goal` code fence and the Copilot
Autopilot code fence are byte-identical after the change. The Grok bullet ships the same condition line as
the definition of done, then states plainly: Grok drives the goal itself and marks it complete via
`update_goal` when it judges the work done, so the condition is not a runtime-enforced predicate; the agent
can self-complete before remote checks are green or `progress.md` Phase is `done`. It carries the
unattended-run warning, the `/goal pause | resume` note, and the headless
`grok -p "<prompt incl. done-condition>" --always-approve --max-turns <N>` fallback with `--continue` /
resume. The closing pointer line and frontmatter description gain `grok-tools.md` / a Grok mention,
additively.

### 4. models.md platform model resolution + xAI cross-provider (decision 3)

**Schema.** A new optional `## Platform model map` section maps each canonical tier to a concrete host
model. Its parse contract is tight: it is a single pipe table whose first non-separator row is the header
(`| Tier | <host> ... |`, col 0 label ignored, cols 1+ are host names), and every later row maps one tier:

```
## Platform model map
| Tier | grok |
|------|------|
| fable | grok-4.5 |
| opus | grok-4.5 |
| sonnet | grok-composer-2.5-fast |
| haiku | grok-composer-2.5-fast |
```

`grok-4.5` is the strong/default model, `grok-composer-2.5-fast` the cheap/fast one (both resolved from
`grok models` at config time, S6). An unmapped tier, or `inherit`, passes through unchanged. The map is
optional: absent it, non-Claude hosts run every dispatch at the session model, the same as today.

**Host detection rule.** The host is `grok` when the run is following `references/grok-tools.md` (wi was
invoked under the `grok` CLI); otherwise the host is `claude` and the tier tokens are used as-is. Codex and
Copilot are `claude`-tier hosts for this purpose unless they later get their own map column.

**Runtime dispatch path vs the helper.** `cross_review.py` is the cross-provider HTTP layer and the only
Python that parses `models.md`; it does not drive `spawn_subagent`. The runtime resolution is the
orchestrator's, unchanged in shape from today's tier resolution: **detect host, read the platform map,
write the concrete per-role model ids into the `## Model routing (resolved)` block in `progress.md`, then
pass those ids to `spawn_subagent`.** The `models.md` prose states that path. The new
`platform_model_for(agent, cfg, host="claude")` helper in `cross_review.py` is that path's **executable,
tested specification** (the map-resolution contract), not the mechanism that "runs" routing: it resolves
`model_for(agent, cfg)` to a tier, then on a non-Claude host maps that tier through the platform map,
returning the tier verbatim for a Claude host or an unmapped tier. `orchestrator` stays informational (the
session model, set by the host's own model selector).

**xAI cross-provider.** `provider` accepts `openai | anthropic | xai | none`. `xai` uses xAI's
OpenAI-compatible endpoint and therefore rides the existing `_call_openai` path (`provider in ("openai",
"xai")` to `_call_openai`, `"anthropic"` to `_call_anthropic`). Normalization: when `provider == "xai"` and
`base_url` is empty or still the OpenAI default, `base_url` is set to `https://api.x.ai/v1` (a module
constant `XAI_BASE`); an explicit `base_url` is respected. On a Grok host, `models.md` prose directs the
cross-provider layer at `openai` or `anthropic` for real family diversity, not `xai`.

**Tests** (in `tests/test_models_config.py`): platform-map parse (golden fixture byte-identical to the
`models.md` table), Claude-host pass-through, Grok-host tier mapping (including an override that maps to a
Grok model), unmapped-tier pass-through, xAI base_url defaulting when unset, and xAI respecting an explicit
base_url.

### 5. Spine pointers (additive)

`AGENTS.md` (Grok row + persistence line), `skills/dev/SKILL.md` and `skills/research/SKILL.md` (keep-alive
handoff names Grok's model-judged `/goal`; the `autopilot` string stays so validate.py check 4 still
passes), `skills/build/references/worktrees-and-subagents.md` (Grok `spawn_subagent` dispatch + the
three-mechanism worktree policy), and `skills/scan/references/plugin-bootstrap.md` (Grok install + aliases +
superpowers on Grok's marketplace). Every edit is additive; no Claude/Codex/Copilot clause is reworded.
`agents/*.md` charters are never touched.

### 6. validate.py hard checks

Extend, never weaken: require `references/grok-tools.md` alongside the codex/copilot portability files;
assert a Grok keep-alive marker in `keep-alive.md` (`Grok Build` + `update_goal`); require a Grok pointer in
`skills/dev/SKILL.md` and `skills/research/SKILL.md` beside the existing Autopilot check; keep three-way
manifest parity (four-way only if `.grok-plugin/plugin.json` is added). Update the check-4 docstring.

### 7. README and manifests

README gains a fourth matrix column, an updated tool-map pointer, and a Grok install stanza. All three
manifests bump together to `1.12.0` and mention Grok Build in their descriptions, with a keep-alive
parenthetical that does not conflate Grok's model-judged goal with Claude's predicate (for example
`Claude/Codex predicate /goal; Grok model-judged /goal; Copilot Autopilot`).

## Acceptance criteria

1. **Grok scan + dev reach an open PR** on a real Grok Build session, under the Grok keep-alive line, with
   at least one parallel `spawn_subagent` wave in a wi feature worktree (no nested session worktree). On a
   remote-less repo, the local close-out (ship:7) stands in for the PR.
2. **Agent-resolved script execution works:** in a fresh session, with no human-pasted absolute path, the
   agent resolves the plugin root and runs `python <root>/skills/ship/scripts/now.py` and
   `check_mermaid.py`, both exit 0.
3. **Existing platforms are byte-stable:** `git diff main -- references/codex-tools.md
   references/copilot-tools.md` is empty; `git diff main -- references/keep-alive.md` shows only additive
   hunks (the Claude/Codex and Copilot fences unchanged).
4. **Static gates green:** `python scripts/validate.py` exit 0 (including the new Grok checks) and
   `python -m pytest tests/` all pass; three-way (or four-way) manifest parity at `1.12.0`.
5. **The `/goal` fidelity result is recorded honestly** (S5), even if that is "predicate not enforced;
   model-judged", and the keep-alive warning matches it.

## Verification

**Blocking recon spike (runs first, on the owner's Grok session).** Order: install/load first (that is
itself under test; fall back to clone + `--plugin-dir` if the plugin path is what fails), then the env +
agent-resolved-script gate, then the behavior probes. It measures S1-S8:

- S1 env-var outcome (set / hook-only / never); S2 does `export` persist across shell calls; S3 install
  command + trust/enable; S4 working entry slash form; S5 `/goal` fidelity (fail a condition clause, observe
  self-completion); S6 `grok models` ids; S7 named vs inline dispatch; S8 `grok -w` vs wi worktree nesting.

The spike answers feed the `[from S-N]` cells in `grok-tools.md` and the merge-gate decisions (S1 = B/C
makes the resolution protocol mandatory, which it is written as regardless; S2 = no drops the `export`
convenience). The static and live acceptance criteria above are the merge gate; the Checkpoint B harness
(frozen transcripts + analysis) is the sanctioned evidence method, and the `release/1.8.0` to Grok
"baseline-c" comparison doubles as the verification run.

## Out of scope

- **MoA cross-vendor proposers (#34):** letting the MoA council use non-Claude proposer models. This spec
  touches only the routing layer of `models.md`; #34's mechanics land in `references/moa.md` when
  un-postponed.
- **`.grok-plugin/plugin.json`:** deferred until a live install requires it.
- **`rpa` end to end:** stretch, not a merge blocker.
