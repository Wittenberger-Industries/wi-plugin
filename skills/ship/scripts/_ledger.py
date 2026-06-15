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
