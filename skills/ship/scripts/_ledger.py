"""
_ledger.py: shared helpers for the tokens.md token ledger.

NOT an entrypoint. Imported by the two scripts the skills invoke:
  - check_tokens.py  (--init scaffold, default = verify gate)
  - token_report.py  (--write finalize: Orchestrator section + Subagents sum
                      + Duration totals + per-agent split/cost where recoverable)

tokens.md is a per-feature RUNTIME artifact in a user's .wit/, never in this plugin repo.
This module owns the file format; the scripts are thin CLIs over it. Stdlib only.
Canonical prose for the ledger discipline ("the ledger rule"):
skills/research/references/wit-directory.md, tokens.md template section.
"""
import re
from datetime import date
from pathlib import Path

# Exact sentinel ship writes when the orchestrator transcript can't be parsed. The verify
# gate treats this as RESOLVED: an honest "can't measure" passes; only the untouched
# PENDING placeholder fails. Must match the wording in ship/SKILL.md and wit-directory.md.
UNAVAILABLE = "Orchestrator: unavailable for this run"

# [^.*] excludes the literal dot and asterisk, so the lazy capture stops before the closing '.**'
_SUM_RE = re.compile(r"\*\*Subagents \(exact\):\s*([^.*]*?)\.\*\*")
_COMPUTE_RE = re.compile(r"\*\*Σ compute: ([^*]*?) across ([^*]*?) dispatches\.\*\*")
_WALL_RE = re.compile(r"\*\*Autonomous wall-clock \(excl\. manual steps\): ([^*]*?)\.\*\*")
_ORCH_RE = re.compile(r"^## Orchestrator\b.*$", re.MULTILINE)
_DUR_RE = re.compile(r"^(?:(\d+)h)?(?:(\d{1,2})m)?(\d{1,2})s$")

TEMPLATE = """\
---
type: Token Ledger
title: "__TITLE__"
description: Exact per-subagent token usage + the orchestrator total (finalized by ship pre-PR).
feature: __SLUG__
timestamp: __TIMESTAMP__
---

# __TITLE__

Append a row the moment each subagent's completion notification arrives; the figure
exists only there and is NOT retrievable later. Duration comes from the notification's
elapsed time or the orchestrator's own dispatch/arrival stamps (OS clock); write
`unavailable` when unknown, never an estimate. ship finalizes the Orchestrator section.

| Phase | Source | Tokens | Duration | Basis |
|-------|--------|--------|----------|-------|
| orchestrator | main thread, all phases | (see Orchestrator section) | n/a (see below) | parsed by token_report.py; unavailable if the parse fails: never substitute or estimate |

**Subagents (exact): <sum>.**
**Σ compute: <dur> across <n> dispatches.**
**Autonomous wall-clock (excl. manual steps): <dur>.**

## Orchestrator

_PENDING: ship replaces this section during the dossier tidy (BEFORE the dossier commit and the PR) by running `python ${CLAUDE_PLUGIN_ROOT}/skills/ship/scripts/token_report.py --write <this file>` on Claude Code; on a non-Claude host the platform tool map names the finalizer (Grok Build: `grok_token_report.py --write`, references/grok-tools.md). It parses the session data, fills the duration totals from the ledger rows + progress.md phase spans, and appends the exact per-subagent split. That parsed figure is the only reliable orchestrator measure; if the parse fails it writes `Orchestrator: unavailable for this run`; never a substitute, estimate, or invented figure. A tokens.md still reading PENDING after ship is a defect._
"""


def make_template(slug, timestamp=None):
    ts = timestamp or date.today().isoformat()
    return (TEMPLATE.replace("__TITLE__", "Token ledger: " + slug)
                    .replace("__SLUG__", slug)
                    .replace("__TIMESTAMP__", ts))


def format_duration(seconds):
    """Seconds -> '42s' / '3m12s' / '1h03m05s'; None or negative -> 'unavailable'."""
    if seconds is None or seconds < 0:
        return "unavailable"
    s = int(round(seconds))
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return "{}h{:02d}m{:02d}s".format(h, m, sec)
    if m:
        return "{}m{:02d}s".format(m, sec)
    return "{}s".format(sec)


def parse_duration(text):
    """Inverse of format_duration. Returns seconds (int) or None ('unavailable'/unparseable)."""
    m = _DUR_RE.match((text or "").strip())
    if not m:
        return None
    h, mi, s = (int(g) if g else 0 for g in m.groups())
    return h * 3600 + mi * 60 + s


