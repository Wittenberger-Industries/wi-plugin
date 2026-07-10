"""Timing + per-subagent split/cost tests for now.py and token_report.py (issue #35 + extensions)."""
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "ship" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import _ledger  # noqa: E402
import token_report  # noqa: E402

NOW = SCRIPTS / "now.py"
REPORT = SCRIPTS / "token_report.py"
CHECK = SCRIPTS / "check_tokens.py"


def run(*args):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True)


PROGRESS_FIXTURE = """---
type: Feature Progress
title: fixture
feature: 0001-fixture
status: done
timestamp: 2026-07-05
---

# Feature: fixture

- **Phase:** done

## Log
- 2026-07-05 **Created** feature, phase = brainstorm
- 2026-07-05T14:19:47+02:00 **Update** phase = research (handoff accepted)
- 2026-07-05T14:41:03+02:00 **Update** phase = plan
- 2026-07-05T14:52:38+02:00 **Update** design gate opened
- 2026-07-05T15:08:02+02:00 **Update** design gate approved, phase = build
- 2026-07-05T15:58:14+02:00 **Update** PR opened, phase = done
"""


class ProgressSpanTests(unittest.TestCase):
    def test_spans_from_full_timestamps(self):
        s1, s2 = token_report.parse_progress_spans(PROGRESS_FIXTURE)
        self.assertEqual(s1, 1971)   # 14:19:47 -> 14:52:38
        self.assertEqual(s2, 3012)   # 15:08:02 -> 15:58:14

    def test_auto_approved_variant_counts_as_gate_approval(self):
        text = PROGRESS_FIXTURE.replace(
            "**Update** design gate approved, phase = build",
            "**Update** design gate auto-approved (--auto), phase = build")
        s1, s2 = token_report.parse_progress_spans(text)
        self.assertEqual((s1, s2), (1971, 3012))

    def test_missing_boundary_yields_none_not_a_guess(self):
        no_gate = "\n".join(l for l in PROGRESS_FIXTURE.splitlines() if "design gate opened" not in l)
        s1, s2 = token_report.parse_progress_spans(no_gate)
        self.assertIsNone(s1)
        self.assertEqual(s2, 3012)

    def test_date_only_stamps_are_ignored(self):
        legacy = PROGRESS_FIXTURE.replace("2026-07-05T14:19:47+02:00", "2026-07-05")
        s1, _ = token_report.parse_progress_spans(legacy)
        self.assertIsNone(s1)

    def test_negative_span_is_none(self):
        skewed = PROGRESS_FIXTURE.replace("2026-07-05T14:52:38+02:00", "2026-07-05T13:00:00+02:00")
        s1, _ = token_report.parse_progress_spans(skewed)
        self.assertIsNone(s1)


