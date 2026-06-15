---
type: Plan
title: "Harder guardrails for tokens.md implementation plan"
description: Task-by-task plan for the tokens.md scaffold + script-write + blocking ship gate, across the dev and rpa flows.
timestamp: 2026-06-15
tags: [tokens, ship, guardrail, plan]
---

# Harder guardrails for tokens.md Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the per-goal token ledger (`tokens.md`) impossible to silently skip — a deterministic scaffold, a script that writes the orchestrator total into the file, and a structural close-out gate whose non-zero exit blocks the PR on a genuine skip (but never on an honest "can't measure").

**Architecture:** Three stdlib-only Python files under `skills/ship/scripts/`: a shared non-entrypoint helper `_ledger.py` (template, table/section parsing, the `verify()` gate logic), plus the two scripts the skills actually invoke — `check_tokens.py` (`--init` idempotent scaffold; default = verify gate) and `token_report.py` (existing transcript parser, gains `--write` to finalize the Orchestrator section + recompute the Subagents sum). Skill prose in the dev flow (research/build/ship) and the rpa flow is rewired to call these scripts instead of describing the steps in prose.

**Tech Stack:** Python 3 stdlib only (`re`, `json`, `argparse`, `pathlib`, `datetime`) — no new deps. Tests: stdlib `unittest` via `python -m unittest discover -s tests`, driving the scripts as subprocesses (faithful to the CLI + exit-code contract). Markdown skills with OKF frontmatter; `scripts/validate.py` for manifest/frontmatter checks.

**Spec:** `docs/specs/2026-06-15-tokens-md-guardrails-design.md` (read it first — problem, the four skip points, the "subagent counts are unrecoverable" constraint, and acceptance criteria 1–11).

---

## File Structure

