#!/usr/bin/env python3
"""
grok_token_report.py: the Grok Build counterpart of token_report.py; reads Grok's
session files and finalizes a feature's tokens.md on a Grok host.

  grok_token_report.py [--session ID] [--cwd DIR]      # print the report
  grok_token_report.py --write TOKENS_MD [--progress PROGRESS_MD]
                                                       # finalize the existing ledger

Claude Code's token_report.py sums per-turn `usage` from the JSONL transcript. Grok
Build's TUI persists no cumulative input/output ledger for the parent session, but it
does persist EXACT per-subagent figures. This script reads what Grok writes under
~/.grok/sessions/<url-encoded-cwd>/<session-id>/:

  Subagents (exact):  `subagent_finished` events in updates.jsonl -> tokens_used,
                      duration_ms, tool_calls, turns; labels from subagents/*/meta.json
                      `description` (== the ledger Source cell by wi convention).
  Orchestrator:       signals.json context occupancy + peak `totalTokens` in the
                      updates stream. These measure CONTEXT WINDOW size, never
                      cumulative billable I/O; the ledger records them as such and the
                      Orchestrator line stays the honest `unavailable` sentinel.

--write mirrors token_report.py --write: it never creates the file (check_tokens.py
--init scaffolds it; the run appends the rows), it replaces the tail idempotently via
_ledger, sets the Subagents (exact) sum from the SESSION split (on Grok the in-run rows
record Tokens 0/unavailable: the exact figures live in the session files, recovered
here), fills the duration totals (compute from the split's exact durations, wall-clock
from progress.md's phase-span stamps), and appends the per-subagent split section.
Row cells are never edited (ledger append order is not session completion order).

Stdlib only (+ sibling _ledger). Never estimates: missing figures are `unavailable`.
Stdout stays ASCII (Windows cp1252 consoles); the file itself is UTF-8.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
from pathlib import Path

import _ledger

STAMP_RE = re.compile(
    r"^\s*-\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+\-]\d{2}:?\d{2}))\b"
)


# --- session discovery ----------------------------------------------------------------

def grok_home() -> Path:
    env = os.environ.get("GROK_HOME")
    return Path(env) if env else Path.home() / ".grok"


def sessions_root() -> Path:
    return grok_home() / "sessions"


def encode_cwd(cwd: Path) -> str:
    """Grok's session-group naming: the URL-encoded absolute path (quote, safe='')."""
    return urllib.parse.quote(str(cwd.resolve()), safe="")


def _norm(p: str) -> str:
    """Case/separator-insensitive path key for matching active_sessions cwd entries."""
    return os.path.normcase(os.path.normpath(p))


def active_session_for_cwd(cwd: Path) -> str | None:
    path = grok_home() / "active_sessions.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, list):
        return None
    target = _norm(str(cwd.resolve()))
    exact, prefix = None, None
    for row in data:
        if not isinstance(row, dict):
            continue
        sid, scwd = row.get("session_id"), row.get("cwd")
        if not sid or not scwd:
            continue
        s = _norm(scwd)
        if s == target:
            exact = sid
        elif target.startswith(s + os.sep) or s.startswith(target + os.sep):
            prefix = sid
    return exact or prefix


def find_session_dir(session_id: str) -> Path | None:
    root = sessions_root()
    if not root.is_dir():
        return None
    for group in root.iterdir():
        if not group.is_dir():
            continue
        candidate = group / session_id
        if (candidate / "summary.json").is_file() or (candidate / "updates.jsonl").is_file():
            return candidate
    return None


def newest_session_in_group(group: Path) -> Path | None:
    best, best_mtime = None, -1.0
    if not group.is_dir():
        return None
    for child in group.iterdir():
        if not child.is_dir():
            continue
        marker = child / "summary.json"
        if not marker.is_file():
            marker = child / "updates.jsonl"
            if not marker.is_file():
                continue
        try:
            mtime = marker.stat().st_mtime
        except OSError:
            continue
        if mtime > best_mtime:
            best, best_mtime = child, mtime
    return best


