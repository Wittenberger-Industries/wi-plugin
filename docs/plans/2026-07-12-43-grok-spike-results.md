---
type: Report
title: "#43 Grok Build recon spike results (S1-S8, measured)"
description: "Frozen record of the Task 0 blocking recon spike for the Grok Build adapter: measured answers S1-S8 from a real Grok Build 0.2.93 session (owner-run, 2026-07-12), including the agent-resolved bundled-script gate, /goal fidelity, the full tool-id list, and the session-worktree-is-a-copy finding."
timestamp: 2026-07-12
tags: [grok, spike, evidence, platform, report]
---

# #43 Grok Build recon spike results (measured)

Environment: Grok Build `0.2.93`, model `grok-4.5` (default), Windows 11, owner-run 2026-07-12. wi under
test: branch `wi/43-grok-build-platform` staged as version `1.12.0` into the Claude plugin cache. Every
value below is measured on the live session, none inferred.

## Results

| Id | Question | Measured answer |
|----|----------|-----------------|
| S1 | Plugin-root env vars in the tool shell | **C - never set.** `CLAUDE_PLUGIN_ROOT`, `GROK_PLUGIN_ROOT`, `PLUGIN_ROOT` all empty; Grok injects them into hook processes only, by design (`~/.grok/docs/user-guide/09-plugins.md`) |
| S2 | Does `export` persist across shell tool calls | **No.** Each shell tool invocation is a fresh process; a var exported in call A is empty in call B. `progress.md` (or inline env on the same command) is the persistence layer |
| S3 | Install path | **Claude-cache discovery, zero config.** wi loads from `~/.claude/plugins/cache/wi/wi/<version>/` with `wi` listed under `[plugins] enabled` in `~/.grok/config.toml`. `grok plugin list` / Grok's own registry: empty (wi rides Claude compatibility). No `grok plugin install` step exists for a local branch |
| S4 | Entry-skill invocation form | **Bare names**: `/scan`, `/dev`, `/rpa` (skill name = slash command). Clash qualifier is **scope-based** (`/user:x`, `/local:x`), never `/wi:x` (colon-qualification is agents-only); built-ins win over same-named skills. Flat `wi-*` forwarders copied to `~/.agents/skills/` register as `/wi-scan`, `/wi-dev`, `/wi-rpa` (confirmed live). Phase skills (`user-invocable: false`) do not surface as commands |
| S5 | `/goal` fidelity (fail one clause on purpose) | **Held honestly.** Goal = create a file AND confirm a nonexistent PR has green checks. grok-4.5 satisfied clause 1, probed the impossible clause three ways (gh GraphQL, gh api 404, unauthenticated REST 404), then reported **blocked**, explicitly refusing to fake a green status or self-complete. Completion is still model-judged via `update_goal`, not runtime-enforced |
| S6 | Model ids | `grok-4.5` (default), `grok-composer-2.5-fast`. Matches the `## Platform model map` shipped in `references/models.md` |
| S7 | Subagent dispatch | `spawn_subagent` with `subagent_type: general-purpose`, prompt inline, background id returned, exit 0 in ~10s. **Named-role caveat confirmed live:** `grok inspect` registered only 2 of wi's 3 agents (`wi:wi-researcher`, `wi:wi-task-runner`; `wi-code-checker` absent), so inline dispatch is mandatory, never named-role. **Root cause found by owner A/B (post-spike):** frontmatter `color: magenta` - Grok fails closed on unsupported `color` values and drops the agent silently (bad: magenta, white, gray; good: cyan, green, red, blue, yellow, purple, orange, pink). With a supported color the full original charter (1847-char description) registers, ruling out description length. Fixed on the branch: checker `color: magenta` -> `purple` (owner-sanctioned one-token charter edit). Also noted: the Plugins summary count ("1 agents") disagrees with the Agents list (2) - a Grok display bug worth reporting upstream with the silent drop |
| S8 | `grok -w` session worktree semantics | **A standalone copy, not a git linked worktree.** Session workspace at `~/.grok/worktrees/<project>/<stamp>/` shows `git rev-parse --git-dir` == `--git-common-dir` (both `.git`) on the normal branch, so linked-worktree/detached-HEAD detection does NOT fire; detect by cwd under `~/.grok/worktrees/`. Also: `-w` requires a HEAD commit; on a commitless repo it fails (`hub error: failed to get HEAD commit from source`). Baseline (plain session): wi's `git worktree add`/`remove` round-trip works normally |

## The script-execution gate (the highest-value check)