- **Create** `skills/ship/scripts/_ledger.py` — shared helpers: `TEMPLATE`/`make_template`, `UNAVAILABLE` sentinel, table-row + Subagents-sum + Orchestrator-section parsing/rewriting, `parse_frontmatter`, and `verify()` (returns `None` on pass or a one-line reason). Single responsibility: the tokens.md *file format*. Imported by both scripts (same dir → on `sys.path` when run as a script).
- **Create** `skills/ship/scripts/check_tokens.py` — CLI: `--init PATH` (scaffold iff absent) and `PATH` (verify gate). Thin wrapper over `_ledger`.
- **Modify** `skills/ship/scripts/token_report.py` — refactor `main()` into `parse_transcript` + `orchestrator_body` + `run_print` (unchanged console behavior) + `run_write` (new `--write`/`--transcript`).
- **Create** `tests/test_tokens_guardrail.py` — subprocess + unit tests for criteria 1–6. (Introduces the repo's first `tests/` dir.)
- **Modify** prose (wire to the scripts): `skills/ship/SKILL.md` (§5.3, §8), `skills/research/SKILL.md` (§0 + the delegate bullet), `skills/build/SKILL.md` (step 4), `skills/research/references/wi-directory.md` (template + script calls), and the rpa flow: `skills/rpa/SKILL.md`, `skills/rpa/references/build-uipath.md`, `skills/rpa/references/verification-gate.md`, `skills/rpa/references/rpa-constitution-template.md`.
- **Modify** `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json` (version `0.10.3 → 0.10.4`) and `README.md` (one release-notes line).

---

## Task 1: `_ledger.py` — the file-format helpers + verify gate

**Files:**
- Create: `skills/ship/scripts/_ledger.py`
- Test: `tests/test_tokens_guardrail.py`

- [ ] **Step 1: Write the failing unit tests for `_ledger`**

Create `tests/test_tokens_guardrail.py` with the import-level unit tests first (subprocess CLI tests are added in Tasks 2–3):

```python
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "ship" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import _ledger  # noqa: E402


def _scaffold_text():
    return _ledger.make_template("my-goal", timestamp="2026-06-15")


def _with_row_and_sum(text, tokens=100):
    text = text.replace(
        "| orchestrator |",
        "| build W1 | task-runner: t1 | {} | exact |\n| orchestrator |".format(tokens),
    )
    return text.replace("<sum>", str(tokens))


def _resolve_orchestrator(text, body="Orchestrator: unavailable for this run"):
    return re.sub(r"## Orchestrator[\s\S]*$", "## Orchestrator\n\n" + body + "\n", text)


class LedgerHelperTests(unittest.TestCase):
    def test_template_has_required_markers(self):
        t = _scaffold_text()
        self.assertIn("type: Token Ledger", t)
        self.assertIn("goal: my-goal", t)
        self.assertIn("timestamp: 2026-06-15", t)
        self.assertIn("**Subagents (exact): <sum>.**", t)
        self.assertIn("## Orchestrator", t)
        self.assertIn("PENDING", t)

    def test_data_rows_ignore_header_separator_and_orchestrator(self):
        t = _scaffold_text()
        self.assertFalse(_ledger.has_data_row(t))          # only header/sep/orchestrator rows
        t2 = _with_row_and_sum(t, 250)
        self.assertTrue(_ledger.has_data_row(t2))
        self.assertEqual(_ledger.sum_data_rows(t2), 250)

    def test_sum_excludes_orchestrator_and_handles_commas(self):
        t = _scaffold_text().replace(
            "| orchestrator |",
            "| build | task-runner: a | 1,200 | exact |\n| build | task-runner: b | 800 | exact |\n| orchestrator |",
        )
        self.assertEqual(_ledger.sum_data_rows(t), 2000)

    def test_subagents_sum_filled_and_set(self):
        t = _scaffold_text()
        self.assertFalse(_ledger.subagents_sum_filled(t))   # still <sum>
        t = _ledger.set_subagents_sum(t, 2000)
        self.assertIn("**Subagents (exact): 2,000.**", t)
        self.assertTrue(_ledger.subagents_sum_filled(t))

    def test_orchestrator_resolved_pending_vs_figure_vs_unavailable(self):
        t = _scaffold_text()
        self.assertFalse(_ledger.orchestrator_resolved(t))  # PENDING
        self.assertTrue(_ledger.orchestrator_resolved(_resolve_orchestrator(t)))
        figured = _ledger.replace_orchestrator_section(t, "- output tokens (generated): 22")
        self.assertTrue(_ledger.orchestrator_resolved(figured))
        self.assertNotIn("PENDING", figured)

    def test_parse_frontmatter(self):
        fm = _ledger.parse_frontmatter(_scaffold_text())
        self.assertIsNotNone(fm)
        self.assertEqual(fm["type"], "Token Ledger")
        self.assertIsNone(_ledger.parse_frontmatter("no frontmatter here"))

    def test_verify_reasons(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "tokens.md"
            self.assertEqual(_ledger.verify(p), "tokens.md missing")
            p.write_text(_scaffold_text(), encoding="utf-8")
            self.assertEqual(_ledger.verify(p), "no subagent row with an integer token count")
            p.write_text(_with_row_and_sum(_scaffold_text()), encoding="utf-8")
            self.assertEqual(_ledger.verify(p), "Orchestrator section still PENDING / unresolved")
            p.write_text(_resolve_orchestrator(_with_row_and_sum(_scaffold_text())), encoding="utf-8")
            self.assertIsNone(_ledger.verify(p))            # full pass
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m unittest tests.test_tokens_guardrail.LedgerHelperTests -v`
Expected: FAIL — `ModuleNotFoundError: No module named '_ledger'` (file not created yet).

- [ ] **Step 3: Create `skills/ship/scripts/_ledger.py`**

```python
#!/usr/bin/env python3
"""
_ledger.py — shared helpers for the tokens.md token ledger.

NOT an entrypoint. Imported by the two scripts the skills invoke:
  - check_tokens.py  (--init scaffold, default = verify gate)
  - token_report.py  (--write finalize: Orchestrator section + Subagents sum)

tokens.md is a per-goal RUNTIME artifact in a user's .wi/, never in this plugin repo.
This module owns the file format; the scripts are thin CLIs over it. Stdlib only.
"""
import re
from datetime import date
from pathlib import Path

# Exact sentinel ship writes when the orchestrator transcript can't be parsed. The verify
# gate treats this as RESOLVED — an honest "can't measure" passes; only the untouched
# PENDING placeholder fails. Must match the wording in ship/SKILL.md and wi-directory.md.
UNAVAILABLE = "Orchestrator: unavailable for this run"

_SUM_RE = re.compile(r"\*\*Subagents \(exact\):\s*([^.*]*?)\.\*\*")
_ORCH_RE = re.compile(r"^## Orchestrator\b.*$", re.MULTILINE)

TEMPLATE = """\
---
type: Token Ledger
title: "__TITLE__"
description: Exact per-subagent token usage + the orchestrator total (finalized by ship pre-PR).
goal: __SLUG__
timestamp: __TIMESTAMP__
---

# __TITLE__

Append a row the moment each subagent's completion notification arrives — the figure
exists only there and is NOT retrievable later. ship finalizes the Orchestrator section.

| Phase | Source | Tokens | Basis |
|-------|--------|--------|-------|
| orchestrator | main thread, all phases | (see Orchestrator section) | parsed by token_report.py; unavailable if the parse fails — never substitute or estimate |

**Subagents (exact): <sum>.**

## Orchestrator

_PENDING — ship replaces this section during the dossier tidy (BEFORE the dossier commit and the PR) by running `python3 ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/token_report.py --write <this file>`, which parses the session transcript. That parsed figure is the only reliable orchestrator measure; if the parse fails it writes `Orchestrator: unavailable for this run` — never a substitute, estimate, or invented figure. A tokens.md still reading PENDING after ship is a defect._
"""


def make_template(slug, timestamp=None):
    ts = timestamp or date.today().isoformat()
    return (TEMPLATE.replace("__TITLE__", "Token ledger: " + slug)
                    .replace("__SLUG__", slug)
                    .replace("__TIMESTAMP__", ts))


def _data_row_tokens(text):
    """Integer token counts from ledger rows whose Tokens (3rd) cell is an integer.
    Header, separator, the orchestrator row, and <n> placeholders are naturally excluded."""
    vals = []
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.split("|")[1:-1]]
        if len(cells) < 3:
            continue
        tok = cells[2].replace(",", "").replace("_", "")
        if tok.isdigit():
            vals.append(int(tok))
    return vals


def has_data_row(text):
    return len(_data_row_tokens(text)) > 0


def sum_data_rows(text):
    return sum(_data_row_tokens(text))


def subagents_sum_filled(text):
    m = _SUM_RE.search(text)
    if not m:
        return False
    return m.group(1).strip().replace(",", "").replace("_", "").isdigit()


def set_subagents_sum(text, total):
    repl = "**Subagents (exact): {:,}.**".format(total)
    if _SUM_RE.search(text):
        return _SUM_RE.sub(lambda _m: repl, text, count=1)
    return text


def orchestrator_resolved(text):
    m = _ORCH_RE.search(text)
    if not m:
        return False
    body = text[m.end():]
    return "PENDING" not in body and body.strip() != ""


def replace_orchestrator_section(text, body):
    section = "## Orchestrator\n\n" + body.rstrip() + "\n"
    m = _ORCH_RE.search(text)
    if not m:
        return text.rstrip() + "\n\n" + section
    return text[:m.start()] + section


def parse_frontmatter(text):
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    fm = {}
    for line in text[3:end].splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm


def verify(path):
    """Return None if the ledger passes the gate, else a one-line failure reason."""
    p = Path(path)
    if not p.is_file():
        return "tokens.md missing"
    text = p.read_text(encoding="utf-8", errors="replace")
    fm = parse_frontmatter(text)
    if fm is None:
        return "frontmatter missing or unparseable"
    if fm.get("type") != "Token Ledger":
        return "frontmatter 'type' is not 'Token Ledger'"
    if not has_data_row(text):
        return "no subagent row with an integer token count"
    if not subagents_sum_filled(text):
        return "Subagents (exact) sum not filled (still '<sum>')"
    if not orchestrator_resolved(text):
        return "Orchestrator section still PENDING / unresolved"
    return None
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m unittest tests.test_tokens_guardrail.LedgerHelperTests -v`
Expected: PASS (7 tests).

- [ ] **Step 5: Commit**

```bash
git add skills/ship/scripts/_ledger.py tests/test_tokens_guardrail.py
git commit -m "feat(ship): tokens.md ledger format helpers + verify gate (_ledger.py)"
```

---

## Task 2: `check_tokens.py` — scaffold (`--init`) + verify gate CLI

**Files:**
- Create: `skills/ship/scripts/check_tokens.py`
- Test: `tests/test_tokens_guardrail.py` (add `CheckTokensCliTests`)

- [ ] **Step 1: Write the failing CLI tests**

Append to `tests/test_tokens_guardrail.py`:

```python
CHECK = SCRIPTS / "check_tokens.py"
REPORT = SCRIPTS / "token_report.py"


def run(*args):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True)


def init_ledger(d, slug="my-goal"):
    p = Path(d) / slug / "tokens.md"
    run(CHECK, "--init", p)
    return p


class CheckTokensCliTests(unittest.TestCase):
    def test_init_creates_when_absent(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "my-goal" / "tokens.md"
            r = run(CHECK, "--init", p)
            self.assertEqual(r.returncode, 0, r.stderr)
            text = p.read_text(encoding="utf-8")
            self.assertIn("type: Token Ledger", text)
            self.assertIn("goal: my-goal", text)
            self.assertIn("## Orchestrator", text)
            self.assertIn("PENDING", text)
            self.assertIn("<sum>", text)

    def test_init_idempotent_byte_for_byte(self):
        with tempfile.TemporaryDirectory() as d:
            p = init_ledger(d)
            first = p.read_bytes()
            r = run(CHECK, "--init", p)
            self.assertEqual(r.returncode, 0)
            self.assertEqual(p.read_bytes(), first)

    def test_verify_missing_fails(self):
        with tempfile.TemporaryDirectory() as d:
            r = run(CHECK, Path(d) / "tokens.md")
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("missing", (r.stdout + r.stderr).lower())

    def test_verify_fresh_scaffold_fails_no_rows(self):
        with tempfile.TemporaryDirectory() as d:
            p = init_ledger(d)
            r = run(CHECK, p)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("row", (r.stdout + r.stderr).lower())

    def test_verify_pending_fails_even_with_row_and_sum(self):
        with tempfile.TemporaryDirectory() as d:
            p = init_ledger(d)
            p.write_text(_with_row_and_sum(p.read_text(encoding="utf-8")), encoding="utf-8")
            r = run(CHECK, p)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("orchestrator", (r.stdout + r.stderr).lower())

    def test_verify_full_passes_with_unavailable(self):
        with tempfile.TemporaryDirectory() as d:
            p = init_ledger(d)
            p.write_text(_resolve_orchestrator(_with_row_and_sum(p.read_text(encoding="utf-8"))), encoding="utf-8")
            r = run(CHECK, p)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m unittest tests.test_tokens_guardrail.CheckTokensCliTests -v`
Expected: FAIL — `check_tokens.py` does not exist, so subprocesses return non-zero and `test_init_creates_when_absent` / `test_verify_full_passes_with_unavailable` fail their assertions.

- [ ] **Step 3: Create `skills/ship/scripts/check_tokens.py`**

```python
#!/usr/bin/env python3
"""
check_tokens.py — scaffold and verify a goal's tokens.md ledger.

  check_tokens.py --init PATH   # write the template iff absent (idempotent no-op otherwise)
  check_tokens.py PATH          # verify (the close-out gate)

Verify exits 0 iff the ledger is present and structurally finalized (frontmatter
type: Token Ledger, >=1 integer-token row, Subagents sum filled, Orchestrator resolved —
a real figure OR the honest "unavailable" sentinel, NOT the PENDING placeholder).
Otherwise exit 1 and print the first failing check. A non-zero exit is the hard guardrail:
ship must not mark Phase=done, so the keep-alive loop keeps working the goal. Stdlib only.
"""
import argparse
import sys
from pathlib import Path

import _ledger


def run_init(path):
    p = Path(path)
    if p.exists():
        return 0  # idempotent: never touch an existing ledger
    p.parent.mkdir(parents=True, exist_ok=True)
    slug = p.parent.name or "goal"
    p.write_text(_ledger.make_template(slug), encoding="utf-8")
    print("check_tokens: scaffolded {}".format(path))
    return 0


def run_verify(path):
    reason = _ledger.verify(path)
    if reason is None:
        print("check_tokens: OK — {}".format(path))
        return 0
    print("check_tokens: FAIL — {} ({})".format(reason, path), file=sys.stderr)
    return 1


def main():
    ap = argparse.ArgumentParser(description="Scaffold (--init) or verify a goal's tokens.md ledger.")
    ap.add_argument("path", help="path to the goal's tokens.md")
    ap.add_argument("--init", action="store_true", help="write the template iff absent, then exit 0")
    a = ap.parse_args()
    return run_init(a.path) if a.init else run_verify(a.path)


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m unittest tests.test_tokens_guardrail.CheckTokensCliTests -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add skills/ship/scripts/check_tokens.py tests/test_tokens_guardrail.py
git commit -m "feat(ship): check_tokens.py — idempotent scaffold + structural verify gate"
```

---

## Task 3: `token_report.py --write` — finalize Orchestrator section + Subagents sum

**Files:**
- Modify: `skills/ship/scripts/token_report.py` (refactor `main`; add `run_write`, `orchestrator_body`, `parse_transcript`)
- Test: `tests/test_tokens_guardrail.py` (add `TokenReportWriteTests`)

- [ ] **Step 1: Write the failing write-mode tests**

Append to `tests/test_tokens_guardrail.py`:

```python
def fixture_transcript(d):
    f = Path(d) / "t.jsonl"
    f.write_text(
        '{"message":{"usage":{"input_tokens":10,"output_tokens":20,'
        '"cache_creation_input_tokens":0,"cache_read_input_tokens":5}}}\n'
        '{"usage":{"input_tokens":1,"output_tokens":2,'
        '"cache_creation_input_tokens":0,"cache_read_input_tokens":0}}\n',
        encoding="utf-8",
    )
    return f


class TokenReportWriteTests(unittest.TestCase):
    def _ledger_with_rows(self, d):
        p = init_ledger(d)
        text = p.read_text(encoding="utf-8").replace(
            "| orchestrator |",
            "| build W1 | task-runner: t1 | 100 | exact |\n"
            "| build W1 | task-runner: t2 | 50 | exact |\n| orchestrator |",
        )
        p.write_text(text, encoding="utf-8")
        return p

    def test_write_fills_orchestrator_and_sum_and_passes_gate(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._ledger_with_rows(d)
            r = run(REPORT, "--write", p, "--transcript", fixture_transcript(d))
            self.assertEqual(r.returncode, 0, r.stderr)
            out = p.read_text(encoding="utf-8")
            self.assertNotIn("PENDING", out)
            self.assertIn("output tokens (generated): 22", out)   # 20 + 2
            self.assertIn("**Subagents (exact): 150.**", out)     # 100 + 50
            self.assertEqual(run(CHECK, p).returncode, 0)

    def test_write_unavailable_on_unparseable_transcript(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._ledger_with_rows(d)
            empty = Path(d) / "empty.jsonl"
            empty.write_text("", encoding="utf-8")
            r = run(REPORT, "--write", p, "--transcript", empty)
            self.assertEqual(r.returncode, 0, r.stderr)
            out = p.read_text(encoding="utf-8")
            self.assertIn("Orchestrator: unavailable for this run", out)
            self.assertNotIn("PENDING", out)
            self.assertEqual(run(CHECK, p).returncode, 0)         # honest unavailable passes

    def test_write_missing_file_errors_and_creates_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "nope" / "tokens.md"
            r = run(REPORT, "--write", p, "--transcript", fixture_transcript(d))
            self.assertNotEqual(r.returncode, 0)
            self.assertFalse(p.exists())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m unittest tests.test_tokens_guardrail.TokenReportWriteTests -v`
Expected: FAIL — the current `token_report.py` reads `sys.argv[1]` (no argparse), so it treats `--write` as a transcript path, finds no such file, prints "no transcript found" and exits 1 **without modifying the ledger**. `test_write_fills_...` and `test_write_unavailable_...` fail (file unchanged, still PENDING, wrong exit); `test_write_missing_file_errors...` happens to pass already. The suite is red overall.

- [ ] **Step 3: Replace `skills/ship/scripts/token_report.py` with the refactored version**

Keep the module docstring's intent but rewrite the body. Full new file:

```python
#!/usr/bin/env python3
"""
token_report.py — sum the main-thread (orchestrator) token usage from a Claude Code
session transcript (JSONL), and optionally write it into a goal's tokens.md.

  token_report.py [TRANSCRIPT.jsonl]      # print the orchestrator report (auto-detects transcript)
  token_report.py --write TOKENS_MD [--transcript T.jsonl]
                                          # finalize: replace the tokens.md Orchestrator
                                          # section + recompute the Subagents (exact) sum

The model can't read its own running total mid-turn, but the harness records a `usage`
object on every assistant message in the session transcript. --write turns the parsed
result into the ledger directly, so there is no manual stdout-copy step to skip. On a
parse failure it writes `Orchestrator: unavailable for this run` — never a substitute,
estimate, or fabricated figure. It does NOT create the file (run check_tokens.py --init
first); --write exits non-zero only if the file is absent or unwritable.

Stdlib only.
"""
import argparse
import json
import sys
from pathlib import Path

import _ledger

FIELDS = ("input_tokens", "output_tokens",
          "cache_creation_input_tokens", "cache_read_input_tokens")


def find_transcript():
    base = Path.home() / ".claude" / "projects"
    if not base.is_dir():
        return None
    files = sorted(base.glob("**/*.jsonl"),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def extract_usage(obj):
    for u in (obj.get("usage"), (obj.get("message") or {}).get("usage")):
        if isinstance(u, dict):
            return u
    return None


def parse_transcript(path):
    """Return (totals, turns) or None if the transcript has no usage records."""
    tot = {k: 0 for k in FIELDS}
    turns = 0
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            u = extract_usage(obj)
            if not u:
                continue
            turns += 1
            for k in FIELDS:
                v = u.get(k)
                if isinstance(v, int):
                    tot[k] += v
    if turns == 0:
        return None
    return tot, turns


def orchestrator_body(path, tot, turns):
    return "\n".join([
        "- transcript: `{}`  ({} assistant turns)".format(path, turns),
        "- output tokens (generated): {:,}".format(tot["output_tokens"]),
        "- input tokens (fresh): {:,}".format(tot["input_tokens"]),
        "- cache-write tokens: {:,}".format(tot["cache_creation_input_tokens"]),
        "- cache-read tokens: {:,}".format(tot["cache_read_input_tokens"]),
        "- NOTE: cache-read is the same context re-read each turn (the bulk of a long run); "
        "counts run up to ship time — the last few messages aren't in the transcript yet.",
    ])


def run_print(path):
    if not path or not Path(path).is_file():
        print("token_report: no transcript found — orchestrator total unavailable", file=sys.stderr)
        return 1
    parsed = parse_transcript(path)
    if parsed is None:
        print("token_report: no usage records in transcript — orchestrator total unavailable", file=sys.stderr)
        return 1
    tot, turns = parsed
    print("## Orchestrator (main thread) — token consumption from session transcript")
    print(orchestrator_body(path, tot, turns))
    return 0


def run_write(token_path, transcript):
    p = Path(token_path)
    if not p.is_file():
        print("token_report: {} does not exist — run check_tokens.py --init first".format(token_path),
              file=sys.stderr)
        return 1
    text = p.read_text(encoding="utf-8", errors="replace")
    tpath = transcript or find_transcript()
    parsed = parse_transcript(tpath) if tpath and Path(tpath).is_file() else None
    if parsed is None:
        body = _ledger.UNAVAILABLE
    else:
        body = orchestrator_body(tpath, *parsed)
    text = _ledger.replace_orchestrator_section(text, body)
    text = _ledger.set_subagents_sum(text, _ledger.sum_data_rows(text))
    p.write_text(text, encoding="utf-8")
    print(body)
    return 0


def main():
    ap = argparse.ArgumentParser(
        description="Sum orchestrator tokens from a session transcript; optionally write them into tokens.md.")
    ap.add_argument("transcript", nargs="?", help="transcript path for print mode (default: auto-detect)")
    ap.add_argument("--write", metavar="TOKENS_MD",
                    help="write the Orchestrator section + Subagents sum into this tokens.md, then exit")
    ap.add_argument("--transcript", dest="transcript_opt", help="explicit transcript path for --write mode")
    a = ap.parse_args()
    if a.write:
        return run_write(a.write, a.transcript_opt)
    return run_print(a.transcript or find_transcript())


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the full test suite to verify everything passes**

Run: `python -m unittest discover -s tests -v`
Expected: PASS (all 16 tests across the three classes).

- [ ] **Step 5: Commit**

```bash
git add skills/ship/scripts/token_report.py tests/test_tokens_guardrail.py
git commit -m "feat(ship): token_report.py --write finalizes tokens.md in place"
```

---

## Task 4: Wire `ship/SKILL.md` — finalize via `--write`, gate via `check_tokens.py`

**Files:**
- Modify: `skills/ship/SKILL.md` (§5 step 3; §8 close-out checklist)

- [ ] **Step 1: Replace the §5.3 finalize prose**

Find this block (the `3. *Finalize ... tokens.md ...*` item) and replace it:

Old:
```
  3. *Finalize `tokens.md` — NOW, not at close-out.* The file must be complete **inside the dossier
     commit**, or it never rides the PR. Run the bundled transcript parser — the model can't read its own
     running total mid-turn, but the harness records per-turn `usage` in the session transcript:
     `python3 ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/token_report.py` (auto-detects the active session
     transcript under `~/.claude/projects/`; pass the path if you know it). **Write its output into
     `tokens.md`**, replacing the `## Orchestrator` placeholder — the parsed transcript is the only
     reliable orchestrator measure. Then write the **Subagents (exact)** sum line from the ledger rows.
     **If the script fails** (no transcript or no `usage`), write `Orchestrator: unavailable for this run`
     in that section — never substitute, estimate, or fabricate. Printing the report to the console does
     **not** count as done: the file is the deliverable; the console report at close-out is read *from* it.
```

New:
```
  3. *Finalize `tokens.md` — NOW, not at close-out.* The file must be complete **inside the dossier
     commit**, or it never rides the PR. The ledger was scaffolded at research/build start and its
     subagent rows appended live; finalize the orchestrator total with one command:
     `python3 ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/token_report.py --write .wi/goals/<slug>/tokens.md`
     (auto-detects the active session transcript under `~/.claude/projects/`; add
     `--transcript <path>` if you know it). It replaces the `## Orchestrator` section in place and
     recomputes the **Subagents (exact)** sum from the ledger rows — no manual stdout-copy. On a parse
     failure it writes `Orchestrator: unavailable for this run` (never a substitute, estimate, or
     fabricated figure). The **file** is the deliverable, not the console output.
```

- [ ] **Step 2: Replace the §8 close-out `tokens.md` checkbox with the gate**

Old:
```
- [ ] `tokens.md` has the subagent ledger rows **and** a finalized `## Orchestrator` section (parsed
      figure or explicit `unavailable`) — verify by reading the **file**, not the console log
```

New:
```
- [ ] `tokens.md` passes the structural gate — run
      `python3 ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/check_tokens.py .wi/goals/<slug>/tokens.md`; a
      **non-zero exit blocks `Phase = done`** (file missing / no subagent row / unfilled sum / `## Orchestrator`
      still PENDING). An honest `Orchestrator: unavailable for this run` passes. This *replaces* reading the
      file by eye — the exit code is the close-out condition the keep-alive loop waits on.
```

- [ ] **Step 3: Verify the prose validates**

Run: `python scripts/validate.py`
Expected: `[OK] all checks passed`.

- [ ] **Step 4: Commit**

```bash
git add skills/ship/SKILL.md
git commit -m "feat(ship): finalize tokens.md via --write; gate close-out on check_tokens.py"
```

---

## Task 5: Wire the dev flow — `research`, `build`, and the canonical template doc

**Files:**
- Modify: `skills/research/SKILL.md` (§0 scaffold + the delegate bullet)
- Modify: `skills/build/SKILL.md` (step 4 row-append)
- Modify: `skills/research/references/wi-directory.md` (template note → the three script calls)

- [ ] **Step 1: Add the scaffold call to research §0**

In `skills/research/SKILL.md`, find the `### 0 - Engage & resume` paragraph and append a sentence after `so it's auditable on disk.`:

Old:
```
<version> from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` (don't guess; if that file isn't reachable — e.g. a per-skill Copilot install — omit the version rather than inventing one) — so it's auditable on disk. Then re-enter the phase it names (research | plan | design-gate).
```

New:
```
<version> from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` (don't guess; if that file isn't reachable — e.g. a per-skill Copilot install — omit the version rather than inventing one) — so it's auditable on disk. Then scaffold the token ledger (idempotent — no-op if it exists): `python3 ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/check_tokens.py --init .wi/goals/<slug>/tokens.md`. Then re-enter the phase it names (research | plan | design-gate).
```

- [ ] **Step 2: Point the delegate bullet at the ledger**

Old:
```
- **Delegate, summarize, discard.** Researchers run in parallel subagents and return short reports; log
  each one's token count to `tokens.md` the moment its completion notification arrives.
```

New:
```
- **Delegate, summarize, discard.** Researchers run in parallel subagents and return short reports; append
  each one's token count as a row to `tokens.md` the moment its completion notification arrives (the figure
  exists only there — NOT retrievable later). ship finalizes the orchestrator total and a `check_tokens.py`
  gate blocks the PR if the ledger was skipped.
```

- [ ] **Step 3: Update the build step-4 row-append**

In `skills/build/SKILL.md`, find the committer sentence and extend it.

Old:
```
   are the only committer, so commits stay serialized and clean. Append the runner's token count to the
   goal's `tokens.md` (it's in the task-completion notification and is NOT retrievable later), then
   recompute the ready set and dispatch the next wave without waiting for stragglers it doesn't depend on.
```

New:
```
   are the only committer, so commits stay serialized and clean. Append the runner's token count as a row to
   the goal's `tokens.md` (it's in the task-completion notification and is NOT retrievable later; if the file
   is somehow absent, `python3 ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/check_tokens.py --init .wi/goals/<slug>/tokens.md`
   first), then recompute the ready set and dispatch the next wave without waiting for stragglers it doesn't depend on.
```

- [ ] **Step 4: Update the `wi-directory.md` template note**

In `skills/research/references/wi-directory.md`, in the `## ``tokens.md`` template` section, replace the closing PENDING note paragraph so it names the scripts.

Old:
```
_PENDING — ship replaces this section during the dossier tidy (BEFORE the dossier commit and the PR) with
the output of `python3 ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/token_report.py`, which parses the
session transcript (the harness records per-turn `usage`: output, fresh input, cache write/read). That
parsed figure is the **only** reliable orchestrator measure; if the parse fails, ship writes
`Orchestrator: unavailable for this run` — never a substitute, estimate, or invented figure. A tokens.md
still reading PENDING after ship is a defect._
```

New:
```
_PENDING — the ledger is scaffolded by `check_tokens.py --init` (research §0), rows appended live, and
ship replaces this section during the dossier tidy (BEFORE the dossier commit and the PR) by running
`python3 ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/token_report.py --write <this file>`, which parses the
session transcript (per-turn `usage`: output, fresh input, cache write/read) and recomputes the Subagents
sum. That parsed figure is the **only** reliable orchestrator measure; if the parse fails it writes
`Orchestrator: unavailable for this run` — never a substitute, estimate, or invented figure. At close-out
`check_tokens.py <this file>` gates `Phase = done`: a tokens.md still reading PENDING (or missing rows) is
a defect that blocks the PR._
```

- [ ] **Step 5: Validate and commit**

Run: `python scripts/validate.py`
Expected: `[OK] all checks passed`.

```bash
git add skills/research/SKILL.md skills/build/SKILL.md skills/research/references/wi-directory.md
git commit -m "feat(research,build): scaffold tokens.md at start; point appends at the gate"
```

---

## Task 6: Wire the rpa flow to the same scaffold + gate

**Files:**
- Modify: `skills/rpa/SKILL.md` (build step append; verify & ship gate line)
- Modify: `skills/rpa/references/build-uipath.md` (step 4)
- Modify: `skills/rpa/references/verification-gate.md` (tokens.md line)
- Modify: `skills/rpa/references/rpa-constitution-template.md` (definition-of-done line)

- [ ] **Step 1: `rpa/SKILL.md` — scaffold on first append + gate at the verification gate**

Old (build step append):
```
   coded-allowed → `.cs` workflows ok; scaffold each unit as REFramework per the SDD, never Blank),
   append each unit's tokens to `tokens.md`, and
```

New:
```
   coded-allowed → `.cs` workflows ok; scaffold each unit as REFramework per the SDD, never Blank),
   append each unit's tokens to `tokens.md` (scaffold it first if absent:
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/check_tokens.py --init .wi/goals/<slug>/tokens.md`), and
```

Old (verify & ship gate line):
```
7. **Verify & ship.** Gate = `${CLAUDE_PLUGIN_ROOT}/skills/rpa/references/verification-gate.md` (**paradigm =
   XAML REFramework** + Workflow Analyzer + `uip` validate + `tokens.md` present + the **goal-level checker · result mode** over `sdd.md` §13). Then reuse the **ship**
