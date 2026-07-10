---
type: Report
title: "Pile 1 before/after dry-run comparison — #36 #37 #38 (v1.6.0 → v1.7.0)"
description: "Two identical /wi:dev --auto dry-runs on the same notes-cli fixture — one against main @ 63b4cc9 (v1.6.0), one against pile1-context-budget @ 2c687b8 (v1.7.0) — mechanism verification and objective sidecar token accounting."
timestamp: 2026-07-10
tags: [testing, dry-run, context-budget, tokens]
---

# Pile 1 before/after dry-run comparison (2026-07-10)

**Method.** Two dry-runs with byte-identical procedure prompts (only SUT/sandbox paths differ), the same
deterministic fixture (a 2-commit, 3-test stdlib `notes-cli`), the same feature idea (`add a search <term>
command…`), the same invocation (`/wi:dev … --auto`, headless), and the same pinned dry-run-agent model
(opus). SUTs were detached git worktrees: **before** = main @ `63b4cc9` (v1.6.0), **after** =
`pile1-context-budget` @ `2c687b8` (v1.7.0). Neither agent knew a comparison existed. Token/behavior
figures below come from parsing each agent's full sidecar transcript with the same stdlib analyzer
(assistant-turn `usage` sums + tool-call census) — the two in-run `token_report.py` orchestrator figures
are excluded as ambiguous inside nested agents. Harness mirrors `2026-07-03-dry-run-dev-rpa.md` (§5),
boundaries B1/B3/B4/B5/B7.

## Mechanism verification — every pile-1 behavior engaged as written

| Mechanism (issue) | Before (v1.6.0) | After (v1.7.0) |
|---|---|---|
| Routing source (#38) | `references/models.md` read at setup; per-dispatch resolution re-derived from it | `## Model routing (resolved)` block written once at dev §1, committed in the dossier; **every dispatch's logged model determinant = a block cell** |
| Model assignments (#38 AC) | checker=opus ×2 · researcher=sonnet · task-runner=sonnet | **identical** — checker=opus ×2 · researcher=sonnet · task-runner=sonnet ×2 |
| Gate outputs (#36) | piped inline (`\| tail -8/-12`) to console; nothing on disk | redirected — `.logs/w1-tests.txt` (wave gate), `.logs/gate-tests.txt` (ship §1); exit code + tail read; **2 redirect-into-`.logs/` Bash calls observed** (before: 0) |
| `.logs/` lifecycle (#36 AC) | n/a (concept absent) | created self-gitignored → absent from `git status` → pruned at ship §6 → **absent from the final tree** (verified on the branch) |
| Dossier after done | 7-file exact | 7-file exact (block rides inside `progress.md`) |
| Repeat Reads (#37) | 0 repeats (28 unique files) | 0 repeats (31 unique files) — discipline now rule-backed (each phase skill cites the budget) rather than dispositional |
| STAMP_RE safety (#38) | n/a | block stamp is mid-line (`- resolved 2026-07-10T22:25:45+03:00 from …`) — cannot match `token_report.py`'s line-initial stamp regex |
| Gates/verdicts | all green; Phase=done | all green; Phase=done — no gate weakened, no missing-context stall, checker passes had their inputs |

## Objective sidecar accounting — and its honest interpretation

| metric | before | after | Δ |
|---|---|---|---|
| assistant turns | 277 | 335 | +21% |
| fresh input | 61,874 | 61,480 | ≈0 |
| output | 135,540 | 140,043 | +3% |
| cache-write | 1,666,655 | 2,221,358 | +33% |
| cache-read | 43,376,608 | 56,683,270 | +31% |
| cache-read / turn | ≈156.6K | ≈169.2K | +8% |
| wi dispatches / exact tokens | 4 / 175,761 | 5 / 170,716 | +1 / −3% |

**The totals moved up, and the pile is not the reason — run shape is.** The two runs are not
shape-identical: the after-run's plan phase decomposed the feature into **2 tasks** (before: 1), adding a
dispatch, a second TDD cycle, extra wave bookkeeping and commits; it also hit one self-corrected
sequencing slip (build state first written to main's dossier copy, then relocated to the worktree —
its D3) that cost a multi-turn detour. Longer runs also compound: the marginal late turns are the most
expensive ones, so +21% turns yields +31% cache-read.

**This fixture cannot demonstrate #36/#37's savings by construction.** The whole gate output is ~10
lines (6 unit tests), the diff is 2 small files, there is no CI — so redirecting output saves
approximately nothing here, while v1.7.0's added instruction text (net ≈ +180 lines across the always-read
skills) is a small real per-turn cost the micro-run does pay. The issues' savings case rests on the
measured ~75× re-read amplification on real-scale features (the 0009-guardian-invite evidence run:
231.8M cache-read / 585 turns), where a single 3k-token test log or whole-diff read costs ~200k+
cache-read over the run's remainder. **Conclusion: mechanisms verified operationally with zero behavior
regression; magnitude must be measured on the next real feature** (the sweep's Checkpoint B real-run gate
for #42 is the natural slot — read this comparison's table again beside that run's `token_report.py`).

## Side-output: spec findings from the two runs (candidate follow-up issues, none in this PR's scope)

Both runs, independently, surfaced overlapping findings in v1.6.0-era text that pile 1 does not touch:

1. **Checker verdict-marker ambiguity** — an INFO-only result returns `## ISSUES FOUND`; anything keying
   on `## CHECK PASSED` misreads an all-clear (`agents/wi-code-checker.md` output contract).
2. **Design-gate commit ordering vs `--auto` phase flip** — the dossier commit precedes the
   auto-approve/phase=build write, leaving main dirty or the worktree behind; both runs self-corrected
   (research §3 / build §1 seam).
3. **Build+ship wall-clock span structurally `unavailable` under the no-remote close-out** — the span end
   is the `PR opened` stamp, which that close-out never writes; also interacts with ship §6 finalizing
   `tokens.md` before §7/§8 exist (`token_report.py` + ship §6.3/§7).
4. **Worktree-tool precedence** — build §1 mandates `superpowers:using-git-worktrees`, whose native
   harness tool targets the harness repo, not necessarily the repo wi is operating on (sandbox/multi-repo
   case); both runs needed the git fallback plus judgment.
5. **Headless carve-outs incomplete** — brainstorm's delegate hard-gates on user approval, and scan §4/§5
   ask AskUserQuestion, with no explicit headless-supersede line like dev §1's (`skills/brainstorm/SKILL.md`,
   `skills/scan/SKILL.md`).

## Evidence

- Fixture + procedure: this repo's scratchpad session (`make_fixture.sh`, `dryrun-procedure.md`); sandboxes
  `db/` (before) and `da/` (after), each ending with branch `wi/0001-search-command` merge-ready and
  `Phase = done` under the no-remote close-out.
- Sidecar transcripts: session `subagents/agent-a7484a9f0cfab03cf.jsonl` (before) and
  `agent-adc00ffc41c630398.jsonl` (after), analyzed with `analyze_sidecar.py` (stdlib; same code for both).
- Both runs' full inline reports are preserved in the orchestrating session's transcript.
