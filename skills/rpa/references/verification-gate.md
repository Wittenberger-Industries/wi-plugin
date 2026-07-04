---
type: Reference
title: "RPA verification gate"
description: "The bar a built UiPath solution must clear before it ships."
timestamp: 2026-06-08
tags: [rpa, reference]
---

# RPA verification gate

The bar a built UiPath solution must clear before it ships. It uses UiPath's own tooling via the `uip`
CLI / the `uipath-platform` skill — wi doesn't invent checks. Run every command **non-interactively and
time-bounded** (a hands-off run must never stall on a prompt; a hang is a blocker to surface).

**Publishing is not part of this gate.** Pushing the package to a tenant (`progress.md` → `Publish: feed |
deploy`) is a separate, **post-gate** ship action that runs only on an already-green build with the PR open
(see rpa/SKILL.md step 7) — it never gates "done" and never runs on a red build.

## Framework branch (check `progress.md` → `Framework:` first)

This gate is **framework-aware**. The steps below are the **REFramework** gate. On the **Maestro** path
(`Framework: maestro`) the gate is instead: `uip maestro flow validate` (mandatory) **+** `uip maestro flow
eval` **when eval sets exist** (run-if-present, reported) — there is **no** Workflow Analyzer or
approved-paradigm check (those are REFramework-specific). The **checker (result mode)** below — the
feature-level pass plus the inline line-level review — runs on **both** paths.

## Run, in this order (per process/project) — REFramework

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
4. **House-rules sweep (constitution)** — cheap, concrete checks on the generated `.xaml` against the
   constitution + gate decisions; needs no Studio, so it runs even when the gate degrades. Each miss is a
   finding that **loops back to build**:
   - **Email approach** — units that send mail/notifications use **only the gate-confirmed approach**
     (SDD / assumptions); grep for email activities/connectors of any *other* stack (a silent
     SMTP→Outlook swap is a red gate). No confirmed approach on record → the send must be a mock tied to
     an open dep, not an implicitly chosen framework.
   - **No default activity names** — grep the `.xaml` for default DisplayNames
     (`DisplayName="Assign"`, `"If"`, `"Sequence"`, `"Log Message"`, `"Invoke Workflow File"`, …) **and**
     for common activities carrying no `DisplayName` attribute at all (Studio shows those under the default
     name too); every activity is explicitly named for what it does.
   - **Multiple Assign** — no chains of consecutive single `<Assign>` activities (grep for adjacent
     `<Assign` siblings in a Sequence); assignments that happen together are grouped in one Multiple
     Assign, a lone assignment stays a single Assign.
   - **Logging** — each major SDD step is followed by a Log Message whose text carries runtime context
     (transaction id / key values / outcome), not generic success text; levels and Add Log Fields per the
     constitution. A `Process.xaml` with no Log Message between SDD steps is a finding.
   - **Annotations** — every workflow root and the non-obvious activities/blocks carry annotations
     (`sap:Annotation.AnnotationText` / `sap2010:Annotation.AnnotationText` in the `.xaml`) explaining the
     why — decisions, branch conditions, magic values, deliberate shortcuts.
5. **(Optional) Test cases** — if test workflows exist (or the constitution requires them), run them.

Capture each command + result — these become the PR's "Testing" section. The `uip` steps above are
deliberately generic — the UiPath skills own the literal subcommands (borrow, don't reinvent). The first
time this gate runs for a project, resolve each step to its exact command via `uipath-rpa` /
`uipath-platform` and **record the resolved commands in `progress.md`'s Log** — reruns (and the keep-alive
loop) then replay them deterministically instead of re-deriving. If the `uip` CLI / Studio isn't
available in the run environment, the gate degrades to: **artifacts complete + the SDD lists the Analyzer
ruleset/criteria to pass**, and the actual Analyzer run is deferred to the user (say so explicitly — don't
claim green you didn't verify).

## Checker (result mode) — feature-level + line-level, one dispatch

Beyond the tooling above, dispatch the **checker** (`${CLAUDE_PLUGIN_ROOT}/agents/wi-code-checker.md`) in `result`
mode — **one dispatch, two sequential passes**, same interface and logging as `wi:ship` §2:

- **Feature-level pass** — against **the SDD's acceptance-criteria section** (§10 in the base ToC) + the
  locked decisions (the SDD's §1-§7, the `rpa-constitution`, any ADR): it confirms each is **delivered and
  wired in the generated project**, not just present. Coverage-level, distinct from the Analyzer's rules.
- **Line-level pass** — the same dispatch carries the code review inline. Before dispatching, resolve the
  line-review source: if `superpowers:requesting-code-review` is in your available skills, locate its
  reviewer template — the `code-reviewer.md` inside that skill's installed directory (Glob the plugin
  roots, e.g. `~/.claude/plugins/**/requesting-code-review/**/code-reviewer.md`) — and pass its absolute
  path in the dispatch as `Line review template: <path>`; absent → `Line review template: none` (the
  checker runs wi's built-in line review over the branch diff — here, the generated project). Log
  `review via wi-code-checker + superpowers:requesting-code-review[inline]` or
  `review via wi-code-checker (wi line review; superpowers absent)`.

Findings from both passes land in `verification.md` (the feature-level matrix plus its
`## Line-level findings` section) in the BLOCKER/WARNING/INFO taxonomy, refreshing it. A result-mode
**BLOCKER** — an unmet SDD criterion, a decision silently reduced to a stub/mock not signed off, or a
line-level defect of that gravity — **loops back to build** (**max 2 review→fix rounds**, shared with the
cross-provider findings when that layer is configured — `wi:ship` §2's rule); ship never opens the PR on a
run the checker says isn't met.

## What "green" means

- the build is the **expected paradigm** — XAML REFramework (or Coded only with an ADR), checked first.
- restore + validate succeed; Workflow Analyzer has **zero error-level violations**.
- the **token ledger `tokens.md` passes `check_tokens.py`** — present, with a row per delegated build unit,
  the Subagents sum filled, and a resolved `## Orchestrator` section (real figure or honest `unavailable`).
- every criterion in the SDD's acceptance-criteria section maps to something that actually passed.
- every assumption is either confirmed (gate) or recorded for sign-off; no unaddressed `NEEDS DECISION`.
- the **checker (result mode) verdict is PASS** — every SDD acceptance criterion and locked decision
  delivered and wired, and no line-level BLOCKER outstanding.

## The iron law (same as wi:dev)

No PASS without a fresh run this session — analyzer/validate output from *this* build, not quoted from
earlier and not "should pass". A red gate stops the ship: fix the workflow (loop back to build) or, if the
SDD was wrong, amend it deliberately and note it. Never weaken a rule to go green.