```

New:
```
7. **Verify & ship.** Gate = `${CLAUDE_PLUGIN_ROOT}/skills/rpa/references/verification-gate.md` (**paradigm =
   XAML REFramework** + Workflow Analyzer + `uip` validate + `tokens.md` passes `check_tokens.py` + the **goal-level checker · result mode** over `sdd.md` §13). Then reuse the **ship**
```

- [ ] **Step 2: `build-uipath.md` step 4 — scaffold via the script**

Old:
```
4. **Commit small + record tokens.** One workflow\process per focused commit (`feat(<process>): ...`); tick
   `progress.md`. **Append each delegated unit's token count to `tokens.md`** the moment that subagent
   reports completion (the only point the count exists) — `tokens.md` is **mandatory**, not optional;
   initialize it on the first delegation if absent, and ship finalizes it.
```

New:
```
4. **Commit small + record tokens.** One workflow\process per focused commit (`feat(<process>): ...`); tick
   `progress.md`. **Append each delegated unit's token count to `tokens.md`** the moment that subagent
   reports completion (the only point the count exists) — `tokens.md` is **mandatory**, not optional;
   initialize it on the first delegation if absent
   (`python3 ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/check_tokens.py --init .wi/goals/<slug>/tokens.md`),
   and ship finalizes it (`token_report.py --write`) under a `check_tokens.py` close-out gate.
