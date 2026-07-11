---
type: Skill
name: dev
description: >
  The main entry point for building a feature with wi. Use this skill when the user types
  "/wi:dev <idea>", or says "build me <feature>", "I want a feature that <does X>", "add <capability> to
  this project", or otherwise asks to design-and-build something — including re-running an idea whose feature
  is already in flight (dev detects it and resumes instead of duplicating). Supports "/wi:dev <idea>
  --auto" to auto-approve the design gate for a fully hands-off run.
---

# /wi:dev "<feature idea>" — brainstorm with me, then build it hands-off

This is how a feature starts. Interactive mode has two interactive moments — brainstorm and the design
gate — plus a one-line handoff confirmation between them; **`--auto` collapses everything after
brainstorm**, so brainstorm becomes the only stop and the run goes straight through to a PR.

The contract: brainstorming decides the *what*; the research skill proposes the *how*; the **design
gate** is where the user confirms it; after their go, nothing more is asked until the PR is up. wi
pairs with a **keep-alive loop** for persistence — Claude Code & Codex use their built-in `/goal`,
Copilot uses Autopilot: wi provides the method (skills, artifacts, gates), the loop keeps running until done.

## Procedure

1. **Ensure the project is scanned — and current.** If `.wi/repo-map.md` is missing, run **scan** first;
   don't proceed without a repo map and constitution. If it exists but looks stale — `scanned` stamp older
   than ~2 weeks, or config/lock/CI files changed since it — run the scan skill's **`--refresh`** drift
   pass (cheap; updates facts + consolidates learnings) before building on the map.
   **Model routing first-run setup** (`${CLAUDE_PLUGIN_ROOT}/references/models.md` "First-run setup"):
   `.wi/models.md` absent → ask once and write+commit per that section (`--auto` → the **simple** preset,
   logged as an assumption); present → apply it silently, warning once if the session model is below the
   configured orchestrator tier; a pre-1.3 legacy config → rename per that section. Never re-ask an
   existing config. Finish by resolving the routing once (override → role →
   `inherit` per dispatch kind — models.md's **resolve-once rule**); dev:2 records it as the
   `## Model routing (resolved)` block when `progress.md` is seeded, and a resumed feature missing the
   block gets it written on re-entry. Every later dispatch reads the block, not `.wi/models.md`.
2. **Open the feature folder — or route the edge case first.** Parse flags: `--auto` sets **Gate mode:
   auto-approve** in progress.md — tell the user the design gate will be auto-approved and recorded, not
   asked. Then **classify the idea before creating anything** — **new / resume / in-flight-overlap /
   done-collision / roadmap-row / legacy-repo** (tells: an in-flight `features/*/progress.md` reading as
   this same idea → resume; others merely in flight → overlap; a done feature with this name →
   done-collision; a matching `.wi/roadmap.md` row → roadmap-row; a pre-rename work-unit folder
   (`goals`, not `features`) → legacy). Anything but a plain new feature → follow
   `${CLAUDE_PLUGIN_ROOT}/references/feature-folder-cases.md` for every case whose tell fires. The
   common path: derive a kebab-case name, prefix the **next global 4-digit ordinal** so `<slug>` =
   `NNNN-<name>` (next = highest existing `.wi/features/` ordinal + 1, else `0001` — e.g.
   `0001-stripe-webhooks`; full rule: wi-directory.md's Slugs bullet), create `.wi/features/<slug>/`,
   and seed `progress.md` (template in the research skill's `wi-directory.md`). Every Log line — the `**Created**`
   seed included — opens with a full ISO-8601 timestamp from the OS clock (`date -Iseconds`, or
   `python ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/now.py`); ship computes the run's timing from these
   stamps, so never write a date-only or guessed one.
3. **Brainstorm** (skill `wi:brainstorm`) — the dialogue about desired behavior, scope, constraints.
   Writes `brief.md`.
4. **Hand off — and arm persistence (platform-aware).** First the **preflight** — an armed loop with a
   broken condition is guaranteed waste, so check two things before printing anything:
   - **The gate commands are real.** The lint + test commands about to be embedded in the condition must
     exist in `repo-map.md` and not be `UNKNOWN — ask` (greenfield gaps). UNKNOWN → resolve it now (one
     question, or scan's guided setup); never arm a condition no checker can verify. A command genuinely
     absent from the project (no linter configured) is recorded as `n/a — not configured` and **passes**
     the preflight — the keep-alive condition renders without that clause (keep-alive.md's fill rule);
     only `UNKNOWN` blocks.
   - **The brief answers the must-asks.** Scope/non-goals, desired behavior, acceptance, hard constraints
     are actually answered in `brief.md` — not blank, not self-answered. One carve-out: a **headless run**
     (brainstorm's headless rule) is *sanctioned* self-answering — there the check becomes "every must-ask
     has its logged assumption, and the stamp says `self-answered (headless)`". A hole → one more
     brainstorm round to fill it.
   - **A PR-open condition needs a remote.** `git remote` prints nothing → do **not** print or arm the
     keep-alive at all: the condition can never hold and an armed loop would spin forever. Note in
     progress.md that the run ends at ship's no-remote close-out (ship:7) and the keep-alive applies once
     a remote exists. (All checks resolve inside the brainstorm stop — they are not a new gate.)
   Both green → recap the brief in 3-5 lines, then print the keep-alive handoff for the current platform
   **verbatim from `${CLAUDE_PLUGIN_ROOT}/references/keep-alive.md`** — the single source of the platform
   templates (`/goal` on Claude Code & Codex, the Autopilot relaunch + unattended-run warning on Copilot).

   Armed, the run continues across turns until the condition holds (keep-alive.md). The per-platform
   mechanism is in
   `${CLAUDE_PLUGIN_ROOT}/references/codex-tools.md` / `copilot-tools.md`. **Then branch on Gate mode
   (from `progress.md`):**
   - **auto-approve** (`--auto`): do **not** ask for confirmation — the user already chose hands-off by
     passing the flag. Set Phase = `research` — stamp the Log line (`- <ts> **Update** phase = research`);
     it starts the run's autonomous clock — and continue straight into the design phase **in the same
     turn**. Brainstorm was the only stop; pausing for "say go" here is the bug `--auto` exists to avoid.
   - **interactive** (default): ask once — *"Ready to hand off?"* — and advance on the user's go.
     **Pasting the `/goal` line is the go.** When the goal registers (the platform echoes "Goal set: …"),
     do not stop: set Phase = `research` (same stamped Log line — it starts the autonomous clock) and
     continue into the design phase **in the same turn**, exactly as the auto path does. Ending the turn after the recap or the "Goal set" acknowledgment — waiting
     for another prompt — is the stall this rule exists to prevent.
5. **Design** (skill `wi:research`): research -> plan -> **design gate** (inline summary; approve / amend
   / stop — or auto-approve per the flag).
6. **Implement** (after the gate): **build** (skill `wi:build`) — worktree + parallel waves — then
   **ship** (skill `wi:ship`) — verification gate, PR opened and its remote checks verified, cleanup,
   and the final report including the token table. **No questions anywhere in this stretch**
   (workflow.md's no-questions rule); decisions get made, recorded, and moved past.

## Boundaries

- User interactions by mode: **interactive** = brainstorm + a one-line handoff confirmation + the design
  gate; **`--auto`** = brainstorm only (no handoff confirmation, gate auto-approved and recorded). Never
  stop for anything else.
- **Context budget (workflow.md):** dev holds `repo-map.md`, `constitution.md`, and the feature's
  `progress.md`; resume detection reads each in-flight feature's `progress.md` — nothing else; the
  handoff preflight checks `brief.md` once. Bigger reads are delegated — the phase skills' subagents
  do the reading.
- **Compact reasoning, run-wide** (the **compact-reasoning rule** —
  `${CLAUDE_PLUGIN_ROOT}/references/compact-reasoning.md`): across the autonomous stretch, essential,
  decision-bearing thoughts only — classification, preflight, and sequencing are decided, not narrated.
  The note's carve-outs (plan decomposition, the design gates) keep full depth.
- If brainstorming reveals several features, capture them in `.wi/roadmap.md` — committed where written
  (`docs(wi): roadmap`) — and run each as its own `/wi:dev`. One feature = one PR.
- **Mid-run user input is routed, never absorbed silently.** If the user interjects during the autonomous
  stretch, record the message in progress.md (Decisions/blockers), then route it: small and inside the
  approved spec → append a task to `tasks.md` (build schedules it like any other); out-of-scope → a
  `roadmap.md` line (tell them which feature it became); contradicts the approved design/ADR → pause,
  re-open the design gate with a delta summary (approve / amend / stop), continue on the answer. The run
  never derails on input, and input never vanishes.
- **Superpowers precedence** (integrations.md "Who initiates" —
  `${CLAUDE_PLUGIN_ROOT}/skills/research/references/integrations.md`): delegation points only, never
  self-triggered mid-phase; wi's artifact formats always win.
- Keep dev thin: it sequences; the phase skills do the work; the keep-alive loop (`/goal` or Autopilot) keeps it alive.
