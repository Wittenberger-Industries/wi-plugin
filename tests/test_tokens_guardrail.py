import json
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
import token_report  # noqa: E402


def _scaffold_text():
    return _ledger.make_template("my-feature", timestamp="2026-06-15")


def _fill_totals(text, compute="1m00s", n="1", wall="unavailable"):
    return (text
            .replace("**Σ compute: <dur> across <n> dispatches.**",
                     "**Σ compute: {} across {} dispatches.**".format(compute, n))
            .replace("**Autonomous wall-clock (excl. manual steps): <dur>.**",
                     "**Autonomous wall-clock (excl. manual steps): {}.**".format(wall)))


def _with_row_and_sum(text, tokens=100):
    text = text.replace(
        "| orchestrator |",
        "| build W1 | task-runner: t1 | {} | 1m00s | exact |\n| orchestrator |".format(tokens),
    )
    return _fill_totals(text.replace("<sum>", str(tokens)))


def _resolve_orchestrator(text, body="Orchestrator: unavailable for this run"):
    return re.sub(r"## Orchestrator[\s\S]*$", "## Orchestrator\n\n" + body + "\n", text)


class LedgerHelperTests(unittest.TestCase):
    def test_template_has_required_markers(self):
        t = _scaffold_text()
        self.assertIn("type: Token Ledger", t)
        self.assertIn("feature: my-feature", t)
        self.assertIn("timestamp: 2026-06-15", t)
        self.assertIn("**Subagents (exact): <sum>.**", t)
        self.assertIn("| Duration |", t)
        self.assertIn("**Σ compute: <dur> across <n> dispatches.**", t)
        self.assertIn("**Autonomous wall-clock (excl. manual steps): <dur>.**", t)
        self.assertIn("## Orchestrator", t)
        self.assertIn("PENDING", t)

    def test_format_duration(self):
        self.assertEqual(_ledger.format_duration(42), "42s")
        self.assertEqual(_ledger.format_duration(192), "3m12s")
        self.assertEqual(_ledger.format_duration(3785), "1h03m05s")
        self.assertEqual(_ledger.format_duration(0), "0s")
        self.assertEqual(_ledger.format_duration(None), "unavailable")
        self.assertEqual(_ledger.format_duration(-5), "unavailable")

    def test_parse_duration_round_trip(self):
        for secs in (0, 9, 42, 60, 192, 3599, 3600, 3785, 7322):
            self.assertEqual(_ledger.parse_duration(_ledger.format_duration(secs)), secs)
        self.assertIsNone(_ledger.parse_duration("unavailable"))
        self.assertIsNone(_ledger.parse_duration("<dur>"))
        self.assertIsNone(_ledger.parse_duration(""))
        self.assertIsNone(_ledger.parse_duration(None))

    def test_set_and_check_compute_totals(self):
        t = _scaffold_text()
        self.assertFalse(_ledger.compute_totals_filled(t))       # placeholders
        t2 = _ledger.set_compute_totals(t, 1040, 4, 2466)
        self.assertIn("**Σ compute: 17m20s across 4 dispatches.**", t2)
        self.assertIn("**Autonomous wall-clock (excl. manual steps): 41m06s.**", t2)
        self.assertTrue(_ledger.compute_totals_filled(t2))
        t3 = _ledger.set_compute_totals(t, None, 0, None)        # honest unavailable
        self.assertIn("**Σ compute: unavailable across 0 dispatches.**", t3)
        self.assertIn("wall-clock (excl. manual steps): unavailable.**", t3)
        self.assertTrue(_ledger.compute_totals_filled(t3))
        # idempotent re-set over already-filled lines
        t4 = _ledger.set_compute_totals(t2, 60, 1, 120)
        self.assertIn("**Σ compute: 1m00s across 1 dispatches.**", t4)

    def test_data_rows_ignore_header_separator_and_orchestrator(self):
        t = _scaffold_text()
        self.assertFalse(_ledger.has_data_row(t))          # only header/sep/orchestrator rows
        t2 = _with_row_and_sum(t, 250)
        self.assertTrue(_ledger.has_data_row(t2))
        self.assertEqual(_ledger.sum_data_rows(t2), 250)

    def test_sum_excludes_orchestrator_and_handles_commas(self):
        t = _scaffold_text().replace(
            "| orchestrator |",
            "| build | task-runner: a | 1,200 | 2m00s | exact |\n| build | task-runner: b | 800 | 30s | exact |\n| orchestrator |",
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

    def test_verify_frontmatter_and_type_and_sum_reasons(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "tokens.md"
            # frontmatter missing
            p.write_text("no frontmatter\n| build | task-runner: t1 | 5 | exact |\n", encoding="utf-8")
            self.assertEqual(_ledger.verify(p), "frontmatter missing or unparseable")
            # wrong type
            p.write_text("---\ntype: Spec\n---\n\n| build | task-runner: t1 | 5 | exact |\n", encoding="utf-8")
            self.assertEqual(_ledger.verify(p), "frontmatter 'type' is not 'Token Ledger'")
            # subagents sum not filled (data row present, <sum> still unfilled, checked before orchestrator)
            t = _scaffold_text().replace(
                "| orchestrator |",
                "| build W1 | task-runner: t1 | 5 | 10s | exact |\n| orchestrator |",
            )
            p.write_text(t, encoding="utf-8")
            self.assertEqual(_ledger.verify(p), "Subagents (exact) sum not filled (still '<sum>')")

    def test_verify_duration_and_totals_gate(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "tokens.md"
            # v2 row with an EMPTY Duration cell fails
            t = _scaffold_text().replace(
                "| orchestrator |",
                "| build W1 | task-runner: t1 | 100 |  | exact |\n| orchestrator |",
            )
            t = _fill_totals(t.replace("<sum>", "100"))
            p.write_text(_resolve_orchestrator(t), encoding="utf-8")
            reason = _ledger.verify(p)
            self.assertIsNotNone(reason)
            self.assertIn("duration", reason.lower())
            # 'unavailable' Duration is an honest value and passes
            t = _scaffold_text().replace(
                "| orchestrator |",
                "| build W1 | task-runner: t1 | 100 | unavailable | exact |\n| orchestrator |",
            )
            t = _fill_totals(t.replace("<sum>", "100"), compute="unavailable", n="1")
            p.write_text(_resolve_orchestrator(t), encoding="utf-8")
            self.assertIsNone(_ledger.verify(p))
            # totals still placeholders fails
            t = _scaffold_text().replace(
                "| orchestrator |",
                "| build W1 | task-runner: t1 | 100 | 1m00s | exact |\n| orchestrator |",
            ).replace("<sum>", "100")
            p.write_text(_resolve_orchestrator(t), encoding="utf-8")
            reason = _ledger.verify(p)
            self.assertIsNotNone(reason)
            self.assertIn("totals", reason.lower())

    def test_verify_four_column_ledger_fails(self):
        # The pre-Duration 4-column format is no longer recognized (#48): the gate
        # rejects it like any other malformed ledger instead of grandfathering it.
        four_col = (
            "---\ntype: Token Ledger\ntitle: old\nfeature: old-feature\ntimestamp: 2026-05-01\n---\n\n"
            "# Token ledger: old-feature\n\n"
            "| Phase | Source | Tokens | Basis |\n"
            "|-------|--------|--------|-------|\n"
            "| build W1 | task-runner: t1 | 100 | exact |\n\n"
            "**Subagents (exact): 100.**\n\n"
            "## Orchestrator\n\nOrchestrator: unavailable for this run\n"
        )
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "tokens.md"
            p.write_text(four_col, encoding="utf-8")
            reason = _ledger.verify(p)
            self.assertIsNotNone(reason)
            self.assertIn("Duration column", reason)


def _write_agent(dirpath, agent_id, *, meta=None, model="claude-opus-4-8",
                 prompt="You implement exactly ONE task for feature 0053- (boilerplate charter prose)"):
    """Write a minimal agent-<id>.jsonl (one usage record + a user prompt) and, if given,
    its sibling agent-<id>.meta.json. Returns the .jsonl Path."""
    sub = Path(dirpath)
    sub.mkdir(parents=True, exist_ok=True)
    jsonl = sub / "agent-{}.jsonl".format(agent_id)
    jsonl.write_text(
        '{"type":"user","message":{"content":' + json.dumps(prompt) + '}}\n'
        '{"message":{"usage":{"input_tokens":10,"output_tokens":20,'
        '"cache_creation_input_tokens":0,"cache_read_input_tokens":5},"model":"' + model + '"}}\n',
        encoding="utf-8",
    )
    if meta is not None:
        (sub / "agent-{}.meta.json".format(agent_id)).write_text(
            json.dumps(meta), encoding="utf-8")
    return jsonl


class AgentLabelTests(unittest.TestCase):
    def test_label_prefers_meta_description(self):
        with tempfile.TemporaryDirectory() as d:
            j = _write_agent(d, "a1", meta={"agentType": "wi:wi-task-runner",
                                             "description": "task-runner: task 3 (@/db seam)"})
            a = token_report.parse_agent_file(j)
            self.assertEqual(a["label"], "task-runner: task 3 (@/db seam)")

    def test_label_falls_back_to_agent_type_when_description_blank(self):
        with tempfile.TemporaryDirectory() as d:
            j = _write_agent(d, "a2", meta={"agentType": "wi:wi-researcher", "description": "  "})
            a = token_report.parse_agent_file(j)
            self.assertEqual(a["label"], "wi-researcher")

    def test_label_falls_back_to_prompt_prefix_without_meta(self):
        with tempfile.TemporaryDirectory() as d:
            j = _write_agent(d, "a3", meta=None)  # no sidecar -> legacy behavior
            a = token_report.parse_agent_file(j)
            self.assertTrue(a["label"].startswith("You implement exactly ONE task"))
            self.assertLessEqual(len(a["label"]), 48)

    def test_label_survives_unparseable_meta(self):
        with tempfile.TemporaryDirectory() as d:
            j = _write_agent(d, "a4", meta=None)
            (Path(d) / "agent-a4.meta.json").write_text("{not json", encoding="utf-8")
            a = token_report.parse_agent_file(j)  # must not raise
            self.assertTrue(a["label"].startswith("You implement exactly ONE task"))

    def test_label_normalizes_and_caps_description(self):
        with tempfile.TemporaryDirectory() as d:
            j = _write_agent(d, "a5", meta={"agentType": "x",
                                            "description": "a b   c | d " + "z" * 60})
            a = token_report.parse_agent_file(j)
            self.assertNotIn("|", a["label"])
            self.assertNotIn("  ", a["label"])
            self.assertLessEqual(len(a["label"]), 48)


CHECK = SCRIPTS / "check_tokens.py"
REPORT = SCRIPTS / "token_report.py"


def run(*args):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True)


def init_ledger(d, slug="my-feature"):
    p = Path(d) / slug / "tokens.md"
    run(CHECK, "--init", p)
    return p


class CheckTokensCliTests(unittest.TestCase):
    def test_init_creates_when_absent(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "my-feature" / "tokens.md"
            r = run(CHECK, "--init", p)
            self.assertEqual(r.returncode, 0, r.stderr)
            text = p.read_text(encoding="utf-8")
            self.assertIn("type: Token Ledger", text)
            self.assertIn("feature: my-feature", text)
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


def fixture_transcript(d):
    f = Path(d) / "t.jsonl"
    f.write_text(
        '{"message":{"usage":{"input_tokens":10,"output_tokens":20,'
        '"cache_creation_input_tokens":0,"cache_read_input_tokens":5},"model":"claude-opus-4-8"}}\n'
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
            "| build W1 | task-runner: t1 | 100 | 1m00s | exact |\n"
            "| build W1 | task-runner: t2 | 50 | 1m30s | exact |\n| orchestrator |",
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
            self.assertIn("**Σ compute: 2m30s across 2 dispatches.**", out)
            # no sibling progress.md in this fixture -> honest unavailable
            self.assertIn("wall-clock (excl. manual steps): unavailable.**", out)
            self.assertIn("- model: claude-opus-4-8", out)
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

    def test_split_rows_labeled_from_meta_and_join_ledger_source(self):
        with tempfile.TemporaryDirectory() as d:
            # ledger row Source == the dispatch description we will stamp in meta.json
            p = init_ledger(d)
            text = p.read_text(encoding="utf-8").replace(
                "| orchestrator |",
                "| research | researcher: db seam | 30 | 1m00s | exact |\n| orchestrator |",
            )
            p.write_text(text, encoding="utf-8")
            t = fixture_transcript(d)  # -> <d>/t.jsonl ; sidecars live in <d>/t/subagents/
            _write_agent(Path(d) / "t" / "subagents", "b1",
                         meta={"agentType": "wi:wi-researcher", "description": "researcher: db seam"})
            r = run(REPORT, "--write", p, "--transcript", t)
            self.assertEqual(r.returncode, 0, r.stderr)
            out = p.read_text(encoding="utf-8")
            self.assertIn("## Subagent detail", out)
            # the split row's first cell verbatim-contains the ledger Source name
            self.assertIn("| researcher: db seam (b1) |", out)
            # idempotent: a second --write neither duplicates the section nor changes the label
            r2 = run(REPORT, "--write", p, "--transcript", t)
            self.assertEqual(r2.returncode, 0, r2.stderr)
            out2 = p.read_text(encoding="utf-8")
            self.assertEqual(out2.count("## Subagent detail"), 1)
            self.assertEqual(out, out2)

    def test_write_missing_file_errors_and_creates_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "nope" / "tokens.md"
            r = run(REPORT, "--write", p, "--transcript", fixture_transcript(d))
            self.assertNotEqual(r.returncode, 0)
            self.assertFalse(p.exists())


if __name__ == "__main__":
    unittest.main()
