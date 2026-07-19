"""Tests for skills/add-issues/scripts/check_draft.py."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "add-issues" / "scripts" / "check_draft.py"

BUG_OK = """---
type: Issue Draft
title: "ship: example failure"
description: "demo bug"
timestamp: 2026-07-19
issue_type: Bug
labels: []
assignees: []
milestone:
parent:
blocked_by: []
---

# ship: example failure

## Summary
Something breaks.

## Steps to reproduce
1. Run the command

## Actual results
It fails

## Expected results
It works

## Root cause
Unknown - needs investigation

## Proposed fix
TBD

## Acceptance criteria
- [ ] New test `tests/test_ship.py::test_example` fails on the bug and passes after the fix
- [ ] Behavior restored
"""

BUG_NO_TEST = BUG_OK.replace(
    "- [ ] New test `tests/test_ship.py::test_example` fails on the bug and passes after the fix\n",
    "- [ ] Manual repro checklist only\n",
)

FEATURE_OK = """---
type: Issue Draft
title: "scan: add capability"
description: "demo feature"
timestamp: 2026-07-19
issue_type: Feature
labels: []
assignees: []
milestone:
parent:
blocked_by: []
---

# scan: add capability

## Summary
Add a thing.

## Motivation
Users need it.

## Proposed solution
Ship the thing.

## Acceptance criteria
- [ ] Thing is available
- [ ] Tests cover the new behavior in `scan`
"""


class CheckDraftCliTests(unittest.TestCase):
    def _write(self, text: str) -> Path:
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        path = Path(td.name) / "draft.md"
        path.write_text(text, encoding="utf-8")
        return path

    def _run(self, path: Path, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(path), *extra],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_bug_ok(self):
        r = self._run(self._write(BUG_OK))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("draft ok", r.stdout)

    def test_bug_ok_crlf(self):
        """Windows-style CRLF drafts must pass (publish awk is already CRLF-safe)."""
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        path = Path(td.name) / "draft.md"
        path.write_bytes(BUG_OK.replace("\n", "\r\n").encode("utf-8"))
        r = self._run(path)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("draft ok", r.stdout)

    def test_bug_ok_quoted_issue_type(self):
        """YAML-quoted issue_type values must parse (not 'got: none')."""
        for quoted in ('issue_type: "Bug"', "issue_type: 'Bug'"):
            with self.subTest(quoted=quoted):
                draft = BUG_OK.replace("issue_type: Bug", quoted)
                r = self._run(self._write(draft))
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                self.assertIn("draft ok", r.stdout)

    def test_bug_missing_new_test(self):
        r = self._run(self._write(BUG_NO_TEST))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("DRAFT CHECK FAILED", r.stdout)
        self.assertIn("new automated test", r.stdout)

    def test_bug_rejects_test_substring_false_positives(self):
        """Substring 'test' alone (contested / attestation / latest) is not enough."""
        for criterion in (
            "Behavior is contested and needs triage",
            "Manual attestation of the fix in staging",
            "Latest release still broken",
        ):
            with self.subTest(criterion=criterion):
                draft = BUG_OK.replace(
                    "- [ ] New test `tests/test_ship.py::test_example` "
                    "fails on the bug and passes after the fix\n",
                    f"- [ ] {criterion}\n",
                )
                r = self._run(self._write(draft))
                self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
                self.assertIn("new automated test", r.stdout)

    def test_bug_accepts_new_automated_test_variants(self):
        for criterion in (
            "New test `tests/test_ship.py::test_example` fails on the bug and passes after the fix",
            "Add automated test `tests/foo.py::test_bar` that fails before the fix",
            "Regression test covering the edge case fails on the bug and passes after",
            "Unit test for the parser fails on the bug and passes after the fix",
        ):
            with self.subTest(criterion=criterion):
                draft = BUG_OK.replace(
                    "- [ ] New test `tests/test_ship.py::test_example` "
                    "fails on the bug and passes after the fix\n",
                    f"- [ ] {criterion}\n",
                )
                r = self._run(self._write(draft))
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_bug_allow_no_test(self):
        r = self._run(self._write(BUG_NO_TEST), "--allow-no-test")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_feature_ok(self):
        r = self._run(self._write(FEATURE_OK))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_missing_section(self):
        bad = BUG_OK.replace("## Proposed fix\nTBD\n\n", "")
        r = self._run(self._write(bad))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Proposed fix", r.stdout)

    def test_missing_frontmatter(self):
        r = self._run(self._write("# no frontmatter\n\n## Summary\n"))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("missing OKF frontmatter", r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
