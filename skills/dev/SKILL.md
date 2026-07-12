---
type: Skill
name: dev
description: >
  The main entry point for building a feature with wit. Use this skill when the user types
  "/wit:dev <idea>", or says "build me <feature>", "I want a feature that <does X>", "add <capability> to
  this project", or otherwise asks to design-and-build something, including re-running an idea whose feature
  is already in flight (dev detects it and resumes instead of duplicating). Supports "/wit:dev <idea>
  --auto" to auto-approve the design gate for a fully hands-off run.
---

# /wit:dev "<feature idea>": brainstorm with me, then build it hands-off

The contract: brainstorming decides the *what*; the research skill proposes the *how*; the **design
gate** is where the user confirms it; after their go, nothing more is asked until the PR is up.
**`--auto` collapses everything after brainstorm**, so brainstorm becomes the only stop and the run
goes straight through to a PR. wit pairs with a **keep-alive loop** for persistence: `/goal` on Claude
Code & Codex, Grok Build's model-judged `/goal`, Autopilot on Copilot.

Design rationale for this skill lives in the wit repo's `docs/design-notes/dev.md` (maintainer doc,
never loaded at runtime).

## Procedure

1. **Ensure the project is scanned, and current.** If the project has a legacy `.wi/` (pre-1.12.2 name)
   and no `.wit/`, rename it first (`git mv .wi .wit`, one commit; ask unless `--auto`).
   If `.wit/repo-map.md` is missing, run **scan** first;
   don't proceed without a repo map and constitution. Stale (`scanned` stamp older than ~2 weeks, or
   config/lock/CI files changed since it) → run the scan skill's **`--refresh`** drift pass before
   building on the map.
   **Model routing first-run setup** here (`${CLAUDE_PLUGIN_ROOT}/references/models.md` "First-run
   setup"): set up `.wit/models.md` if absent, else apply it, then resolve the routing once per that
   reference. dev:2 records the result as the `## Model routing (resolved)` block when `progress.md` is
   seeded, and a resumed feature missing the block gets it written on re-entry; every later dispatch reads
   the block, not `.wit/models.md`.
2. **Open the feature folder, or route the edge case first.** Parse flags: `--auto` sets
   **Gate mode: auto-approve** in progress.md; tell the user the design gate will be auto-approved and
   recorded, not asked. Then **classify the idea before creating anything**:
   **new / resume / in-flight-overlap / done-collision / roadmap-row** (tells: an in-flight
   `features/*/progress.md` reading as this same idea → resume; others merely in flight → overlap; a
   done feature with this name → done-collision; a matching `.wit/roadmap.md` row → roadmap-row).
   Anything but a plain new feature → follow
   `${CLAUDE_PLUGIN_ROOT}/references/feature-folder-cases.md` for every case whose tell fires. The
   common path: derive a kebab-case name, prefix the **next global 4-digit ordinal** so `<slug>` =
   `NNNN-<name>` (next = highest existing `.wit/features/` ordinal + 1, else `0001`, e.g.
   `0001-stripe-webhooks`; full rule: wit-directory.md's Slugs bullet), create `.wit/features/<slug>/`,
   and seed `progress.md` (template in the research skill's `wit-directory.md`). Every Log line, the
   `**Created**` seed included, opens with a full ISO-8601 timestamp from the OS clock
   (`date -Iseconds`, or `python ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/now.py`); never a date-only
   or guessed stamp.
3. **Brainstorm** (skill `wit:brainstorm`): the dialogue about desired behavior, scope, constraints.
   Writes `brief.md`. **Interactive and never skipped**: `--auto` does not collapse it, and a detailed
   idea or a matching roadmap row **seeds** the dialogue, never replaces it. The only sanctioned
   self-answer stamp is `self-answered (headless)`, and headless means no user can answer at all (CI, a
   subagent dispatch, a scheduled run; brainstorm's headless rule) - a session with a user present is
   never headless.
4. **Hand off and arm persistence (platform-aware).** First the **preflight**; resolve every check
   before printing anything:
   - **The gate commands are real.** The lint + test commands about to be embedded in the condition must
     exist in `repo-map.md` and not be `UNKNOWN - ask` (greenfield gaps). UNKNOWN → resolve it now (one
     question, or scan's guided setup); never arm a condition no checker can verify. A command genuinely
     absent from the project (no linter configured) is recorded as `n/a - not configured` and **passes**
     the preflight; the keep-alive condition renders without that clause (keep-alive.md's fill rule);
     only `UNKNOWN` blocks.
   - **The brief answers the must-asks.** Scope/non-goals, desired behavior, acceptance, hard constraints
     are actually answered in `brief.md`: not blank, not self-answered. One carve-out: a **headless run**
     (brainstorm's headless rule) is *sanctioned* self-answering; there the check becomes "every must-ask
     has its logged assumption, and the stamp says `self-answered (headless)`". Any other `self-answered`
     label (`roadmap-seeded`, `for speed`, ...) **fails this check**. A hole → one more
     brainstorm round to fill it.
   - **A PR-open condition needs a remote.** `git remote` prints nothing → do **not** print or arm the
     keep-alive at all. Note in progress.md that the run ends at ship's no-remote close-out (ship:7) and
     the keep-alive applies once a remote exists. (All checks resolve inside the brainstorm stop; they
     are not a new gate.)
   All green → recap the brief in 3-5 lines, then print the keep-alive handoff for the current platform
   **verbatim from `${CLAUDE_PLUGIN_ROOT}/references/keep-alive.md`**, the single source of the platform
   templates (`/goal` on Claude Code & Codex, Grok Build's model-judged `/goal`, the Autopilot relaunch +
   unattended-run warning on Copilot). The per-platform mechanism is in
   `${CLAUDE_PLUGIN_ROOT}/references/codex-tools.md` / `copilot-tools.md` / `grok-tools.md`.
   **Then branch on Gate mode (from `progress.md`):**
   - **auto-approve** (`--auto`): do **not** ask for confirmation; the user already chose hands-off. Set
     Phase = `research`, stamp the Log line (`- <ts> **Update** phase = research`; it starts the run's
     autonomous clock), and continue straight into the design phase **in the same turn**. Brainstorm was
     the only stop.
   - **interactive** (default): ask once, *"Ready to hand off?"*, and advance on the user's go.
     **Pasting the `/goal` line is the go.** When the goal registers (the platform echoes "Goal set: …"),
     do not stop: set Phase = `research` (same stamped Log line) and continue into the design phase
     **in the same turn**, exactly as the auto path does. Never end the turn at the recap or the
     "Goal set" acknowledgment.
5. **Design** (skill `wit:research`): research -> plan -> **design gate** (inline summary;
   approve / amend / stop, or auto-approve per the flag).
6. **Implement** (after the gate): **build** (skill `wit:build`), worktree + parallel waves, then
   **ship** (skill `wit:ship`): verification gate, PR opened and its remote checks verified, cleanup,
   and the final report including the token table. **No questions anywhere in this stretch**
   (workflow.md's no-questions rule).

## Boundaries

- User interactions by mode: **interactive** = brainstorm + a one-line handoff confirmation + the design
  gate; **`--auto`** = brainstorm only (no handoff confirmation, gate auto-approved and recorded). Never
  stop for anything else.
- **Context budget (workflow.md):** dev holds `repo-map.md`, `constitution.md`, and the feature's
  `progress.md`; resume detection reads each in-flight feature's `progress.md` and nothing else; the
  handoff preflight checks `brief.md` once. Bigger reads are delegated to the phase skills' subagents.
- **Compact reasoning, run-wide** (the **compact-reasoning rule**;
  `${CLAUDE_PLUGIN_ROOT}/references/compact-reasoning.md`): across the autonomous stretch, essential,
  decision-bearing thoughts only; classification, preflight, and sequencing are decided, not narrated.
  The note's carve-outs (plan decomposition, the design gates) keep full depth.
- If brainstorming reveals several features, capture them in `.wit/roadmap.md`, committed where written
  (`docs(wit): roadmap`), and run each as its own `/wit:dev`. One feature = one PR.
- **Mid-run user input is routed, never absorbed silently.** Record the message in progress.md
  (Decisions/blockers), then route it: small and inside the approved spec → append a task to `tasks.md`
  (build schedules it like any other); out-of-scope → a `roadmap.md` line (tell them which feature it
  became); contradicts the approved design/ADR → pause, re-open the design gate with a delta summary
  (approve / amend / stop), continue on the answer.
- **Superpowers precedence** (integrations.md "Who initiates";
  `${CLAUDE_PLUGIN_ROOT}/skills/research/references/integrations.md`): delegation points only, never
  self-triggered mid-phase; wit's artifact formats always win.
- Keep dev thin: it sequences; the phase skills do the work; the keep-alive loop (`/goal` or Autopilot)
  keeps it alive.