class CostTests(unittest.TestCase):
    def test_estimate_cost_known_model(self):
        tot = {"input_tokens": 1_000_000, "output_tokens": 100_000,
               "cache_creation_input_tokens": 400_000, "cache_read_input_tokens": 2_000_000}
        # opus 4.8: 5 + 2.5 + 0.4M*1.25*5/M + 2M*0.1*5/M = 5 + 2.5 + 2.5 + 1.0
        self.assertAlmostEqual(token_report.estimate_cost("claude-opus-4-8", tot), 11.0)

    def test_estimate_cost_prefix_match_and_unknown(self):
        tot = {"input_tokens": 1_000_000, "output_tokens": 0,
               "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}
        self.assertAlmostEqual(token_report.estimate_cost("claude-haiku-4-5-20251001", tot), 1.0)
        self.assertIsNone(token_report.estimate_cost("future-model-x", tot))
        self.assertIsNone(token_report.estimate_cost(None, tot))


def _agent_line(ts, usage=None, model=None, user_text=None):
    obj = {"timestamp": ts}
    if user_text is not None:
        obj["type"] = "user"
        obj["message"] = {"content": [{"type": "text", "text": user_text}]}
    elif usage is not None:
        obj["type"] = "assistant"
        obj["message"] = {"usage": usage, "model": model}
    return json.dumps(obj)


def make_session(d):
    """Main transcript t.jsonl + sidecar t/subagents/ with two agent files."""
    t = Path(d) / "t.jsonl"
    t.write_text(
        '{"message":{"usage":{"input_tokens":10,"output_tokens":20,'
        '"cache_creation_input_tokens":0,"cache_read_input_tokens":5},"model":"claude-opus-4-8"}}\n',
        encoding="utf-8",
    )
    sub = Path(d) / "t" / "subagents"
    sub.mkdir(parents=True)
    u = {"input_tokens": 500_000, "output_tokens": 50_000,
         "cache_creation_input_tokens": 200_000, "cache_read_input_tokens": 1_000_000}
    (sub / "agent-abc1234def56789.jsonl").write_text("\n".join([
        _agent_line("2026-07-10T10:00:00Z", user_text="Task 3 | add the /healthz endpoint and its test"),
        _agent_line("2026-07-10T10:01:30Z", usage=u, model="claude-opus-4-8"),
        _agent_line("2026-07-10T10:03:12Z", usage=u, model="claude-opus-4-8"),
    ]) + "\n", encoding="utf-8")
    (sub / "agent-b777777777777777.jsonl").write_text("\n".join([
        _agent_line("2026-07-10T10:00:00+02:00", user_text="researcher: survey job queues"),
        _agent_line("2026-07-10T10:00:42+02:00",
                    usage={"input_tokens": 1000, "output_tokens": 2000,
                           "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0},
                    model="future-model-x"),
    ]) + "\n", encoding="utf-8")
    return t


class AgentFileTests(unittest.TestCase):
    def test_parse_agent_file_split_duration_label(self):
        with tempfile.TemporaryDirectory() as d:
            t = make_session(d)
            files = token_report.find_subagent_files(t)
            self.assertEqual(len(files), 2)
            a = token_report.parse_agent_file(files[0])
            self.assertEqual(a["model"], "claude-opus-4-8")
            self.assertEqual(a["tot"]["input_tokens"], 1_000_000)   # two usage turns summed
            self.assertEqual(a["tot"]["cache_read_input_tokens"], 2_000_000)
            self.assertEqual(a["duration"], 192)                    # 10:00:00 -> 10:03:12
            self.assertNotIn("|", a["label"])                       # pipe-escaped for the table
            self.assertTrue(a["label"].startswith("Task 3"))
            b = token_report.parse_agent_file(files[1])
            self.assertEqual(b["duration"], 42)
            self.assertEqual(b["model"], "future-model-x")

    def test_no_subagents_dir_is_empty_list(self):
        with tempfile.TemporaryDirectory() as d:
            t = Path(d) / "solo.jsonl"
            t.write_text("{}\n", encoding="utf-8")
            self.assertEqual(token_report.find_subagent_files(t), [])


class WriteEndToEndTests(unittest.TestCase):
    def _feature(self, d, rows=3):
        feat = Path(d) / "0001-fixture"
        p = feat / "tokens.md"
        run(CHECK, "--init", p)
        row = "| build W1 | task-runner: t{i} | 100 | 1m00s | exact |\n"
        text = p.read_text(encoding="utf-8").replace(
            "| orchestrator |",
            "".join(row.format(i=i) for i in range(rows)) + "| orchestrator |")
        p.write_text(text, encoding="utf-8")
        (feat / "progress.md").write_text(PROGRESS_FIXTURE, encoding="utf-8")
        return p

    def test_write_adds_split_costs_and_timing(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._feature(d)
            t = make_session(d)
            r = run(REPORT, "--write", p, "--transcript", t)
            self.assertEqual(r.returncode, 0, r.stderr)
            out = p.read_text(encoding="utf-8")
            # timing from progress.md phase spans: 1971 + 3012 = 4983s
            self.assertIn("**Σ compute: 3m00s across 3 dispatches.**", out)
            self.assertIn("**Autonomous wall-clock (excl. manual steps): 1h23m03s.**", out)
            # split section: exact per-agent rows with model, duration, cost
            self.assertIn("## Subagent detail (exact, from agent transcripts)", out)
            self.assertIn("| claude-opus-4-8 |", out)
            self.assertIn("3m12s", out)
            # opus agent (two 500k-usage turns summed): 1M in*$5 + 0.1M out*$25
            # + 0.4M cw*1.25*$5 + 2M cr*0.1*$5 = 5 + 2.5 + 2.5 + 1.0 = $11.00
            self.assertIn("$11.00", out)
            self.assertIn("n/a (no price)", out)                    # unknown model row
            self.assertIn("1 unpriced row(s)", out)
            self.assertIn("Split covers 2 of 3 ledger rows", out)   # resumed-run honesty
            self.assertIn("est. cost", out)                         # orchestrator's own cost line
            self.assertEqual(run(CHECK, p).returncode, 0)

    def test_write_is_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._feature(d, rows=2)
            t = make_session(d)
            run(REPORT, "--write", p, "--transcript", t)
            first = p.read_text(encoding="utf-8")
            run(REPORT, "--write", p, "--transcript", t)
            self.assertEqual(p.read_text(encoding="utf-8"), first)
            self.assertEqual(first.count("## Subagent detail"), 1)

    def test_unparseable_transcript_still_fills_totals_honestly(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._feature(d, rows=1)
            empty = Path(d) / "empty.jsonl"
            empty.write_text("", encoding="utf-8")
            r = run(REPORT, "--write", p, "--transcript", empty)
            self.assertEqual(r.returncode, 0, r.stderr)
            out = p.read_text(encoding="utf-8")
            self.assertIn("Orchestrator: unavailable for this run", out)
            self.assertIn("**Σ compute: 1m00s across 1 dispatches.**", out)
            self.assertIn("**Autonomous wall-clock (excl. manual steps): 1h23m03s.**", out)
            self.assertNotIn("## Subagent detail", out)
            self.assertEqual(run(CHECK, p).returncode, 0)


class NowHelperTests(unittest.TestCase):
    def test_now_prints_iso_with_offset(self):
        r = run(NOW)
        self.assertEqual(r.returncode, 0, r.stderr)
        stamp = r.stdout.strip()
        dt = datetime.fromisoformat(stamp)
        self.assertIsNotNone(dt.utcoffset())


if __name__ == "__main__":
    unittest.main()
