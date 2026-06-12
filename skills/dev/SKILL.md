---
name: dev
description: >
  The main entry point for building a feature with wi. Use this skill when the user types
  "/wi:dev <idea>", or says "build me <feature>", "I want a feature that <does X>", "add <capability> to
  this project", or otherwise asks to design-and-build something — including re-running an idea whose goal
  is already in flight (dev detects it and resumes instead of duplicating). dev orchestrates the whole loop:
  brainstorm (dialogue about WHAT) -> research skill (design: research -> plan -> design gate) -> build ->
  ship -> PR. At handoff it arms a keep-alive loop (Claude Code & Codex CLI use their built-in /goal; Copilot CLI uses Autopilot) so the run
  keeps going across turns until the PR condition is met. Supports "/wi:dev <idea> --auto" to
  auto-approve the design gate for a fully hands-off run (the gate summary is still recorded).
---

# /wi:dev "<feature idea>" — brainstorm with me, then build it hands-off

This is how a feature starts. Interactive mode has two interactive moments — brainstorm and the design
gate; **`--auto` collapses everything after brainstorm**, so brainstorm becomes the only stop and the run
goes straight through to a PR.

The contract: brainstorming decides the *what*; the research skill proposes the *how*; the **design
gate** is where the user confirms it; after their go, nothing more is asked until the PR is up. wi
pairs with a **keep-alive loop** for persistence — Claude Code & Codex use their built-in `/goal`,
Copilot uses Autopilot: wi provides the method (skills, artifacts, gates), the loop keeps running until done.

## Procedure

1. **Ensure the project is scanned — and current.** If `.wi/repo-map.md` is missing, run **scan** first;
   don't proceed without a repo map and constitution. If it exists but looks stale — `scanned` stamp older
   than ~2 weeks, or config/lock/CI files changed since it — run the scan skill's **`--refresh`** drift
   pass (cheap; updates facts + consolidates learnings) before building on the map.
2. **Open the goal folder — or resume the one already open.** Parse flags: `--auto` sets **Gate mode:
   auto-approve** in progress.md — tell the user the design gate will be auto-approved and recorded, not
   asked. Derive a kebab-case `<slug>`, then **check before creating**:
   - Scan `.wi/goals/*/progress.md` for Phase ≠ `done`. One matches this idea (same/near slug, or a title
     that reads as the same feature)? Then this is a **resume, not a new goal**: re-read its progress.md,
     announce the phase and what's left (ticked tasks, recorded decisions), and re-enter that phase —
     research/build/ship all re-enter from progress.md (workflow.md). Never seed a second folder for the
     same feature; never overwrite an existing dossier.
   - Idea is new but other goals are in flight: say so in one line (slug + phase each). If their
     `tasks.md` files overlap this idea's likely surface, run sequentially — two goals editing the same
     module trades merge conflicts for wall-clock.
   - Slug collides with a **done** goal: suffix the new one (`<slug>-2`); a finished dossier is history,
     not a scratch folder.
   - **Roadmap match:** if `.wi/roadmap.md` exists and this idea is one of its rows, use the row's slug,
     mark it `in-progress`, and carry the row's notes + sequencing rationale into brainstorm as seed
     context — the WHAT was part-captured when the roadmap was written, so brainstorm gets shorter, not
     skipped. Check its **Depends on**: a dependency that is done-but-unmerged (PR still open) means this
     goal would build against code `main` doesn't have — ask once (inside the brainstorm stop, like the
     preflight): wait for the merge, **stack** this branch on the dependency's branch (record it in
     progress.md; retarget the PR after the dep merges), or proceed off `main` deliberately.
   Only then create `.wi/goals/<slug>/` and seed `progress.md` (template in the research skill's
   `wi-directory.md`).
3. **Brainstorm** (skill `wi:brainstorm`) — the dialogue about desired behavior, scope, constraints.
   Writes `brief.md`.
