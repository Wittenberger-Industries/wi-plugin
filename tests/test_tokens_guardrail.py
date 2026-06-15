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
