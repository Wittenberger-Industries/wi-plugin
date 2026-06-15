#!/usr/bin/env python3
"""
token_report.py — sum the main-thread (orchestrator) token usage from a Claude Code
session transcript (JSONL), and optionally write it into a goal's tokens.md.

  token_report.py [TRANSCRIPT.jsonl]      # print the orchestrator report (auto-detects transcript)
  token_report.py --write TOKENS_MD [--transcript T.jsonl]
                                          # finalize: replace the tokens.md Orchestrator
                                          # section + recompute the Subagents (exact) sum

The model can't read its own running total mid-turn, but the harness records a `usage`
object on every assistant message in the session transcript. --write turns the parsed
result into the ledger directly, so there is no manual stdout-copy step to skip. On a
parse failure it writes `Orchestrator: unavailable for this run` — never a substitute,
estimate, or fabricated figure. It does NOT create the file (run check_tokens.py --init
first); --write exits non-zero only if the file is absent or unwritable.

Stdlib only.
"""
import argparse
import json
import sys
from pathlib import Path

import _ledger

FIELDS = ("input_tokens", "output_tokens",
          "cache_creation_input_tokens", "cache_read_input_tokens")


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


def parse_transcript(path):
    """Return (totals, turns) or None if the transcript has no usage records."""
    tot = {k: 0 for k in FIELDS}
    turns = 0
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
    if turns == 0:
        return None
    return tot, turns


def orchestrator_body(path, tot, turns):
    return "\n".join([
        "- transcript: `{}`  ({} assistant turns)".format(path, turns),
        "- output tokens (generated): {:,}".format(tot["output_tokens"]),
        "- input tokens (fresh): {:,}".format(tot["input_tokens"]),
        "- cache-write tokens: {:,}".format(tot["cache_creation_input_tokens"]),
        "- cache-read tokens: {:,}".format(tot["cache_read_input_tokens"]),
        "- NOTE: cache-read is the same context re-read each turn (the bulk of a long run); "
        "counts run up to ship time — the last few messages aren't in the transcript yet.",
    ])


def run_print(path):
    if not path or not Path(path).is_file():
        print("token_report: no transcript found — orchestrator total unavailable", file=sys.stderr)
        return 1
    parsed = parse_transcript(path)
    if parsed is None:
        print("token_report: no usage records in transcript — orchestrator total unavailable", file=sys.stderr)
        return 1
    tot, turns = parsed
    print("## Orchestrator (main thread) — token consumption from session transcript")
    print(orchestrator_body(path, tot, turns))
    return 0


def run_write(token_path, transcript):
    p = Path(token_path)
    if not p.is_file():
        print("token_report: {} does not exist — run check_tokens.py --init first".format(token_path),
              file=sys.stderr)
        return 1
    text = p.read_text(encoding="utf-8", errors="replace")
    tpath = transcript or find_transcript()
    parsed = parse_transcript(tpath) if tpath and Path(tpath).is_file() else None
    if parsed is None:
        body = _ledger.UNAVAILABLE
    else:
        body = orchestrator_body(tpath, *parsed)
    text = _ledger.replace_orchestrator_section(text, body)
    text = _ledger.set_subagents_sum(text, _ledger.sum_data_rows(text))
    p.write_text(text, encoding="utf-8")
    print(body)
    return 0


def main():
    ap = argparse.ArgumentParser(
        description="Sum orchestrator tokens from a session transcript; optionally write them into tokens.md.")
    ap.add_argument("transcript", nargs="?", help="transcript path for print mode (default: auto-detect)")
    ap.add_argument("--write", metavar="TOKENS_MD",
                    help="write the Orchestrator section + Subagents sum into this tokens.md, then exit")
    ap.add_argument("--transcript", dest="transcript_opt", help="explicit transcript path for --write mode")
    a = ap.parse_args()
    if a.write:
        return run_write(a.write, a.transcript_opt)
    return run_print(a.transcript or find_transcript())


if __name__ == "__main__":
    sys.exit(main())
