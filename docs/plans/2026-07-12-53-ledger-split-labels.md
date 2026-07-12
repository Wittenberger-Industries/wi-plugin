---
type: Plan
title: "#53 ledger split labels: name the per-subagent split rows from meta.json description"
description: "token_report.py labels each Subagent detail row from the harness's agent-<id>.meta.json description (fallback: agentType short name, then the dispatch prompt prefix) instead of a 48-char prompt-prefix, and the ledger rule gains the description==Source convention so the split and ledger tables are joinable by name."
feature: 53-ledger-split-labels
timestamp: 2026-07-12
tags: [plan, ship, tokens, consistency]
---

# #53 ledger split labels

## Problem (from the issue AC)

The `## Subagent detail` split that `token_report.py --write` appends to `tokens.md` labels each row
with a 48-char truncation of the dispatch prompt's first user message plus the agent id. Every
task-runner row opens with the same charter boilerplate, so the split is a wall of near-identical
prefixes that a reader cannot match against the ledger's human `Source` names. The two tables describe
the same dispatches and should share names.

## Verified mechanics (on-disk, this repo)

- `parse_agent_file()` in `skills/ship/scripts/token_report.py` builds `label` from the first
  `user`-type message text, whitespace-collapsed, `|`->`/`, `[:48]`. Nothing else is consulted.
- The harness writes a sidecar `agent-<id>.meta.json` beside every `agent-<id>.jsonl`, confirmed shape:
  `{"agentType":"wi:wi-researcher","description":"Research search-command seam","toolUseId":"...","spawnDepth":2}`.
  The `description` is the 3-5 word dispatch description (the same field the Agent tool takes), which is
  exactly the material the ledger `Source` column already uses.
- The ledger `Source` names are authored by the orchestrator at notification time; the sidecar files
  never contain them. So the join needs a shared naming convention, not a shared key.

## Approach (option 1 from the issue: one name, written twice by convention)

1. **Code.** `parse_agent_file()` reads the sidecar meta.json and labels each row from a fallback chain:
   `description` -> `agentType` short name (namespace prefix stripped) -> today's prompt-prefix ->
   `(no prompt)`. Same normalization applied to whichever wins (collapse whitespace, `|`->`/`, `[:48]`).
   A missing or unparseable meta.json falls straight through to the prompt-prefix: current behavior,
   never a crash.
2. **Convention.** Add one line to the ledger rule in `wi-directory.md`: author each row's `Source` with
   the same short string passed as the dispatch's `description`, so the split (labeled from meta.json
   `description`) and the ledger row (labeled `Source`) carry the same name and join by eye.

Chosen over option 2 (id-join) because it leaves the ledger byte format untouched: `_ledger.py`,
`check_tokens.py`, and `tests/test_tokens_guardrail.py`'s ledger assertions are not touched, so this does
not collide with the #48 surface.

## Tasks (TDD, one test-first slice each)

1. `_read_agent_meta(path)` helper: returns the parsed sidecar dict or `{}` on absent/unreadable/invalid
   JSON. Test: present -> dict; absent -> `{}`; garbage bytes -> `{}`.
2. `parse_agent_file()` label fallback chain. Tests (fixtures = a minimal `agent-<id>.jsonl` with one
   usage record, plus/minus a sibling meta.json):
   - meta with `description` -> label is the description.
   - meta with empty/absent `description` but an `agentType` -> label is the short agent type.
   - no meta.json -> label is the prompt prefix (unchanged legacy behavior).
   - normalization + 48-char cap still applied to the winning source.
3. `--write` integration: a split row's first cell verbatim-contains the meta `description`, so it
   matches a ledger `Source` of the same name; re-running `--write` stays idempotent (section replaced,
   not duplicated); the count-mismatch note still fires when `len(agents) < ledger_rows`.
4. Doc: the `description`==`Source` convention line in `wi-directory.md` (ledger rule + a note in the
   subagent-detail paragraph naming meta.json `description` as the label source).
5. Manifests: minor bump 1.9.10 -> 1.10.0 in all three (artifact-format change, house rule).

## Success criteria (issue AC)

- Every split row's first cell equals or verbatim-contains the corresponding ledger `Source` name.
- Graceful fallback when meta.json is absent (older sessions, Codex/Copilot): current behavior, no crash.
- `python scripts/validate.py` + `pytest tests/` green; `check_tokens.py` still accepts the file.
- `--write` on an already-finalized tokens.md stays idempotent.

## Out of scope

- No ledger byte-format change (rules out option 2's id suffix).
- No change to how `Source` is authored at runtime beyond the one convention line.