def _data_rows(text):
    """[(tokens, duration_cell_or_None), ...] for ledger rows whose Tokens (3rd) cell is an
    integer. Header, separator, the orchestrator row, and <n> placeholders are excluded.
    duration_cell is None for a malformed short row. Scanning stops at the first '## '
    heading: the ledger table lives above '## Orchestrator' by template design, and the
    finalized tail carries other numeric tables (the per-subagent split) that must never
    be re-counted as ledger rows."""
    rows = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("## "):
            break
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.split("|")[1:-1]]
        if len(cells) < 3:
            continue
        tok = cells[2].replace(",", "").replace("_", "")
        if not tok.isdigit():
            continue
        rows.append((int(tok), cells[3] if len(cells) >= 4 else None))
    return rows


def _data_row_tokens(text):
    return [tok for tok, _dur in _data_rows(text)]


def has_data_row(text):
    return len(_data_row_tokens(text)) > 0


def count_data_rows(text):
    return len(_data_row_tokens(text))


def sum_data_rows(text):
    return sum(_data_row_tokens(text))


def sum_row_durations(text):
    """(seconds_or_None, n_rows): sum of parseable Duration cells across data rows.
    None when no row carries a parseable duration."""
    total, parsed = 0, 0
    rows = _data_rows(text)
    for _tok, dur in rows:
        d = parse_duration(dur) if dur else None
        if d is not None:
            total += d
            parsed += 1
    return (total if parsed else None), len(rows)


def has_duration_column(text):
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("|") and "| Duration |" in s and "| Tokens |" in s:
            return True
    return False


def _duration_cells_ok(text):
    """Every data row must carry a non-empty, non-placeholder Duration cell
    (a real figure or the honest 'unavailable')."""
    for _tok, dur in _data_rows(text):
        if dur is None or not dur or dur.startswith("<"):
            return False
    return True


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


def set_compute_totals(text, compute_seconds, n_dispatches, wall_seconds):
    """Fill (or re-fill) the Σ-compute and autonomous-wall-clock lines. None -> 'unavailable'."""
    comp = format_duration(compute_seconds)
    n = str(n_dispatches if n_dispatches is not None else 0)
    wall = format_duration(wall_seconds)
    text = _COMPUTE_RE.sub(
        lambda _m: "**Σ compute: {} across {} dispatches.**".format(comp, n), text, count=1)
    text = _WALL_RE.sub(
        lambda _m: "**Autonomous wall-clock (excl. manual steps): {}.**".format(wall), text, count=1)
    return text


def compute_totals_filled(text):
    cm, wm = _COMPUTE_RE.search(text), _WALL_RE.search(text)
    if not cm or not wm:
        return False
    vals = (cm.group(1).strip(), cm.group(2).strip(), wm.group(1).strip())
    return all(v and not (v.startswith("<") and v.endswith(">")) for v in vals)


def orchestrator_resolved(text):
    m = _ORCH_RE.search(text)
    if not m:
        return False
    body = text[m.end():]
    # Match the precise '_PENDING' sentinel, not the bare word, so prose that merely
    # mentions "pending" can't be misread as unresolved.
    return "_PENDING" not in body and body.strip() != ""


def replace_tail(text, orchestrator_body, extra_sections=""):
    """Replace from '## Orchestrator' to EOF with the orchestrator body plus any extra
    sections (e.g. the per-subagent split). Re-running regenerates the whole tail, so
    the finalize step stays idempotent."""
    section = "## Orchestrator\n\n" + orchestrator_body.rstrip() + "\n"
    if extra_sections and extra_sections.strip():
        section += "\n" + extra_sections.strip() + "\n"
    m = _ORCH_RE.search(text)
    if not m:
        return text.rstrip() + "\n\n" + section
    # '## Orchestrator' opens the tail by template design, so replacing to EOF is intentional.
    return text[:m.start()] + section


def replace_orchestrator_section(text, body):
    return replace_tail(text, body)


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
    if not has_duration_column(text):
        return "no Duration column in the ledger header (write the current 5-column format)"
    if not subagents_sum_filled(text):
        return "Subagents (exact) sum not filled (still '<sum>')"
    if not compute_totals_filled(text):
        return "duration totals not filled (Σ compute / wall-clock: token_report.py --write fills them)"
    if not orchestrator_resolved(text):
        return "Orchestrator section still PENDING / unresolved"
    # Zero integer-token rows is an honest zero-dispatch / all-unavailable ledger (Codex, Copilot,
    # or an inline-role host): pass once sum/totals/orchestrator are finalized (sum is typically 0).
    # When rows exist, every Duration cell must be a figure or the honest 'unavailable'.
    if has_data_row(text):
        if not _duration_cells_ok(text):
            return "a subagent row's Duration cell is empty (write the figure or 'unavailable')"
    return None
