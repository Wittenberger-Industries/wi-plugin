---
type: Reference
title: "Grok Build: tool & capability mapping for wi"
description: "Claude Code to Grok Build (grok CLI) tool-name and capability equivalents used when running wi on Grok, plus the mandatory resolve-once plugin-root protocol and the model-judged keep-alive pointer."
timestamp: 2026-07-12
tags: [grok, tools, portability, reference]
---

# Grok Build: tool & capability mapping for wi

wi's skills are written with Claude Code names. On Grok Build (`grok` CLI), use these equivalents.

Cells marked `(SPIKE S-N)` are confirmed on a real Grok Build session before this file ships (the recon
spike in `docs/plans/2026-07-12-43-grok-build-platform.md`); everything else is final.

## ${CLAUDE_PLUGIN_ROOT}: resolve once, then use an absolute path (mandatory)

`${CLAUDE_PLUGIN_ROOT}` means the **wi plugin root**: the directory holding `skills/`, `agents/`, and
`.claude-plugin/`. On Grok the plugin-root vars are injected into **hook processes only, by design**
(`~/.grok/docs/user-guide/09-plugins.md`), so they read **empty in the agent's tool shell** (confirmed:
S1). wi resolves the root itself, never relying on the variable:

1. Resolve **once** at the start of any wi entry skill (scan / dev / rpa), before the first
   `${CLAUDE_PLUGIN_ROOT}` script call. Record the result in `progress.md` as
   `Plugin root (resolved): <abs>` and reuse it for the rest of the run: each Grok shell tool call is a
   fresh process and `export` does **not** persist across calls (confirmed: S2), so `progress.md` is the
   persistence layer, not a shell variable.
2. **Never pass an unexpanded `${CLAUDE_PLUGIN_ROOT}` into the shell.** Resolution order:
   1. `$CLAUDE_PLUGIN_ROOT` if non-empty and it contains `skills/` + `.claude-plugin/` (usually empty on
      Grok; see above).
   2. `$GROK_PLUGIN_ROOT` / `$PLUGIN_ROOT` if they look like the wi root.
   3. The active `wi@wi` entry's `installPath` in `~/.claude/plugins/installed_plugins.json` - where
      Grok-via-Claude-compat installs live, and the step that resolves in practice. `grok plugin list` /
      `grok inspect` may show nothing, because wi loads through Claude compatibility, not Grok's own
      plugin registry.
   4. Walk up from cwd for a dir holding both `skills/scan/SKILL.md` and `.claude-plugin/plugin.json`
      (only finds an in-tree clone / `--plugin-dir`, not a cache install).
   Validate the winner: it must contain `skills/`, `.claude-plugin/`, and `skills/scan/SKILL.md`.
3. Use that **absolute path** (read back from `progress.md`) in every `python <root>/skills/.../*.py`
   call for the rest of the run, or inline it in the one command that runs the script
   (`CLAUDE_PLUGIN_ROOT=<abs> python <abs>/skills/.../x.py`).

This is the same root rule Copilot uses (`references/copilot-tools.md` "${CLAUDE_PLUGIN_ROOT}"), made a
hard protocol because Grok shells out. The script-invocation fallback is `references/workflow.md`
"Script invocation".

**Other plugins' skills (superpowers, frontend-design, ...):** the same registry step resolves ANY
Claude-compat plugin, not just wi: the plugin's entry in `~/.claude/plugins/installed_plugins.json` gives
its `installPath`; its skills live at `<installPath>/skills/<skill>/SKILL.md` (superpowers' reviewer
template likewise globs under `~/.claude/plugins/**`). Availability on Grok = the session skill list
(`grok inspect`) or that registry; measured on this harness, a run judged a skill "available" at one
phase and "absent" at a later phase of the same session - so **never log a `(<skill> absent)` fallback
stamp without checking the registry** (integrations.md "How to detect an available skill").

## Install & enable

The standard wi install on Grok is **two steps**:

1. **The plugin.** Confirmed: Grok loads wi from the **Claude plugin cache**
   (`~/.claude/plugins/cache/wi/wi/<version>/`) when `~/.grok/config.toml`'s `[plugins] enabled` lists
   `wi` - no `grok plugin install` step is needed, and `grok plugin list` shows Grok's *own* registry
   (empty for wi, since wi loads via Claude compatibility). Once wi is published to the xAI marketplace,
   `grok plugin install <name>` becomes the first-class path (that command pulls from a marketplace / git
   source, not a local branch); a local clone + `--plugin-dir` is the fallback for testing an unpublished
   build. Publishing to the official catalog is a separate PR to `xai-org/plugin-marketplace`.
2. **The flat `wi-*` aliases** into `~/.agents/skills/` (the shared flat-skills dir Grok scans; confirmed
   live). The bare plugin commands are `/scan`, `/dev`, `/rpa`; the aliases add the collision-free branded
   forms `/wi-scan`, `/wi-dev`, `/wi-rpa`. scan's bootstrap offers this copy
   (`skills/scan/references/plugin-bootstrap.md`); it is additive, one-time, and version-independent (the
   forwarders locate whatever wi plugin is installed).

## Tools

Ids confirmed live on Grok Build `0.2.93` (spike, 2026-07-12) from the session tool list.

