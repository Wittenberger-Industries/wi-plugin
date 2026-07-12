#!/usr/bin/env python3
"""
token_report.py: sum the main-thread (orchestrator) token usage from a Claude Code
session transcript (JSONL), and optionally write it into a feature's tokens.md.

  token_report.py [TRANSCRIPT.jsonl]      # print the orchestrator report (auto-detects transcript)
  token_report.py --write TOKENS_MD [--transcript T.jsonl] [--progress PROGRESS_MD]
                                          # finalize: replace the tokens.md Orchestrator
                                          # section + recompute the Subagents (exact) sum
                                          # + fill the duration totals + append the exact
                                          # per-subagent split/cost (Claude Code)

The model can't read its own running total mid-turn, but the harness records a `usage`
object on every assistant message in the session transcript. --write turns the parsed
result into the ledger directly, so there is no manual stdout-copy step to skip. On a
parse failure it writes `Orchestrator: unavailable for this run`; never a substitute,
estimate, or fabricated figure. It does NOT create the file (run check_tokens.py --init
first); --write exits non-zero only if the file is absent or unwritable.

Timing (issue #35): Σ compute is summed from the ledger rows' Duration cells; the
autonomous wall-clock is the sum of the two autonomous phase spans read from
progress.md's full-ISO Log stamps (research→gate-open + gate-approved→PR/done), which
by construction excludes brainstorm, the handoff, the design-gate wait, and idle time
between resumed sessions. Anything unrecoverable is written `unavailable`.

Subagent split (Claude Code): each dispatch's transcript lives at
<transcript-dir>/<session-id>/subagents/agent-<id>.jsonl with exact per-turn `usage`,
`message.model`, and OS timestamps, parsed here into a per-agent split, duration, and
cost estimate (exact tokens × published list prices; clearly labeled an estimate).

Stdlib only. Canonical prose for the ledger discipline ("the ledger rule"):
skills/research/references/wit-directory.md, tokens.md template section.
"""
import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import _ledger

FIELDS = ("input_tokens", "output_tokens",
          "cache_creation_input_tokens", "cache_read_input_tokens")

# --- cost estimate (extension A) ---------------------------------------------------
# List prices in USD per MTok (input, output), longest-prefix match on message.model.
# Cost is an ESTIMATE derived from exact token counts; token figures themselves stay
# exact-or-unavailable. Update alongside published pricing; unknown models are reported
# as unpriced rather than guessed.
PRICES_AS_OF = "2026-06-24"
PRICES = {
    "claude-fable-5": (10, 50), "claude-mythos-5": (10, 50),
    "claude-opus-4-8": (5, 25), "claude-opus-4-7": (5, 25),
    "claude-opus-4-6": (5, 25), "claude-opus-4-5": (5, 25),
    "claude-sonnet-5": (3, 15), "claude-sonnet-4-6": (3, 15), "claude-sonnet-4-5": (3, 15),
    "claude-haiku-4-5": (1, 5),
}
CACHE_READ_X = 0.1    # cache-read tokens bill at ~0.1x the input price
CACHE_WRITE_X = 1.25  # cache-write at 1.25x input (5-minute TTL, Claude Code's default)

STAMP_RE = re.compile(
    r"^\s*-\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+\-]\d{2}:?\d{2}))\b")


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