4. **Hand off — and arm persistence (platform-aware).** First the **preflight** — an armed loop with a
   broken condition is guaranteed waste, so check two things before printing anything:
   - **The gate commands are real.** The lint + test commands about to be embedded in the condition must
     exist in `repo-map.md` and not be `UNKNOWN — ask` (greenfield gaps). UNKNOWN → resolve it now (one
     question, or scan's guided setup); never arm a condition no checker can verify.
   - **The brief answers the must-asks.** Scope/non-goals, desired behavior, acceptance, hard constraints
     are actually answered in `brief.md` — not blank, not self-answered. A hole → one more brainstorm
     round to fill it. (Both checks resolve inside the brainstorm stop — they are not a new gate.)
   Both green → recap the brief in 3-5 lines, then print the keep-alive handoff for the current platform:

   - **Claude Code / Codex CLI** (both have a built-in `/goal`):

     ```
     /goal The <slug> PR is open and its branch passes <lint + test commands from repo-map.md>;
     .wi/goals/<slug>/progress.md Phase is done. Constraints: only files named in tasks.md change;
     never force-push; tests are never weakened to pass.
     ```

   - **GitHub Copilot CLI** (no `/goal` — use Autopilot, condition in the prompt):

     ```
     copilot --autopilot --max-autopilot-continues <N> --no-ask-user --allow-all -p "Drive the <slug> goal to done:
     build then ship until the <slug> PR is open, its branch passes <lint + test commands>, and
     .wi/goals/<slug>/progress.md Phase is done. Only files named in tasks.md change; never force-push;
     never weaken tests."
     ```

   ⚠️ `--no-ask-user --allow-all` runs Copilot fully unattended (prompts suppressed, all tools/paths
   granted) — bounded only by `--max-autopilot-continues <N>` and the in-prompt constraints. Use it in
   repos you trust; drop `--allow-all` if you want Copilot to still confirm risky actions.

   Armed, the run continues across turns until the condition holds (wi works without it, just less
   robustly through a stalled turn). The per-platform mechanism is in
   `${CLAUDE_PLUGIN_ROOT}/references/codex-tools.md` / `copilot-tools.md`. **Then branch on Gate mode
   (from `progress.md`):**
   - **auto-approve** (`--auto`): do **not** ask for confirmation — the user already chose hands-off by
     passing the flag. Set Phase = `research` and continue straight into the design phase **in the same
     turn**. Brainstorm was the only stop; pausing for "say go" here is the bug `--auto` exists to avoid.
   - **interactive** (default): ask once — *"Ready to hand off?"* — and advance to `research` only on the
     user's go (pasting the `/goal` line counts as go).
5. **Design** (skill `wi:research`): research -> plan -> **design gate** (inline summary; approve / amend
   / stop — or auto-approve per the flag).
6. **Implement** (after the gate): **build** (skill `wi:build`) — worktree + parallel waves — then
   **ship** (skill `wi:ship`) — verification gate, PR, cleanup, and the final report including the token
   table. **No questions anywhere in this stretch**; decisions get made, recorded, and moved past.

## Boundaries

- User interactions by mode: **interactive** = brainstorm + a one-line handoff confirmation + the design
  gate; **`--auto`** = brainstorm only (no handoff confirmation, gate auto-approved and recorded). Never
  stop for anything else.
- If brainstorming reveals several features, capture them in `.wi/roadmap.md` and run each as its own
  `/wi:dev`. One goal = one feature = one PR.
- **Mid-run user input is routed, never absorbed silently.** If the user interjects during the autonomous
  stretch, record the message in progress.md (Decisions/blockers), then route it: small and inside the
  approved spec → append a task to `tasks.md` (build schedules it like any other); out-of-scope → a
  `roadmap.md` line (tell them which goal it became); contradicts the approved design/ADR → pause,
  re-open the design gate with a delta summary (approve / amend / stop), continue on the answer. The run
  never derails on input, and input never vanishes.
- Keep dev thin: it sequences; the phase skills do the work; the keep-alive loop (`/goal` or Autopilot) keeps it alive.