| wi/skill says | Grok equivalent |
|---|---|
| Read a file | `read_file` |
| Write / create a file | `write` (there is no `create_file`) |
| Edit a file | `search_replace` |
| Bash / run a command | `run_terminal_command` |
| Grep / Glob | `grep` (native) / `list_dir`; shell fallback (`run_terminal_command` with `rg`/`find`) |
| dispatch a subagent / task-runner | `spawn_subagent` (built-in types `general-purpose \| explore \| plan`, depth limit 1; `isolation`, `background`, `capability_mode` optional) |
| parallel waves | multiple `spawn_subagent` calls in one turn; inline the runner/researcher prompt (do not rely on named-role dispatch: registration is convenience, not the contract) |
| TodoWrite | no `todo_write`; the closest is the `tasks__*` family (`tasks__create`, `tasks__update`, ...), else keep a plain markdown checklist in the reply |
| AskUserQuestion | `ask_user_question` |
| WebSearch | `web_search` |
| WebFetch | `web_fetch` (also `open_page` / `open_page_with_find` for reading a page) |
| invoke a wi skill | user-invocable skills load as bare slash commands: `/scan`, `/dev`, `/rpa` (the phase skills are `user-invocable: false`, so `/ship` etc. are not commands). On a name clash the qualifier is **scope-based** (`/user:scan`, `/local:scan`), NOT `/wi:scan` (colon-qualification is agents-only), and a built-in of the same name wins. For a collision-free branded form, install the flat `wi-*` forwarding aliases into `~/.agents/skills/` (the shared flat-skills dir Grok scans, same target as Copilot/Codex; never into Grok's own `~/.grok/skills/`) -> `/wi-scan`, `/wi-dev`, `/wi-rpa`. Natural-language auto-trigger also works. (confirmed S4) |
| resolve a skill's `SKILL.md` path (dispatch pointer for pinned runners) | it is under the skill's install dir (the resolved wi root's `skills/<skill>/SKILL.md`, or `~/.agents/skills/<skill>/SKILL.md` for flat aliases); the orchestrator resolves it once and passes it in the `[frontend]`-style dispatch |

## Subagent dispatch (inline, Codex-style)

Grok's tool is `spawn_subagent`. Dispatch each wi role as `general-purpose` with the role's contract
inlined into the prompt; do **not** assume a named wi agent resolves - registration is convenience, not
the contract. Gotcha (measured on `0.2.93`): agent registration **fails closed on the frontmatter
`color`** - an unsupported value silently drops the agent, no log line (bad: `magenta`, `white`, `gray`;
good: `cyan`, `green`, `red`, `blue`, `yellow`, `purple`, `orange`, `pink`). wi's charters use supported
colors; if an agent is missing from `grok inspect`, check `color` first.

| wi role | Grok dispatch |
|---------|----------------|
| `wi-task-runner` | `general-purpose`, prompt = inlined `agents/wi-task-runner.md` contract + task skeleton; **shared** feature worktree (`isolation: none`) |
| `wi-researcher` | `explore` or `general-purpose` + read-only; inline researcher contract |
| `wi-code-checker` | `general-purpose`; inline checker contract |

The named `agents/*.md` files are never edited and never assumed to register as Grok agents; the prompt
content is always inline, exactly as on Codex (`skills/build/references/worktrees-and-subagents.md`).

## Worktrees (three mechanisms, one canonical)

- **wi feature worktree** (`git worktree add -b wi/<slug> ...`) is canonical; the orchestrator is the sole
  committer.
- **Grok session `-w`** is an optional outer shell; do **not** run wi's worktree flow inside it. Measured
  (S8, `0.2.93`): the session workspace is a **standalone copy** of the repo under
  `~/.grok/worktrees/<project>/<stamp>/`, NOT a git linked worktree - inside it `git rev-parse --git-dir`
  equals `--git-common-dir` (both `.git`) on the normal branch, so the generic linked-worktree/detached-HEAD
  detection in `skills/build/references/worktrees-and-subagents.md` does **not** fire. Detect it by
  **path**: cwd under `~/.grok/worktrees/` means you are in a session copy - follow the sandboxed variant
  (commit in place, no new worktrees, hand the user branch + commit + PR text; a `wi/<slug>` branch or
  sibling worktree created inside the copy stays in the copy). Also measured: `-w` needs a HEAD commit; on
  a commitless repo it fails with `hub error: failed to get HEAD commit from source` (irrelevant mid-run:
  wi repos have commits by build time).
- **Subagent `isolation: worktree`** is the level-2 escalate only (file collision / non-parallel-safe
  tests), matching the existing escalation ladder.

## Keep-alive

Grok's `/goal` is **model-judged**, not a hard predicate: see the Grok Build branch in
`references/keep-alive.md`. Reuse the condition line as the definition of done; the unattended-run warning
applies.

## Models & usage

`grok models` lists ids (`grok-4.5` default, `grok-composer-2.5-fast` fast; confirmed S6). Pass the model
on `spawn_subagent` / the session per `references/models.md` "Platform model resolution (non-Claude
hosts)".

**The tokens.md ledger on Grok** (differs from both Claude and Copilot):

- **In-run rows:** the per-dispatch token figure is unobservable at dispatch return, so append each row
  with Tokens `0` and Basis `Grok: tokens unobservable in-run (0 = placeholder, not a measurement)`;
  the Duration cell is exact (the completion notification / OS stamps), `_ledger`-parseable format
  (`1m25s`, never bare `121s`). **Append the wave's rows at each wave gate**: Grok completions are
  pull-based (`get_command_or_subagent_output`), so append-on-notification silently skips dispatches
  (a live run logged 5 of 17); the wave gate is the reliable append point.
- **Finalize (ship's dossier tidy):** run
  `python <resolved-root>/skills/ship/scripts/grok_token_report.py --write .wi/features/<slug>/tokens.md`
  INSTEAD of `token_report.py --write`. Grok persists **exact** per-subagent figures
  (`subagent_finished.tokens_used` in the session's `updates.jsonl`), so the finalizer sets the
  Subagents (exact) sum from the session split, appends the per-agent split section, and fills the
  duration totals - subtracting the **measured human approval-waits** (`events.jsonl`
  `permission_resolved.wait_ms`) that fall inside the autonomous windows from the wall-clock, with the
  subtraction recorded as its own Orchestrator line ("excl. manual steps", made literal). The parent session has **no cumulative I/O on disk** (context-window occupancy
  only), so the Orchestrator line stays the honest `unavailable` sentinel with the occupancy facts
  beneath it; never add occupancy to the subagent total. `/usage` on screen may be copied verbatim
  like Copilot's rule.

## Permissions (unattended)

`--always-approve` / `--yolo` and headless `-p` / `--max-turns` / `--continue` run Grok unattended; the
same unattended warning as Copilot applies. `--check` (headless self-verification) is optional and is not
wi's keep-alive.