def _iso(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def parse_transcript(path):
    """Return (totals, turns, model) or None if the transcript has no usage records.
    model = the most frequent message.model (the session's tier), or None."""
    tot = {k: 0 for k in FIELDS}
    turns = 0
    models = Counter()
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
            model = (obj.get("message") or {}).get("model")
            if model:
                models[model] += 1
    if turns == 0:
        return None
    return tot, turns, (models.most_common(1)[0][0] if models else None)


def price_for(model):
    best = None
    for prefix, p in PRICES.items():
        if (model or "").startswith(prefix) and (best is None or len(prefix) > best[0]):
            best = (len(prefix), p)
    return best[1] if best else None


def estimate_cost(model, tot):
    """USD estimate from exact token counts x list prices; None = no price on file."""
    p = price_for(model)
    if p is None:
        return None
    pin, pout = p
    return (tot["input_tokens"] * pin
            + tot["output_tokens"] * pout
            + tot["cache_creation_input_tokens"] * CACHE_WRITE_X * pin
            + tot["cache_read_input_tokens"] * CACHE_READ_X * pin) / 1_000_000.0


# --- progress.md phase spans (issue #35) --------------------------------------------

def parse_progress_spans(text):
    """(span1_seconds, span2_seconds) from progress.md's ## Log full-ISO stamps.

    span1 (research+plan) = first 'design gate opened' - first 'phase = research'
    span2 (build+ship)    = last 'PR opened' (else last 'phase = done')
                            - last 'design gate approved'/'design gate auto-approved'
    Date-only stamps are ignored; a missing boundary or negative delta yields None.
    """
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

    def span(a, b):
        if a is None or b is None:
            return None
        s = (b - a).total_seconds()
        return int(s) if s >= 0 else None

    research = first("phase = research")
    gate_open = first("design gate opened")
    gate_ok = last("design gate approved", "design gate auto-approved")
    end = last("pr opened") or last("phase = done")
    return span(research, gate_open), span(gate_ok, end)


# --- subagent sidecar transcripts (extension A) --------------------------------------

def find_subagent_files(transcript):
    """Claude Code layout: <dir>/<session>.jsonl + <dir>/<session>/subagents/agent-*.jsonl."""
    d = Path(transcript).with_suffix("") / "subagents"
    return sorted(d.glob("agent-*.jsonl")) if d.is_dir() else []


def read_agent_meta(path):
    """The harness's sidecar `agent-<id>.meta.json` (beside the .jsonl) as a dict, or {}.
    Absent, unreadable, or invalid JSON all fall through to {} (older sessions, Codex/Copilot)."""
    meta = Path(path).with_name(Path(path).stem + ".meta.json")
    try:
        obj = json.loads(meta.read_text(encoding="utf-8", errors="replace"))
        return obj if isinstance(obj, dict) else {}
    except (OSError, ValueError):
        return {}


def _clean_label(text):
    return " ".join((text or "").split()).replace("|", "/")[:48]


def parse_agent_file(path):
    """One sidecar transcript -> {agent, model, tot, duration, label} or None (no usage).

    label prefers the dispatch's human name so the split joins the ledger's Source column
    (issue #53): meta.json `description` (== the ledger Source by convention) -> `agentType`
    short name -> the dispatch prompt's opening -> `(no prompt)`."""
    tot = {k: 0 for k in FIELDS}
    model, label, first_ts, last_ts, turns = None, "", None, None, 0
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            ts = obj.get("timestamp")
            if isinstance(ts, str):
                dt = _iso(ts)
                if dt is not None and dt.tzinfo is not None:
                    first_ts = first_ts or dt
                    last_ts = dt
            msg = obj.get("message") or {}
            if not label and obj.get("type") == "user":
                c = msg.get("content")
                if isinstance(c, str):
                    label = c
                elif isinstance(c, list):
                    label = next((b.get("text", "") for b in c
                                  if isinstance(b, dict) and b.get("type") == "text"), "")
            u = extract_usage(obj)
            if u:
                turns += 1
                for k in FIELDS:
                    v = u.get(k)
                    if isinstance(v, int):
                        tot[k] += v
                if msg.get("model"):
                    model = msg["model"]
    if turns == 0:
        return None
    duration = int((last_ts - first_ts).total_seconds()) if first_ts and last_ts else None
    meta = read_agent_meta(path)
    agent_type = (meta.get("agentType") or "").split(":")[-1]
    label = (_clean_label(meta.get("description"))
             or _clean_label(agent_type)
             or _clean_label(label)
             or "(no prompt)")
    agent_id = Path(path).stem.replace("agent-", "")[:7]
    return {"agent": agent_id, "model": model, "tot": tot,
            "duration": duration, "label": label}


def subagent_section(agents, ledger_rows, orch_cost):
    """Render '## Subagent detail' (exact split + duration + cost estimate). '' if no agents."""
    if not agents:
        return ""
    lines = [
        "## Subagent detail (exact, from agent transcripts)",
        "",
        "| Agent | Model | In | Out | Cache-w | Cache-r | Duration | Est. cost |",
        "|-------|-------|----|-----|---------|---------|----------|-----------|",
    ]
    sub_cost, unpriced = 0.0, 0
    for a in agents:
        c = estimate_cost(a["model"], a["tot"])
        if c is None:
            unpriced += 1
            cost_cell = "n/a (no price)"
        else:
            sub_cost += c
            cost_cell = "${:,.2f}".format(c)
        t = a["tot"]
        lines.append("| {} ({}) | {} | {:,} | {:,} | {:,} | {:,} | {} | {} |".format(
            a["label"], a["agent"], a["model"] or "unknown",
            t["input_tokens"], t["output_tokens"],
            t["cache_creation_input_tokens"], t["cache_read_input_tokens"],
            _ledger.format_duration(a["duration"]), cost_cell))
    lines.append("")
    if ledger_rows and len(agents) < ledger_rows:
        lines.append("Split covers {} of {} ledger rows; a resumed run's earlier sessions "
                     "are not in this transcript's subagents dir.".format(len(agents), ledger_rows))
        lines.append("")
    bits = ["subagents ${:,.2f}".format(sub_cost)]
    grand = sub_cost
    if orch_cost is not None:
        bits.append("orchestrator ${:,.2f}".format(orch_cost))
        grand += orch_cost
    cost_line = ("**Cost (estimate, list prices as of {}, cache-write at 5m TTL): "
                 "{} = ${:,.2f}.**".format(PRICES_AS_OF, " + ".join(bits), grand))
    if unpriced:
        cost_line += " ({} unpriced row(s) excluded.)".format(unpriced)
    lines.append(cost_line)
    return "\n".join(lines)


def orchestrator_body(path, tot, turns, model=None):
    lines = [
        "- transcript: `{}`  ({} assistant turns)".format(path, turns),
        "- model: {}".format(model or "unknown"),
        "- output tokens (generated): {:,}".format(tot["output_tokens"]),
        "- input tokens (fresh): {:,}".format(tot["input_tokens"]),
        "- cache-write tokens: {:,}".format(tot["cache_creation_input_tokens"]),
        "- cache-read tokens: {:,}".format(tot["cache_read_input_tokens"]),
    ]
    cost = estimate_cost(model, tot)
    if cost is not None:
        lines.append("- est. cost (list prices as of {}, cache-write at 5m TTL): ${:,.2f}"
                     .format(PRICES_AS_OF, cost))
    lines.append(
        "- NOTE: cache-read is the same context re-read each turn (the bulk of a long run); "
        "counts run up to ship time: the last few messages aren't in the transcript yet.")
    return "\n".join(lines)


def run_print(path):
    if not path or not Path(path).is_file():
        print("token_report: no transcript found - orchestrator total unavailable", file=sys.stderr)
        return 1
    parsed = parse_transcript(path)
    if parsed is None:
        print("token_report: no usage records in transcript - orchestrator total unavailable", file=sys.stderr)
        return 1
    tot, turns, model = parsed
    print("## Orchestrator (main thread) - token consumption from session transcript")
    print(orchestrator_body(path, tot, turns, model))
    return 0


def run_write(token_path, transcript, progress=None):
    p = Path(token_path)
    if not p.is_file():
        print("token_report: {} does not exist - run check_tokens.py --init first".format(token_path),
              file=sys.stderr)
        return 1
    text = p.read_text(encoding="utf-8", errors="replace")

    # Ledger-table figures come from the pre-tail text: the table region is untouched
    # by the tail replacement, and this can never re-count the split table's rows.
    tokens_sum = _ledger.sum_data_rows(text)
    compute, n_rows = _ledger.sum_row_durations(text)

    tpath = transcript or find_transcript()
    parsed = parse_transcript(tpath) if tpath and Path(tpath).is_file() else None
    extra = ""
    if parsed is None:
        body = _ledger.UNAVAILABLE
    else:
        tot, turns, model = parsed
        body = orchestrator_body(tpath, tot, turns, model)
        agents = [a for a in (parse_agent_file(f) for f in find_subagent_files(tpath)) if a]
        extra = subagent_section(agents, n_rows, estimate_cost(model, tot))
    text = _ledger.replace_tail(text, body, extra)
    text = _ledger.set_subagents_sum(text, tokens_sum)
    ppath = Path(progress) if progress else p.parent / "progress.md"
    span1 = span2 = None
    if ppath.is_file():
        span1, span2 = parse_progress_spans(ppath.read_text(encoding="utf-8", errors="replace"))
    spans = [s for s in (span1, span2) if s is not None]
    wall = sum(spans) if spans else None
    text = _ledger.set_compute_totals(text, compute, n_rows, wall)

    p.write_text(text, encoding="utf-8")
    # The timing line stays ASCII-only: Windows consoles often run cp1252 and crash on Σ/·.
    print(body)
    print("timing: research+plan={} build+ship={} autonomous-total={} | sum-compute={} across {} dispatches".format(
        _ledger.format_duration(span1), _ledger.format_duration(span2),
        _ledger.format_duration(wall), _ledger.format_duration(compute), n_rows))
    return 0


def main():
    ap = argparse.ArgumentParser(
        description="Sum orchestrator tokens from a session transcript; optionally write them into tokens.md.")
    ap.add_argument("transcript", nargs="?", help="transcript path for print mode (default: auto-detect)")
    ap.add_argument("--write", metavar="TOKENS_MD",
                    help="write the Orchestrator section, Subagents sum, duration totals, and "
                         "per-subagent split into this tokens.md, then exit")
    ap.add_argument("--transcript", dest="transcript_opt", help="explicit transcript path for --write mode")
    ap.add_argument("--progress", dest="progress_opt",
                    help="explicit progress.md path for the wall-clock spans (default: sibling of TOKENS_MD)")
    a = ap.parse_args()
    if a.write:
        return run_write(a.write, a.transcript_opt, a.progress_opt)
    return run_print(a.transcript or find_transcript())


if __name__ == "__main__":
    sys.exit(main())