```

- [ ] **Step 3: `verification-gate.md` — gate via the script**

Old:
```
- the **token report `tokens.md` exists** and lists each delegated build unit's tokens.
```

New:
```
- the **token ledger `tokens.md` passes `check_tokens.py`** — present, with a row per delegated build unit,
  the Subagents sum filled, and a resolved `## Orchestrator` section (real figure or honest `unavailable`).
```

- [ ] **Step 4: `rpa-constitution-template.md` — definition-of-done line**

Old:
```
- `tokens.md` (token report) written.
```

New:
```
- `tokens.md` (token ledger) passes `check_tokens.py` — rows + filled sum + resolved Orchestrator.
```

- [ ] **Step 5: Validate and commit**

Run: `python scripts/validate.py`
Expected: `[OK] all checks passed`.

```bash
git add skills/rpa/SKILL.md skills/rpa/references/build-uipath.md skills/rpa/references/verification-gate.md skills/rpa/references/rpa-constitution-template.md
git commit -m "feat(rpa): scaffold + gate tokens.md via check_tokens.py"
```

---

## Task 7: Version bump, README, and full verification

**Files:**
- Modify: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json` (`0.10.3 → 0.10.4`)
- Modify: `README.md` (one release-notes line)

- [ ] **Step 1: Bump the version in all three manifests**

