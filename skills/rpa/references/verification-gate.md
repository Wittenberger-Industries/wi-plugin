# RPA verification gate

The bar a built UiPath solution must clear before it ships. It uses UiPath's own tooling via the `uip`
CLI / the `uipath-platform` skill — wi doesn't invent checks. Run every command **non-interactively and
time-bounded** (a hands-off run must never stall on a prompt; a hang is a blocker to surface).

## Run, in this order (per process/project)

0. **Approved paradigm (format) — check first, no tooling needed.** The build must match the **paradigm the
   user approved at the design gate** (`progress.md` → `Build paradigm:`). It is always REFramework
   (`project.json` on the REFramework template; `Main.xaml`/`Framework/*.xaml`/`Process.xaml` as `.xaml`). If
   **XAML-only** was approved: **no `.cs` / `.codedworkflows` AND no Invoke Code activity** — grep the `.xaml`
   for the `InvokeCode` **activity** (procedural code blocks — **not** normal Assign/If expressions, which are
   fine), and check for any `.cs`; **any** of those is a **red gate, loop back to build** (HARD rule — no
   Invoke-Code exception). If **coded-allowed** was approved: coded `.cs`
   workflows are fine. Building against the *un*approved paradigm is a red gate even if it validates and the
   Analyzer is clean.
1. **Dependencies restore** — `uip restore` (or the project's documented restore) so packages resolve.
2. **Project validates** — `uip` project validation / build; `project.json` is well-formed; no missing
   invoked workflows or arguments.
3. **Workflow Analyzer** — run the analyzer; **all error-level rules must pass** (naming, unused
   variables, empty catches, hardcoded values, args direction, etc. per the project's ruleset). Warnings
   are reported, not necessarily blocking (the constitution sets the bar).
4. **(Optional) Test cases** — if test workflows exist (or the constitution requires them), run them.

Capture each command + result — these become the PR's "Testing" section. If the `uip` CLI / Studio isn't
available in the run environment, the gate degrades to: **artifacts complete + the SDD lists the Analyzer
ruleset/criteria to pass**, and the actual Analyzer run is deferred to the user (say so explicitly — don't
claim green you didn't verify).

## What "green" means

- the build is the **expected paradigm** — XAML REFramework (or Coded only with an ADR), checked first.
- restore + validate succeed; Workflow Analyzer has **zero error-level violations**.
- the **token report `tokens.md` exists** and lists each delegated build unit's tokens.
- every SDD acceptance criterion (§13) maps to something that actually passed.
- every assumption is either confirmed (gate) or recorded for sign-off; no unaddressed `NEEDS DECISION`.

## The iron law (same as wi:dev)

No PASS without a fresh run this session — analyzer/validate output from *this* build, not quoted from
earlier and not "should pass". A red gate stops the ship: fix the workflow (loop back to build) or, if the
SDD was wrong, amend it deliberately and note it. Never weaken a rule to go green.
