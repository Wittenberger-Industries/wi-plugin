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
                "| build W1 | task-runner: t1 | 5 | exact |\n| orchestrator |",
            )
            p.write_text(t, encoding="utf-8")
            self.assertEqual(_ledger.verify(p), "Subagents (exact) sum not filled (still '<sum>')")


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