In each of `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json`, change `"version": "0.10.3"` to `"version": "0.10.4"`.

- [ ] **Step 2: Add a README "shipped" bullet to the Roadmap**

`README.md` has no bullet changelog; shipped features are version-tagged bullets under `## Roadmap`
(e.g. "**Agent verification layer** (v0.9.2-v0.10.0) shipped — …"). Add this as the **first** bullet of
the Roadmap list (most-recent-on-top), matching that style:
```
- **tokens.md guardrails** (v0.10.4) shipped — the per-goal token ledger can no longer be silently
  skipped: a deterministic scaffold (`check_tokens.py --init`), `token_report.py --write` finalizes the
  orchestrator total + Subagents sum in place, and a `check_tokens.py` close-out gate blocks the PR on a
  genuine skip (an honest `unavailable` still ships). Dev + rpa flows; design and plan in `docs/specs/`
  and `docs/plans/`.
```

- [ ] **Step 3: Full verification — tests, validate, file-tail check**

Run the whole suite and the repo validator:
```bash
python -m unittest discover -s tests -v
python scripts/validate.py
```
Expected: all tests PASS; `[OK] all checks passed`.

Then check no markdown file was truncated mid-write (this repo's known hazard) — confirm each modified `.md` ends with a complete line:
```bash
for f in skills/ship/SKILL.md skills/research/SKILL.md skills/build/SKILL.md skills/research/references/wi-directory.md skills/rpa/SKILL.md skills/rpa/references/build-uipath.md skills/rpa/references/verification-gate.md skills/rpa/references/rpa-constitution-template.md README.md; do echo "== $f =="; tail -c 120 "$f"; echo; done
```
Expected: every tail ends on a complete sentence/line.

- [ ] **Step 4: Commit**

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json .codex-plugin/plugin.json README.md
git commit -m "chore: release 0.10.4 — tokens.md guardrails"
```

---

## Done-when

- `python -m unittest discover -s tests` is green (16 tests across criteria 1–6).
- `python scripts/validate.py` passes.
- A fresh `check_tokens.py --init` ledger fails the gate until a real row is appended **and** the Orchestrator section is resolved; `token_report.py --write` resolves it (figure or honest `unavailable`) and the gate then passes.
- ship §5.3 calls `--write`; ship §8 and the rpa gate call `check_tokens.py` with a non-zero exit blocking `Phase = done`.
- Version is `0.10.4` across the three manifests with a README line.

