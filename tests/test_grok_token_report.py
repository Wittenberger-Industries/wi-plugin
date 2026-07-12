import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "ship" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import _ledger  # noqa: E402
import grok_token_report as gtr  # noqa: E402


def make_session(tmp: Path) -> Path:
    """Synthetic Grok session dir: updates.jsonl + subagents/*/meta.json + signals/summary."""
    session = tmp / "D%3A%5Cx%5Crepo" / "0199-test-session"
    (session / "subagents" / "a1").mkdir(parents=True)
    (session / "subagents" / "a2").mkdir(parents=True)

    (session / "subagents" / "a1" / "meta.json").write_text(json.dumps({
        "subagent_id": "a1", "description": "Task 1 schema",
        "subagent_type": "general-purpose", "effective_model_id": "grok-4.5",
    }), encoding="utf-8")
    (session / "subagents" / "a2" / "meta.json").write_text(json.dumps({
        "subagent_id": "a2", "description": "Task 2 ui",
        "subagent_type": "general-purpose", "effective_model_id": "grok-4.5",
    }), encoding="utf-8")

    events = [
        # stale first finish for a1: last-finish-wins must supersede it
        {"params": {"sessionUpdate": "subagent_finished", "subagent_id": "a1",
                    "tokens_used": 1, "duration_ms": 1000, "tool_calls": 1, "turns": 1}},
        {"params": {"sessionUpdate": "subagent_finished", "subagent_id": "a1",
                    "tokens_used": 100, "duration_ms": 65000, "tool_calls": 5, "turns": 1}},
        {"params": {"sessionUpdate": "subagent_finished", "subagent_id": "a2",
                    "tokens_used": 200, "duration_ms": 130000, "tool_calls": 9, "turns": 1}},
        {"params": {"_meta": {"totalTokens": 42000}}},
        {"params": {"_meta": {"totalTokens": 55000}}},
    ]
    (session / "updates.jsonl").write_text(
        "\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")

    (session / "signals.json").write_text(json.dumps({
        "primaryModelId": "grok-4.5", "contextTokensUsed": 51000,
        "contextWindowTokens": 200000, "contextWindowUsage": 25,
        "turnCount": 7, "userMessageCount": 3, "assistantMessageCount": 4,
        "toolCallCount": 30, "sessionDurationSeconds": 900,
    }), encoding="utf-8")
    (session / "summary.json").write_text(json.dumps({
        "info": {"id": "0199-test-session", "cwd": "D:\\x\\repo"},
        "generated_title": "test",
    }), encoding="utf-8")
    return session


def make_ledger(tmp: Path) -> Path:
    """A wi tokens.md as an in-run Grok orchestrator writes it (0-token rows, real durations)."""
    text = _ledger.make_template("0011-test")
    rows = (
        "| build | Task 1 schema | 0 | 1m05s | Grok: tokens unobservable in-run |\n"
        "| build | Task 2 ui | 0 | 2m10s | Grok: tokens unobservable in-run |\n"
    )
    # insert data rows just above the orchestrator row (the last table row in the template)
    marker = "| orchestrator | main thread, all phases |"
    text = text.replace(marker, rows + marker)
    p = tmp / "tokens.md"
    p.write_text(text, encoding="utf-8")
    return p


PROGRESS = """\
## Log
- 2026-07-12T10:00:00+03:00 **Update** phase = research
- 2026-07-12T10:04:00+03:00 **Update** design gate opened
- 2026-07-12T10:05:00+03:00 **Update** design gate auto-approved
- 2026-07-12T10:25:00+03:00 **Update** PR opened
"""


class ParseSubagentsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.session = make_session(self.tmp)

    def test_split_rows_exact_and_labeled(self):
        subs = gtr.parse_subagents(self.session)
        self.assertEqual([s["subagent_id"] for s in subs], ["a1", "a2"])
        self.assertEqual(subs[0]["description"], "Task 1 schema")
        self.assertEqual(subs[1]["tokens_used"], 200)
        self.assertEqual(subs[0]["model"], "grok-4.5")

    def test_last_finish_wins(self):
        subs = gtr.parse_subagents(self.session)
        self.assertEqual(subs[0]["tokens_used"], 100)
        self.assertEqual(subs[0]["duration_ms"], 65000)

    def test_orchestrator_context_stats(self):
        orch = gtr.parse_orchestrator(self.session)
        self.assertEqual(orch["peak_total_tokens"], 55000)
        self.assertEqual(orch["context_tokens_used"], 51000)
        self.assertEqual(orch["model"], "grok-4.5")
        self.assertIsNone(orch["cumulative_usage"])


class FinalizeWriteTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.session = make_session(self.tmp)
        self.ledger = make_ledger(self.tmp)
        self.progress = self.tmp / "progress.md"
        self.progress.write_text(PROGRESS, encoding="utf-8")

    def test_finalize_passes_ledger_gate(self):
        rc = gtr.run_write(self.ledger, self.session, self.progress)
        self.assertEqual(rc, 0)
        self.assertIsNone(_ledger.verify(self.ledger))

    def test_finalize_backfills_exact_sum_and_split(self):
        gtr.run_write(self.ledger, self.session, self.progress)
        text = self.ledger.read_text(encoding="utf-8")
        self.assertIn("**Subagents (exact): 300.**", text)
        self.assertIn("## Subagent detail (exact, from Grok session files)", text)
        self.assertIn("Task 2 ui", text)
        self.assertIn(_ledger.UNAVAILABLE, text)          # honest orchestrator sentinel
        self.assertNotIn("_PENDING", text)

    def test_finalize_fills_durations_from_split_and_progress(self):
        gtr.run_write(self.ledger, self.session, self.progress)
        text = self.ledger.read_text(encoding="utf-8")
        # split durations 65s + 130s = 195s = 3m15s
        self.assertIn("**Σ compute: 3m15s across 2 dispatches.**", text)
        # spans: 4m research->gate + 20m gate-ok->PR = 24m
        self.assertIn("**Autonomous wall-clock (excl. manual steps): 24m00s.**", text)

    def test_finalize_requires_existing_ledger(self):
        rc = gtr.run_write(self.tmp / "absent.md", self.session, self.progress)
        self.assertEqual(rc, 1)

    def test_finalize_is_idempotent(self):
        gtr.run_write(self.ledger, self.session, self.progress)
        once = self.ledger.read_text(encoding="utf-8")
        gtr.run_write(self.ledger, self.session, self.progress)
        self.assertEqual(once, self.ledger.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