def resolve_session_dir(session_id: str | None, cwd: Path) -> Path:
    if session_id:
        found = find_session_dir(session_id)
        if found is None:
            raise SystemExit(f"session not found: {session_id} under {sessions_root()}")
        return found
    sid = active_session_for_cwd(cwd)
    if sid:
        found = find_session_dir(sid)
        if found is not None:
            return found
    newest = newest_session_in_group(sessions_root() / encode_cwd(cwd))
    if newest is not None:
        return newest
    raise SystemExit(
        f"no Grok session found for cwd={cwd} (looked under {sessions_root()}); "
        "pass --session <id> explicitly"
    )


# --- JSON walk helpers ------------------------------------------------------------------

def walk(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v)


def find_dict_with(obj, **eq):
    for d in walk(obj):
        if all(d.get(k) == v for k, v in eq.items()):
            return d
    return None


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, ValueError):
        return None


# --- parse -------------------------------------------------------------------------------

def load_meta_map(session_dir: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    sub = session_dir / "subagents"
    if not sub.is_dir():
        return out
    for child in sub.iterdir():
        data = load_json(child / "meta.json")
        if isinstance(data, dict):
            out[data.get("subagent_id") or child.name] = data
    return out


def parse_subagents(session_dir: Path) -> list[dict]:
    """Exact per-dispatch figures from subagent_finished events (last finish wins per id)."""
    updates = session_dir / "updates.jsonl"
    if not updates.is_file():
        return []
    meta_map = load_meta_map(session_dir)
    seen: dict[str, dict] = {}
    order: list[str] = []
    with updates.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            if "subagent_finished" not in line or "tokens_used" not in line:
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            evt = find_dict_with(obj, sessionUpdate="subagent_finished")
            if not evt:
                continue
            sid = evt.get("subagent_id") or evt.get("child_session_id")
            tokens = evt.get("tokens_used")
            if not sid or not isinstance(tokens, int):
                continue
            meta = meta_map.get(sid, {})
            row = {
                "subagent_id": sid,
                "tokens_used": tokens,
                "duration_ms": evt.get("duration_ms") if isinstance(evt.get("duration_ms"), int)
                else meta.get("duration_ms"),
                "tool_calls": evt.get("tool_calls") if isinstance(evt.get("tool_calls"), int)
                else meta.get("tool_calls"),
                "turns": evt.get("turns") if isinstance(evt.get("turns"), int)
                else meta.get("turns"),
                "status": evt.get("status") or meta.get("status"),
                "description": meta.get("description") or sid,
                "model": meta.get("effective_model_id") or meta.get("model"),
                "subagent_type": meta.get("subagent_type"),
            }
            if sid not in seen:
                order.append(sid)
            seen[sid] = row
    return [seen[i] for i in order]


def parse_orchestrator(session_dir: Path) -> dict:
    """Context-window stats for the parent session; never a cumulative I/O figure."""
    signals = load_json(session_dir / "signals.json") or {}
    summary = load_json(session_dir / "summary.json") or {}
    peak = None
    updates = session_dir / "updates.jsonl"
    if updates.is_file():
        with updates.open(encoding="utf-8", errors="replace") as f:
            for line in f:
                if "totalTokens" not in line:
                    continue
                try:
                    obj = json.loads(line)
                except ValueError:
                    continue
                for d in walk(obj):
                    tt = d.get("totalTokens")
                    if isinstance(tt, int) and (peak is None or tt > peak):
                        peak = tt
    info = summary.get("info") if isinstance(summary.get("info"), dict) else {}
    return {
        "session_id": info.get("id") or session_dir.name,
        "cwd": info.get("cwd") or summary.get("cwd"),
        "model": signals.get("primaryModelId") or summary.get("current_model_id")
        or (signals.get("modelsUsed") or [None])[0],
        "context_tokens_used": signals.get("contextTokensUsed"),
        "context_window_tokens": signals.get("contextWindowTokens"),
        "context_window_usage_pct": signals.get("contextWindowUsage"),
        "peak_total_tokens": peak,
        "turn_count": signals.get("turnCount"),
        "assistant_message_count": signals.get("assistantMessageCount"),
        "tool_call_count": signals.get("toolCallCount"),
        "session_duration_seconds": signals.get("sessionDurationSeconds"),
        "title": summary.get("generated_title") or summary.get("session_summary"),
        "cumulative_usage": None,  # the TUI does not persist it; never substituted
    }


# --- progress.md phase spans (same boundaries as token_report.py) -------------------------

def _iso(ts):
    from datetime import datetime
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _progress_marks(text):
    """(research, gate_open, gate_ok, end) tz-aware datetimes from progress.md, each or None."""
    events = []
    for line in text.splitlines():
        m = STAMP_RE.match(line)
        if not m:
            continue
        dt = _iso(m.group(1))
        if dt is None or dt.tzinfo is None:
            continue
        events.append((dt, line.lower()))

    def first(*phrases):
        for dt, low in events:
            if any(p in low for p in phrases):
                return dt
        return None

    def last(*phrases):
        hit = None
        for dt, low in events:
            if any(p in low for p in phrases):
                hit = dt
        return hit

    return (first("phase = research"), first("design gate opened"),
            last("design gate approved", "design gate auto-approved"),
            last("pr opened") or last("phase = done"))


def _span(a, b):
    if a is None or b is None:
        return None
    s = (b - a).total_seconds()
    return int(s) if s >= 0 else None


def parse_progress_spans(text):
    research, gate_open, gate_ok, end = _progress_marks(text)
    return _span(research, gate_open), _span(gate_ok, end)


def approval_wait_seconds(session_dir: Path, windows) -> int:
    """Sum permission-prompt waits (events.jsonl `permission_resolved.wait_ms`) whose event ts
    falls inside any (start, end) window. Grok measures each prompt's human wait itself; this
    is what makes the wall-clock's 'excl. manual steps' honest on a prompted run. Missing
    events.jsonl, no timestamps, or no windows -> 0."""
    events = Path(session_dir) / "events.jsonl"
    unfiltered = windows is None  # None = whole session (print mode); a list filters by window
    windows = [] if unfiltered else [(a, b) for a, b in windows if a is not None and b is not None]
    if not events.is_file() or (not unfiltered and not windows):
        return 0
    total_ms = 0
    with events.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            if '"permission_resolved"' not in line:
                continue
            try:
                d = json.loads(line)
            except ValueError:
                continue
            wait = d.get("wait_ms")
            ts = _iso(d.get("ts") or "")
            if not isinstance(wait, (int, float)) or wait <= 0 or ts is None or ts.tzinfo is None:
                continue
            if unfiltered or any(a <= ts <= b for a, b in windows):
                total_ms += wait
    return int(round(total_ms / 1000.0))


# --- report / finalize ---------------------------------------------------------------------

def _dur_s(ms):
    return _ledger.format_duration(None if ms is None else int(round(ms / 1000.0)))


def orchestrator_body(session_dir: Path, orch: dict, approval_wait_s: int = 0) -> str:
    """The tokens.md Orchestrator tail: the honest sentinel + context-occupancy facts."""
    lines = [
        _ledger.UNAVAILABLE,
        "",
        "- host: Grok Build (session `{}`)".format(orch["session_id"]),
        "- session dir: `{}`".format(session_dir),
        "- model: {}".format(orch.get("model") or "unavailable"),
    ]
    ctx, peak, win = (orch.get("context_tokens_used"), orch.get("peak_total_tokens"),
                      orch.get("context_window_tokens"))
    if isinstance(ctx, int):
        lines.append("- context_tokens_used (current window fill): {:,}".format(ctx))
    if isinstance(peak, int):
        lines.append("- peak totalTokens in the updates stream (context occupancy): {:,}".format(peak))
    if isinstance(win, int):
        pct = orch.get("context_window_usage_pct")
        lines.append("- context window: {:,}{}".format(win, " ({}%)".format(pct) if pct is not None else ""))
    lines.append("- turns / assistant msgs / tool calls: {} / {} / {}".format(
        orch.get("turn_count"), orch.get("assistant_message_count"), orch.get("tool_call_count")))
    lines.append("- session wall duration (incl. idle): {}".format(
        _ledger.format_duration(orch.get("session_duration_seconds"))))
    if approval_wait_s > 0:
        lines.append("- approval-wait inside the autonomous windows (permission prompts, "
                     "`events.jsonl` wait_ms): {} - subtracted from the wall-clock total"
                     .format(_ledger.format_duration(approval_wait_s)))
    lines.append(
        "- NOTE: the Grok TUI persists no cumulative input/output for the parent session; "
        "the figures above are context-window occupancy and are never added to the "
        "subagent total (mixed metrics). Per-subagent tokens_used below is exact.")
    return "\n".join(lines)


def split_section(subagents: list[dict]) -> str:
    """Render '## Subagent detail (exact, from Grok session files)'; '' if none."""
    if not subagents:
        return ""
    lines = [
        "## Subagent detail (exact, from Grok session files)",
        "",
        "| Agent | Model | Tokens | Duration | Tools | Turns |",
        "|-------|-------|--------|----------|-------|-------|",
    ]
    for s in subagents:
        label = " ".join((s.get("description") or s["subagent_id"]).split()).replace("|", "/")[:48]
        lines.append("| {} | {} | {:,} | {} | {} | {} |".format(
            label, s.get("model") or "unknown", s["tokens_used"], _dur_s(s.get("duration_ms")),
            s.get("tool_calls") if s.get("tool_calls") is not None else "unavailable",
            s.get("turns") if s.get("turns") is not None else "unavailable"))
    total = sum(s["tokens_used"] for s in subagents)
    lines.append("")
    lines.append("Tokens are Grok's `subagent_finished.tokens_used` (exact). The ledger rows above "
                 "record 0/unavailable in-run (the figure is unobservable at dispatch return on "
                 "Grok); the Subagents (exact) sum is set from this split: {:,} across {} "
                 "dispatches. No cost estimate: Grok Build exposes no per-token list price."
                 .format(total, len(subagents)))
    return "\n".join(lines)


def run_print(session_dir: Path) -> int:
    """Human report. ASCII-only stdout: Windows consoles often run cp1252."""
    orch = parse_orchestrator(session_dir)
    subs = parse_subagents(session_dir)
    total = sum(s["tokens_used"] for s in subs)
    dur_ms = sum((s.get("duration_ms") or 0) for s in subs)
    print("Grok session: {}".format(orch["session_id"]))
    print("  dir:   {}".format(session_dir))
    if orch.get("cwd"):
        print("  cwd:   {}".format(orch["cwd"]))
    print("  model: {}".format(orch.get("model") or "unavailable"))
    print()
    print("## Subagents (exact - tokens_used on subagent_finished)")
    if not subs:
        print("  (none)")
    else:
        print("  {:44} {:>10} {:>10} {:>6} {:>5}".format("description", "tokens", "duration", "tools", "turns"))
        print("  " + "-" * 80)
        for s in subs:
            print("  {:44} {:>10,} {:>10} {:>6} {:>5}".format(
                (s.get("description") or s["subagent_id"])[:44], s["tokens_used"],
                _dur_s(s.get("duration_ms")),
                str(s.get("tool_calls")) if s.get("tool_calls") is not None else "-",
                str(s.get("turns")) if s.get("turns") is not None else "-"))
        print("  " + "-" * 80)
        print("  {:44} {:>10,}".format("SUBAGENTS TOTAL (exact)", total))
        print("  sum of dispatch durations: {} across {} dispatches".format(_dur_s(dur_ms), len(subs)))
    wait_all = approval_wait_seconds(session_dir, None)
    if wait_all:
        print("  approval-wait, whole session (permission prompts): {}".format(_ledger.format_duration(wait_all)))
    print()
    print("## Orchestrator (parent session - context occupancy, NOT cumulative I/O)")
    for ln in orchestrator_body(session_dir, orch).splitlines()[2:]:
        print("  " + ln)
    return 0


def run_write(token_path, session_dir, progress=None) -> int:
    """Finalize an existing wi tokens.md from the Grok session (mirror of token_report --write)."""
    p = Path(token_path)
    if not p.is_file():
        print("grok_token_report: {} does not exist - run check_tokens.py --init first".format(token_path),
              file=sys.stderr)
        return 1
    text = p.read_text(encoding="utf-8", errors="replace")

    orch = parse_orchestrator(Path(session_dir))
    subs = parse_subagents(Path(session_dir))
    total = sum(s["tokens_used"] for s in subs)
    n = len(subs)
    compute_s = None
    if subs:
        compute_s = int(round(sum((s.get("duration_ms") or 0) for s in subs) / 1000.0))

    ppath = Path(progress) if progress else p.parent / "progress.md"
    span1 = span2 = None
    wait_s = 0
    if ppath.is_file():
        ptext = ppath.read_text(encoding="utf-8", errors="replace")
        research, gate_open, gate_ok, end = _progress_marks(ptext)
        span1, span2 = _span(research, gate_open), _span(gate_ok, end)
        # #71: the wall-clock says "excl. manual steps" - subtract the measured human
        # approval-waits that fall inside the autonomous windows (Grok logs wait_ms per prompt).
        wait_s = approval_wait_seconds(Path(session_dir),
                                       [(research, gate_open), (gate_ok, end)])
    spans = [s for s in (span1, span2) if s is not None]
    wall = sum(spans) if spans else None
    if wall is not None and wait_s:
        wall = max(0, wall - wait_s)

    text = _ledger.replace_tail(text, orchestrator_body(Path(session_dir), orch, wait_s), split_section(subs))
    if subs:
        # Exact source of truth on Grok is the session split, not the 0/unavailable rows.
        text = _ledger.set_subagents_sum(text, total)
    text = _ledger.set_compute_totals(text, compute_s, n, wall)

    p.write_text(text, encoding="utf-8")
    print("grok_token_report: finalized {}".format(token_path))
    print("timing: research+plan={} build+ship={} autonomous-total={} (net of approval-wait={}) | sum-compute={} across {} dispatches".format(
        _ledger.format_duration(span1), _ledger.format_duration(span2),
        _ledger.format_duration(wall), _ledger.format_duration(wait_s) if wait_s else "0s",
        _ledger.format_duration(compute_s), n))
    return 0


# --- main -------------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Grok Build session token report (subagents exact; orchestrator context only); "
                    "--write finalizes a wi tokens.md ledger.")
    ap.add_argument("--session", "-s", dest="session_id",
                    help="Grok session UUID (default: active session for --cwd, else newest in the cwd group)")
    ap.add_argument("--cwd", default=os.getcwd(),
                    help="working directory whose session group to use (default: process cwd)")
    ap.add_argument("--write", metavar="TOKENS_MD",
                    help="finalize this existing tokens.md (Orchestrator tail, exact Subagents sum, "
                         "duration totals, per-subagent split), then exit")
    ap.add_argument("--progress", metavar="PROGRESS_MD",
                    help="explicit progress.md for the wall-clock spans (default: sibling of TOKENS_MD)")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON instead of the report")
    args = ap.parse_args(argv)

    session_dir = resolve_session_dir(args.session_id, Path(args.cwd))
    if args.json:
        subs = parse_subagents(session_dir)
        json.dump({
            "session_dir": str(session_dir),
            "orchestrator": parse_orchestrator(session_dir),
            "subagents": subs,
            "subagents_tokens_sum": sum(s["tokens_used"] for s in subs),
            "subagents_duration_ms_sum": sum((s.get("duration_ms") or 0) for s in subs),
        }, sys.stdout, indent=2)
        print()
        return 0
    if args.write:
        return run_write(args.write, session_dir, args.progress)
    return run_print(session_dir)


if __name__ == "__main__":
    sys.exit(main())
