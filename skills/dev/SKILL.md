---
name: dev
description: >
  The main entry point for building a feature with wi. Use this skill when the user types
  "/wi:dev <idea>", or says "build me <feature>", "I want a feature that <does X>", "add <capability> to
  this project", or otherwise asks to design-and-build something. dev orchestrates the whole loop:
  brainstorm (dialogue about WHAT) -> research skill (design: research -> plan -> design gate) -> build ->
  ship -> PR. At handoff it prints a ready-made line for Claude Code's BUILT-IN /goal command so the run
  keeps going across turns until the PR condition is met. Supports "/wi:dev <idea> --auto" to
  auto-approve the design gate for a fully hands-off run (the gate summary is still recorded).
---

# /wi:dev "<feature idea>" — brainstorm with me, then build it hands-off

This is how a feature starts. Interactive mode has two interactive moments — brainstorm and the design
gate; **`--auto` collapses everything after brainstorm**, so brainstorm becomes the only stop and the run
goes straight through to a PR.

The contract: brainstorming decides the *what*; the research skill proposes the *how*; the **design
gate** is where the user confirms it; after their go, nothing more is asked until the PR is up. wi
pairs with Claude Code's **built-in `/goal`** for persistence: wi provides the method (skills,
artifacts, gates), `/goal` provides the keep-running-until-done loop.

## Procedure

1. **Ensure the project is scanned.** If `.wi/repo-map.md` is missing, run **scan** first. Don't proceed
   without a repo map and constitution.
2. **Open the goal folder.** Parse flags: `--auto` sets **Gate mode: auto-approve** in
   progress.md — tell the user the design gate will be auto-approved and recorded, not asked. Derive a
   kebab-case `<slug>`, create `.wi/goals/<slug>/`, seed `progress.md` (template in the research skill's
   `wi-directory.md`).
3. **Brainstorm** (skill `wi:brainstorm`) — the dialogue about desired behavior, scope, constraints.
   Writes `brief.md`.
4. **Hand off — and arm the built-in `/goal`.** Recap the brief in 3-5 lines and print the ready-made
   keep-alive line:

   ```
   /goal The <slug> PR is open and its branch passes <lint + test commands from repo-map.md>;
   .wi/goals/<slug>/progress.md Phase is done. Constraints: only files named in tasks.md change;
   never force-push; tests are never weakened to pass.
   ```

   This is Claude Code's built-in persistence loop — armed, the run continues across turns until the
   condition verifiably holds (wi works without it, just less robustly through a stalled turn). **Then
   branch on Gate mode (from `progress.md`):**
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
- Keep dev thin: it sequences; the phase skills do the work; the built-in `/goal` keeps it alive.
