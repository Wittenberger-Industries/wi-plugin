---
type: Reference
title: "The verification gate"
description: "The gate is the objective bar a feature must clear before it can ship."
timestamp: 2026-06-08
tags: [ship, reference]
---

# The verification gate

The gate is the objective bar a feature must clear before it can ship. It uses the **repo's own commands**
(from `.wit/repo-map.md`): wit doesn't invent checks, it runs the ones the project already trusts.

## The iron law

**No PASS claim without fresh verification evidence**: a command actually run in this session, its
output captured to the log, its exit code + tail read. Before writing any "green" / "passed":
1. name the command that proves it; 2. run it now, output redirected per workflow.md's output
house rule; 3. read the exit code + the log's tail (the full output stays on disk; grep it on
red); 4. confirm it matches the claim. Only then report pass.

Red flags that mean you have NOT verified (stop and run the command):
- "should pass", "probably clean", "looks good", "that change is safe";
- quoting a result from an earlier message instead of a fresh run;
- expressing satisfaction before the command has actually run.

This is the line between a gate and a guess.

## Run, in this order

1. **Format check**: e.g. `ruff format --check .` / `prettier --check`. Fast, catches noise.
2. **Lint**: e.g. `ruff check .` / `eslint .`. Zero new violations.
3. **Typecheck**: e.g. `mypy <pkg>` / `tsc --noEmit`. New code must type-check.
4. **Tests (full suite)**: e.g. `pytest` / `pnpm test` / `go test ./...`. All green, no skips that hide
   the new behavior.
5. **CI-equivalent**: if `repo-map.md` records a `make ci` / workflow command, run it; it's the real
   merge bar.

Capture the actual command + result for each; these become the PR's "Testing" section.

## Run commands defensively (a hands-off run must never stall)

These commands run unattended, so any one that blocks on input hangs the entire run. Defend every command:
- **Force non-interactive.** Close stdin (POSIX `< /dev/null`; PowerShell `-NonInteractive` + redirect)
  and pass the tool's own flag when it has one (`--yes`, `--no-input`, `--non-interactive`, `CI=1`).
- **Bound it with a timeout.** Wrap long/external commands (packaging, export, publish, deploy, docker)
  so they cannot run forever. A command that exceeds its timeout is a **blocker to surface**: record it
  in `progress.md` and report it; never silently wait and burn the loop.
- **Prefer the inner seam over the wrapper.** If a CLI wrapper is what hangs (it shells out to
  pack/publish), verify through the library/generation call it wraps and flag the wrapper hang as an
  environmental note. (Real run: a UiPath `export` CLI hung in `uv run uipath pack`; the run verified
  through the exporter's generation call and flagged the CLI; that is the right move.)

## What "green" means

- Every command above exits 0 (or matches the project's defined success).
- Every **acceptance criterion** in `spec.md` maps to at least one check that passed. If a criterion has
  no corresponding check, it is **not** verified: add the test before shipping.
- Every applicable **pitfall** in `pitfalls.md` is either prevented by a passing test or explicitly
  argued as not-applicable in the PR.

## When the gate is red

Stop. A red gate is information, not an obstacle to route around. **Before any fix option**, append one
stamped Log line to the feature's `progress.md`:

`- <ts> **Reflection** <check that failed>: <what went wrong, one clause> - earlier catch: <phase | none>`

(`<ts>` from the OS clock; `earlier catch` is the phase that should have caught it - research, plan,
build, or `none`.) Then options, in order of preference:

1. Fix the code (loop back to the build phase for the failing task).
2. If a test is genuinely wrong, change it **deliberately** and say why in the PR; never delete a test
   just to go green.
3. If the failure shows the plan was wrong, amend `spec.md`/`tasks.md` and rebuild the affected part.

## Coverage & flakiness (if the project cares)

- If the constitution sets a coverage bar, check it; don't chase 100%.
- Re-run a suspected flaky test in isolation before blaming the change. A flaky test discovered here is
  worth a note (or a quick fix) so it doesn't erode the gate's credibility.

## Don't gold-plate

The gate proves the feature's acceptance criteria, not the whole codebase's perfection. Resist expanding
scope to fix unrelated issues you notice: log them (a new feature or a roadmap line) and ship the feature you
planned.

## This gate is the local half

Passing here proves the worktree, not the PR. The PR's **remote checks**, CI runs and deployment checks
(e.g. Vercel), trigger after the push and are verified at ship:8, after the PR opens. The final report
names the two separately: `local gate: green · PR checks: N/N green · deployment: ready`.
