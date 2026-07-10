---
type: Implementation Plan
title: "#35 + extensions — wall-clock timing, per-subagent token split, cost estimate"
description: Task-by-task plan for issue #35 (full-timestamp Log, tokens.md Duration column, Σ-compute + autonomous wall-clock, ship timing table) plus the Claude Code per-subagent split/cost-estimate and Copilot AI-credits extensions.
timestamp: 2026-07-10
tags: [tokens, timing, cost, observability, plan]
---

# #35 + extensions — wall-clock timing, per-subagent token split, cost estimate

**Goal:** implement issue #35 (full-timestamp `progress.md` log, per-subagent `Duration` in `tokens.md`, Σ-compute + autonomous-wall-clock totals, ship timing table) **plus two extensions requested 2026-07-10:** (A) on Claude Code, recover each subagent's exact input/output/cache-write/cache-read split (and model) so cost can be estimated properly; (B) on Copilot CLI, account for premium requests ("AI credits") as far as the platform allows.

**Architecture:** everything stays inside the existing token-ledger pattern. `_ledger.py` remains the sole owner of the `tokens.md` byte format (new `Duration` column + two totals lines). A new trivial `now.py` prints the OS clock as ISO-8601-with-offset for Log stamps. `token_report.py --write` — already the ship-time finalizer — gains three jobs: compute the autonomous wall-clock from `progress.md` phase spans, compute Σ compute from the ledger's Duration cells, and (Claude Code only) parse the session's `subagents/agent-*.jsonl` sidecar transcripts into an exact per-agent split/duration/cost section. Skills only gain one-line instructions at existing stamp/append points.

**Tech stack:** Python 3 stdlib only (repo convention); markdown skill edits; `tests/test_tokens_guardrail.py` + new `tests/test_timing_report.py`.

## Evidence the extensions rest on (verified 2026-07-10 on this machine)

