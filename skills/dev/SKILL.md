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
   **Model routing first-run setup** (`${CLAUDE_PLUGIN_ROOT}/references/models.md`): `.wi/models.md`
   absent → interactive asks once (preset smart / simple / custom, rows confirmable), `--auto` writes the
   **simple** preset and logs the assumption; present → apply it silently, warning once if the session
   model is below the configured orchestrator tier. A legacy config left by a pre-1.3 run (an old-named
   `.wi/*.md` carrying the same `## Roles` / `## Cross-provider config` sections): rename it to
   `.wi/models.md` and set its frontmatter to `type: Model Routing Config` — the section format is
   unchanged. Never re-ask an existing config.
2. **Open the feature folder — or resume the one already open.** Parse flags: `--auto` sets **Gate mode:
   auto-approve** in progress.md — tell the user the design gate will be auto-approved and recorded, not
   asked. Then **check before creating** — the slug ordinal, then whether this idea is new, a resume, or a
   collision:
   - **Legacy migration:** a repo whose work units still live under the pre-rename folder gets a one-time
     `git mv .wi/goals .wi/features` before proceeding — commit it; the dossiers inside are untouched.
   - **Ordinal assignment:** Derive a kebab-case name, then prefix the **next global 4-digit ordinal** so
     `<slug>` = `NNNN-<name>` (e.g. `0001-stripe-webhooks`) — mirroring `ADR-NNNN`: the ordinal is global
     across `.wi/features/`, monotonic, assigned **once at creation, never renumbered** (next = highest
     existing `.wi/features/` ordinal + 1, else `0001`; legacy unnumbered features are left as-is and ignored by
     the scan; a resumed feature keeps its number; a roadmap row's name is numbered when its folder is first
     created).
   - **Resume detection:** Scan `.wi/features/*/progress.md` for Phase ≠ `done`. One matches this idea
     (same/near slug, or a title that reads as the same feature)? Then this is a **resume, not a new feature**:
     re-read its progress.md, announce the phase and what's left (ticked tasks, recorded decisions), and
     re-enter that phase — research/build/ship all re-enter from progress.md (workflow.md). Never seed a
     second folder for the same feature; never overwrite an existing dossier.
   - **In-flight overlap:** Idea is new but other features are in flight: say so in one line (slug + phase
     each). If their `tasks.md` files overlap this idea's likely surface, run sequentially — two features
     editing the same module trades merge conflicts for wall-clock.
   - **Done-slug collision:** Slug collides with a **done** feature: the global ordinal already makes the new
     folder unique (it gets the next number), so the kebab name may safely repeat across ordinals; only add
     a `-2` suffix to disambiguate identical names when scanning. A finished dossier is history, not a
     scratch folder.
   - **Roadmap match & dependency stacking:** if `.wi/roadmap.md` exists and this idea is one of its rows,
     use the row's slug, mark it `in-progress`, and carry the row's notes + sequencing rationale into
     brainstorm as seed context — the WHAT was part-captured when the roadmap was written, so brainstorm
     gets shorter, not skipped. Check its **Depends on**: a dependency that is done-but-unmerged (PR still
     open) means this feature would build against code `main` doesn't have — ask once (inside the brainstorm
     stop, like the preflight): wait for the merge, **stack** this branch on the dependency's branch (record
     it in progress.md; retarget the PR after the dep merges), or proceed off `main` deliberately.
   Only then create `.wi/features/<slug>/` and seed `progress.md` (template in the research skill's
   `wi-directory.md`). Every Log line — the `**Created**` seed included — opens with a full ISO-8601
   timestamp from the OS clock (`date -Iseconds`, or `python
   ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/now.py`); ship computes the run's timing from these
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
     progress.md that the run ends at ship's no-remote close-out (ship §7) and the keep-alive applies once
     a remote exists. (All checks resolve inside the brainstorm stop — they are not a new gate.)
   Both green → recap the brief in 3-5 lines, then print the keep-alive handoff for the current platform:
   Claude Code & Codex CLI arm their built-in `/goal` with the PR-open condition; Copilot CLI relaunches
   under Autopilot. The exact command templates — and the unattended-run warning that must accompany the
   Copilot one — live in `${CLAUDE_PLUGIN_ROOT}/references/keep-alive.md`; print them from there verbatim.

   Armed, the run continues across turns until the condition holds (wi works without it, just less
   robustly through a stalled turn). The per-platform mechanism is in
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
   and the final report including the token table. **No questions anywhere in this stretch**; decisions
   get made, recorded, and moved past.

## Boundaries

- User interactions by mode: **interactive** = brainstorm + a one-line handoff confirmation + the design
  gate; **`--auto`** = brainstorm only (no handoff confirmation, gate auto-approved and recorded). Never
  stop for anything else.
- If brainstorming reveals several features, capture them in `.wi/roadmap.md` — committed where written
  (`docs(wi): roadmap`) — and run each as its own `/wi:dev`. One feature = one PR.
- **Mid-run user input is routed, never absorbed silently.** If the user interjects during the autonomous
  stretch, record the message in progress.md (Decisions/blockers), then route it: small and inside the
  approved spec → append a task to `tasks.md` (build schedules it like any other); out-of-scope → a
  `roadmap.md` line (tell them which feature it became); contradicts the approved design/ADR → pause,
  re-open the design gate with a delta summary (approve / amend / stop), continue on the answer. The run
  never derails on input, and input never vanishes.
- **Superpowers precedence:** during a run, superpowers skills fire only at wi's delegation points
  (`${CLAUDE_PLUGIN_ROOT}/skills/research/references/integrations.md`) — never self-triggered mid-phase;
  wi's artifact formats always win.
- Keep dev thin: it sequences; the phase skills do the work; the keep-alive loop (`/goal` or Autopilot) keeps it alive.