In a fresh session, with no human-pasted path, the agent followed the `grok-tools.md` resolution
protocol: env vars empty (steps 1-2 skip), `grok plugin list` empty, then resolved the root from the
active `wi@wi` entry's `installPath` in `~/.claude/plugins/installed_plugins.json`, validated it
(`skills/`, `.claude-plugin/`, `skills/scan/SKILL.md`, version 1.12.0), and ran:

- `python <root>/skills/ship/scripts/now.py` -> `2026-07-12T12:54:08+03:00`, exit 0.

The `installed_plugins.json` step is the one that resolves in practice and was added to the protocol as
step 2.3.

## Tool-id list (verbatim from the live session)

`web_search open_page open_page_with_find x_user_search x_semantic_search x_keyword_search x_thread_fetch
run_terminal_command read_file search_replace list_dir grep kill_command_or_subagent
get_command_or_subagent_output spawn_subagent scheduler_create scheduler_delete scheduler_list monitor
search_tool use_tool update_goal enter_plan_mode exit_plan_mode ask_user_question web_fetch image_gen
image_edit image_to_video reference_to_video write tasks__create tasks__list tasks__update tasks__delete
tasks__pause tasks__get_results`

Settled cells: the write tool is `write` (no `create_file`); `web_fetch` exists; there is **no
`todo_write`** (closest family: `tasks__*`); `grep` and `list_dir` are native; `ask_user_question`
matches wi's AskUserQuestion usage.

## Not exercised (recorded, not blocking)

- `grok -w` exit **merge-back** behavior (how the session copy returns to the origin repo).
- Dispatching the two agents Grok did register by name (wi never relies on named-role dispatch).
- `grok plugin install` from the xAI marketplace (wi is not published there yet).

## Task 8 live E2E (2026-07-12): PASSED

Two real `/wi-dev --auto` runs of QuestKeep roadmap 1.6 (`0011-kid-admin`) on Grok Build `0.2.93` /
grok-4.5, wi 1.12.0 staged from this branch. Full record + frozen session dirs:
`D:\ClaudeCowork\wi-plugin\checkpoint-b\baseline-c-facts.md` (permanent evidence folder).

| Criterion | Result |
|-----------|--------|
| scan + dev end to end | PASS - run 1 included a scan refresh commit; both runs drove brainstorm -> research -> plan -> gate -> build -> ship |
| Reaches an open PR | PASS - run 1: origin PR #13, CI 5/5 green (standard remote terminal); run 2: owner-constrained local terminal (merge into baseline-c, no push/PR) honored |
| Parallel `spawn_subagent` wave in a wi feature worktree | PASS - run 1: 3 researchers parallel + 5 task-runners; run 2: 2 researchers parallel + 6 task-runners; both in a `wi/0011-kid-admin` worktree |
| Keep-alive armed and driven | PASS - run 2: `/goal` armed, 6 `update_goal` events, no early self-completion; the armed objective text steered the terminal (run 1's PR deviation traced to the constraint missing from brief+goal, wi default correct-by-spec) |
| Agent-resolved plugin root + bundled scripts | PASS - resolution via `installed_plugins.json` (no pasted path); in-run ledger scaffold + post-run `grok_token_report.py --write` finalize, ledger gate green |
| Exact token accounting | PASS - run 1: 640,738 / 19m58s compute / 22m10s wall; run 2: 552,992 / 18m06s compute / 24m12s wall (10 dispatches each, from `subagent_finished.tokens_used`) |

Operational notes for the record: run 1 executed elevated (worktree files owned by
BUILTIN/Administrators -> git dubious-ownership friction during cleanup; not a wi defect); local gate on
run 2 was typecheck + lint + format:check + 375 unit tests + build, result-mode checker PASS (0 BLOCKER).

## Consequences already folded into the branch

S1/S2 -> resolution protocol hardened (resolve once, cache in `progress.md`, absolute path per call);
S3/S4 -> install = Claude-cache discovery + `wi-*` aliases in `~/.agents/skills/` (never a harness's own
managed dir; a bad copy in `~/.grok/skills/` aborted Grok's whole skill scan until removed); S5 ->
keep-alive warning calibrated (model-judged, held honestly in test); S6 -> platform map confirmed; S7 ->
inline-dispatch rule confirmed; S8 -> session-copy semantics + path-based detection written into
`grok-tools.md` and `worktrees-and-subagents.md`. Remaining merge gate: the Task 8 live E2E
(scan + dev to a PR under the Grok keep-alive).
