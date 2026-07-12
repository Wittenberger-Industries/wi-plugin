---
type: Reference
title: "The keep-alive handoff: /goal & Autopilot templates"
description: "Canonical keep-alive handoff block: the /goal condition line (Claude Code/Codex), the Copilot Autopilot command, the Grok Build model-judged /goal branch, and the unattended-run warning. dev:4 and research:4 print from here."
timestamp: 2026-07-03
tags: [keep-alive, goal, autopilot, handoff, portability, reference]
---

# The keep-alive handoff: one canonical block

wit pairs with a keep-alive loop for persistence: armed at handoff, the run continues across turns until
its condition holds (wit works without it, just less robustly through a stalled turn). Claude Code and
Codex CLI use their built-in `/goal`; Copilot CLI has no predicate `/goal` and relaunches under
**Autopilot** with the condition in the prompt. Grok Build has a native `/goal` too, but it is
**model-judged** (the agent self-completes via `update_goal`), so it behaves like Autopilot, not like the
Claude/Codex predicate. This file is the **single source of the exact templates**:
dev:4 and research:4 print from here; edit the block here, never a copy in a skill.

Before printing, fill `<slug>` and `<lint + test commands>` with the exact commands from `repo-map.md`:
never arm a condition no checker can verify (dev's preflight guards this). A command repo-map records as
`n/a - not configured` (e.g. no linter exists) is **dropped from the condition**, not a blocker: render
with the commands that do exist; a test-only condition is valid. Only `UNKNOWN - ask` blocks arming.
No git remote at all → **don't arm anything**: the PR-open condition can never hold on a remote-less
repo (ship closes out locally instead, ship:7); dev's preflight checks this before printing.

- **Claude Code / Codex CLI** (both have a built-in `/goal`):

  ```
  /goal The <slug> PR is open with its remote checks green (or none configured) and its branch passes <lint + test commands from repo-map.md>; .wit/features/<slug>/progress.md Phase is done. Constraints: only files named in tasks.md change; never force-push; tests are never weakened to pass.
  ```

  Print and paste as **one line**. A multi-line `/goal` can register only its first line as the
  predicate, silently dropping the Phase condition and the constraints. When the repo has remote CI,
  "passes" / "green" is judged against the **PR's checks** (the authoritative signal), not only the
  local run; a repo with no CI is judged on the local gate alone.

- **GitHub Copilot CLI** (no `/goal`; use Autopilot, condition in the prompt):

  ```
  copilot --autopilot --max-autopilot-continues <N> --no-ask-user --allow-all -p "Drive the <slug> feature to done:
  build then ship until the <slug> PR is open with its remote checks green (or none configured), its
  branch passes <lint + test commands>, and .wit/features/<slug>/progress.md Phase is done. Only files
  named in tasks.md change; never force-push; never weaken tests."
  ```

⚠️ `--no-ask-user --allow-all` runs Copilot fully unattended (prompts suppressed, all tools/paths
granted), bounded only by `--max-autopilot-continues <N>` and the in-prompt constraints. Use it in
repos you trust; drop `--allow-all` if you want Copilot to still confirm risky actions.

- **Grok Build** (native `/goal`, but **model-judged**, not a predicate):

  ```
  /goal The <slug> PR is open with its remote checks green (or none configured) and its branch passes <lint + test commands from repo-map.md>; .wit/features/<slug>/progress.md Phase is done. Constraints: only files named in tasks.md change; never force-push; tests are never weakened to pass.
  ```

  Grok drives the goal itself and marks it complete via `update_goal` when **it** judges the work done, so
  the condition line is the **definition of done**, not a platform predicate the runtime enforces. Paste it
  as **one line**. Use `/goal pause | resume` around auth-gate stops. Headless fallback:
  `grok -p "<prompt incl. the done-condition>" --always-approve --max-turns <N>` with `--continue` /
  session resume.

  ⚠️ Completion is **model-judged**, not runtime-enforced. In testing, grok-4.5 verified the condition and
  correctly held (it probed an unsatisfiable clause three ways and refused to self-complete or fake a green
  status), so fidelity is good - but the guarantee is the model's diligence plus a clear, explicit
  condition, not a hard predicate the way Claude/Codex `/goal` is. Keep the condition unambiguous, and since
  `--always-approve` runs Grok unattended (prompts suppressed), use it in repos you trust.

The Copilot command is never printed without the warning above. The per-platform mechanism behind
`/goal` / Autopilot lives in `${CLAUDE_PLUGIN_ROOT}/references/codex-tools.md` / `copilot-tools.md` /
`grok-tools.md`.