- Claude Code persists each subagent transcript at `~/.claude/projects/<proj>/<session-id>/subagents/agent-<agentId>.jsonl`. Every assistant line carries `message.usage` (`input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`), `message.model` (exact ID, e.g. `claude-opus-4-8`), and an OS `timestamp`; the first user line carries the dispatch prompt. 489 such files exist locally.
- The main session transcript's `toolUseResult` entries carry `agentId` + `resolvedModel` per dispatch — confirming sidecar files belong to the session (the directory layout already guarantees it).
- List prices per MTok (claude-api skill, cached 2026-06-24): Fable 5 / Mythos 5 $10/$50 · Opus 4.8/4.7/4.6/4.5 $5/$25 · Sonnet 5 / 4.6 / 4.5 $3/$15 · Haiku 4.5 $1/$5. Cache read ≈ 0.1× input; cache write 1.25× input (5-minute TTL — Claude Code's default).
- Copilot CLI: findings from the web-research pass land in Task 8; the honesty rule (exact-or-`unavailable`, never estimated) governs whatever the platform doesn't expose.

## Global constraints

- **Never let the model invent a number.** Timestamps come from `date -Iseconds` / `now.py`; durations from those stamps or transcripts; token splits from transcript `usage` records. Anything unobtainable is written `unavailable`.
- **Cost is explicitly labeled an estimate** (exact tokens × published list prices, "as of" date shown); token figures themselves stay exact-or-unavailable.
- **Backward compatible:** a legacy 4-column `tokens.md` (no Duration) must still pass `check_tokens.py`; the new duration/totals gate applies only when the header carries the Duration column.
- `_ledger.py` stays the single owner of `tokens.md` bytes; scripts stay stdlib-only, no new deps.
- Version bump to **1.6.0** in `.claude-plugin/plugin.json` AND the plugin entry in `.claude-plugin/marketplace.json`.
- No commits until the user says so (squash-merge PR convention, no AI attribution).

---

### Task 1: duration + timestamp helpers in `_ledger.py` (TDD)

**Files:** modify `skills/ship/scripts/_ledger.py`; test `tests/test_tokens_guardrail.py`.

- `format_duration(seconds)` → `"3m12s"` / `"1h03m22s"` / `"42s"`; `None`/negative → `"unavailable"`.
- `parse_duration(text)` → seconds (int) or `None` for `unavailable`/unparseable. Round-trip property.
- `TEMPLATE` gains the `Duration` column (header, separator, orchestrator row cell: `n/a (see below)`) and, after the existing sum line, two seeded totals lines:

```markdown
**Subagents (exact): <sum>.**
**Σ compute: <dur> across <n> dispatches.**
**Autonomous wall-clock (excl. manual steps): <dur>.**
```

- New `set_compute_totals(text, compute_seconds, n_dispatches, wall_seconds)` filling both lines (each side independently `unavailable` when `None`); `compute_totals_filled(text)` (filled = not the `<dur>`/`<n>` placeholders).
- `verify(path)` extension: **iff** the table header contains `| Duration |` → additionally fail when (a) any data row's Duration cell is empty/placeholder (`unavailable` passes), or (b) either totals line still holds placeholders (`unavailable` passes). Header without Duration → legacy, no new checks.

**Steps:** write failing tests (round-trip, template markers, verify matrix incl. legacy pass) → run red → implement → run green: `python -m pytest tests/test_tokens_guardrail.py -q`.

### Task 2: `now.py` — the OS-clock stamp helper

**Files:** create `skills/ship/scripts/now.py`; test in `tests/test_timing_report.py`.

```python
#!/usr/bin/env python3
"""now.py — print the OS clock as ISO-8601 with offset (e.g. 2026-07-10T18:23:45+02:00).
The Log-stamp source of truth on platforms without `date -Iseconds`. Stdlib only."""
from datetime import datetime

if __name__ == "__main__":
    print(datetime.now().astimezone().isoformat(timespec="seconds"))
```

Test: output parses with `datetime.fromisoformat`, has tz offset. Skills will cite: `date -Iseconds` (POSIX shells) or `python ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/now.py`.

### Task 3: progress-span parser + wall-clock (TDD)

**Files:** modify `skills/ship/scripts/token_report.py`; test `tests/test_timing_report.py`.

- `parse_progress_spans(text)` → `(span1_seconds, span2_seconds)` each `int|None`, from `## Log` lines opening with a full ISO stamp:
  - span 1 (research+plan, gate 1 → gate 2) = ts(first line matching `design gate opened`) − ts(first `phase = research`)
  - span 2 (build+ship, gate 2 → end) = ts(last `PR opened`, else last `phase = done`) − ts(last `design gate approved` or `design gate auto-approved`)
  - Tolerant regex `^\s*-\s*(\d{4}-\d{2}-\d{2}T[\d:.+\-Z]+)\s`; date-only or missing boundary → that span `None`. Negative span → `None` (clock skew honesty).
- Wall-clock total = sum of available spans; both `None` → `None` → `unavailable`. Sum-of-spans by construction excludes brainstorm, the handoff, the gate wait, and paused/multi-day idle time.
- `run_write` reads sibling `progress.md` (`tokens_path.parent / "progress.md"`; optional `--progress` override), computes Σ compute (sum of parseable Duration cells + dispatch count from data rows) and calls `set_compute_totals`.

### Task 4: subagent split, duration, and cost estimate (Claude Code) (TDD)

**Files:** modify `skills/ship/scripts/token_report.py`; `_ledger.py` (tail-replace helper); tests with a synthetic `subagents/` fixture.

- Prices table (module constants):

```python
PRICES_AS_OF = "2026-06-24"          # list prices, USD per MTok (input, output)
PRICES = {  # longest-prefix match on message.model; cache: read 0.1x in, write 1.25x in (5m TTL)
    "claude-fable-5": (10, 50), "claude-mythos-5": (10, 50),
    "claude-opus-4-8": (5, 25), "claude-opus-4-7": (5, 25),
    "claude-opus-4-6": (5, 25), "claude-opus-4-5": (5, 25),
    "claude-sonnet-5": (3, 15), "claude-sonnet-4-6": (3, 15), "claude-sonnet-4-5": (3, 15),
    "claude-haiku-4-5": (1, 5),
}
def estimate_cost(model, tot):  # -> float | None (None = no price on file)
```

- `parse_agent_file(path)` → dict: `agent` (id from filename), `model` (last seen), split totals, `duration` (last−first line `timestamp`, `None` if unparseable), `label` (first user text, one line, ≤48 chars, `|`→`/`).
- `find_subagent_files(transcript_path)` → sorted `transcript_path.with_suffix('') / "subagents" / agent-*.jsonl` (empty list when absent — non-Claude platforms or no dispatches).
- Section rendered by `--write` (regenerated idempotently on re-run), appended after the Orchestrator body via a new `_ledger.replace_tail(text, orchestrator_body, extra_sections)` that keeps `## Orchestrator`'s replace-to-EOF semantics:

```markdown
## Subagent detail (exact, from agent transcripts)

| Agent | Model | In | Out | Cache-w | Cache-r | Duration | Est. cost |
|-------|-------|----|-----|---------|---------|----------|-----------|
| task-runner: Task 3 — … (a1b2c3) | claude-opus-4-8 | 121,727 | 40,697 | 789,808 | 8,359,142 | 14m02s | $2.53 |

Split covers 5 of 6 ledger rows — a resumed run's earlier sessions aren't in this transcript dir.
**Cost (estimate, list prices as of 2026-06-24, cache-write at 5m TTL): subagents $X.XX + orchestrator $Y.YY = $Z.ZZ**, plus N unpriced row(s).
```

- Orchestrator cost: same formula over the main-transcript totals; orchestrator model = most frequent `message.model` in the main transcript. Unknown model → `n/a (no price on file)`, excluded from the total with the explicit `unpriced` note. The coverage line prints only when split rows < ledger data rows.
- Fixture tests: 2 synthetic agent files (one priced model, one unknown) + main transcript + progress.md → assert per-agent split, duration arithmetic, cost math to the cent, unpriced handling, coverage note, idempotent second `--write`.

### Task 5: template + reference docs (`wi-directory.md`, `workflow.md`, `moa.md`)

**Files:** `skills/research/references/wi-directory.md`, `skills/research/references/workflow.md`, `references/moa.md`.

- `wi-directory.md`: OKF Log note "ISO dates" → "full ISO-8601 timestamps (date+time+offset, from the OS clock — `date -Iseconds` or `ship/scripts/now.py` — never model-estimated)"; progress template Log line → `- <YYYY-MM-DDTHH:MM:SS±hh:mm> **Created** feature, phase = brainstorm`; tokens template block updated to v2 (Duration column, totals lines, subagent-detail section note, cost-estimate note, Copilot basis note from Task 8).
- `workflow.md` §Token budget: one sentence — time is measured like tokens (stamps at phase flips; per-dispatch durations; ship computes Σ compute + autonomous wall-clock as sum of phase spans).
- `moa.md` token-ledger paragraph: proposer/aggregator rows carry `Duration` like any dispatch row.

### Task 6: stamp + Duration-cell instructions in the skills

**Files:** `skills/dev/SKILL.md` (step 2 seed stamp, step 4 `phase = research` stamp), `skills/research/SKILL.md` (§0 engaged, §1d `phase = plan`, §2 `design gate opened`, §3 gate outcome, §1c/§1d/MoA/§2 rows carry Duration), `skills/build/SKILL.md` (engaged line = build start; §2.4 append Duration cell from the completion notification's elapsed time or dispatch/arrival stamps, else `unavailable`), `skills/ship/SKILL.md` (new first-act `ship engine engaged` stamp — ship currently has none; §2 MoA rows; §6.3 finalize note — `token_report.py --write` now also fills durations/totals/split; §8 timing table in the final report, read from the finalized files, not recomputed:)

```
Timing (autonomous, manual waits excluded)
  research + plan (gate 1 → gate 2):  <span1>
  build + ship (gate 2 → PR):         <span2>
  autonomous total:                   <wall>
  Σ subagent compute:                 <dur> across <N> dispatches
```

- `skills/rpa/SKILL.md` step with checker rows (~line 88): the appended row carries its Duration cell too (one clause; rpa reuses ship, so everything else is inherited).
- Every stamp instruction names the OS-clock source once per file; keep edits to one line per site (this is #35, not the #41 rewrite).

### Task 7: `check_tokens.py` gate & close-out checklist wiring

**Files:** `skills/ship/scripts/check_tokens.py` (no code change expected — `verify` lives in `_ledger`; confirm), `skills/ship/SKILL.md` §8 checklist bullet: the tokens.md box now also fails on missing durations/totals for v2 ledgers (`unavailable` passes). Test: v2 ledger with unfilled totals exits 1 via CLI; legacy 4-col ledger exits 0.

### Task 8: Copilot premium requests / AI credits (scope set by research findings)

**Files:** `references/copilot-tools.md` (+ the tokens template note from Task 5).

Design rule regardless of findings: Copilot CLI's `task` dispatches don't emit Claude-style usage notifications, so per-subagent rows on Copilot record `unavailable (Copilot CLI exposes no per-task usage)` — honesty over invention. Add to `copilot-tools.md` a "Usage / AI credits" mapping section: what the CLI exposes in-session (e.g. `/usage`), that wi records a run-level premium-request figure only when a real figure is on screen to copy (else `unavailable`), and the post-hoc sources (GitHub billing usage report / API) for reconciling a run's cost. Exact command names/paths come from the completed research pass; if the researcher found a machine-readable source (state file under `~/.copilot/`, flag, or API), wire it as the recorded basis.

### Task 9: version bump + full verification

- `.claude-plugin/plugin.json` and `marketplace.json` plugin entry → `1.6.0`.
- `python scripts/validate.py` green; `python -m pytest tests/ -q` green; file-tail check on every edited markdown (truncated-write hazard).
- Manual spot-check: run `token_report.py --write` against a real past feature's `tokens.md` copy (scratch dir) with this session's transcript to see the split section render on live data.

## Out of scope (unchanged from the issue)

Recovering timing/splits for past runs; per-tool-call metrics; any change to how live token counts are captured; #36–#42 (later PRs per `2026-07-10-issue-triage-35-42.md`).
