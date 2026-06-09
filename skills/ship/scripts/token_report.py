#!/usr/bin/env python3
"""
token_report.py — sum the main-thread (orchestrator) token usage from a Claude Code
session transcript (JSONL).

The model can't read its own running total mid-turn, but the *harness* records a `usage`
object on every assistant message in the session transcript. This sums those, giving a
real orchestrator figure for `tokens.md` instead of "not metered".

Usage:
    python3 token_report.py [TRANSCRIPT.jsonl]

If no path is given, auto-detects the most recently modified transcript under
~/.claude/projects/ (the active session is the one being written to). Pass an explicit
path when you know it (Claude Code exposes it as `transcript_path`).

Exit 0 + a report on success. Exit non-zero on failure (no transcript / no usage) — the
caller should then report the orchestrator total as UNAVAILABLE for this run and keep the
subagent-exact sum as the headline. Do NOT fall back to any unreliable substitute, and do
NOT fabricate a figure.

Stdlib only.
"""
import json
import sys
from pathlib import Path

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
    # `usage` may be top-level or nested under `message`.
    for u in (obj.get("usage"), (obj.get("message") or {}).get("usage")):
        if isinstance(u, dict):
            return u
    return None


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else find_transcript()
    if not path or not Path(path).is_file():
        print("token_report: no transcript found — orchestrator total unavailable", file=sys.stderr)
        return 1

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
        print("token_report: no usage records in transcript — orchestrator total unavailable", file=sys.stderr)
        return 1

    out = tot["output_tokens"]
    fresh_in = tot["input_tokens"]
    cc = tot["cache_creation_input_tokens"]
    cr = tot["cache_read_input_tokens"]
    print("## Orchestrator (main thread) — token consumption from session transcript")
    print(f"- transcript: `{path}`  ({turns} assistant turns)")
    print(f"- output tokens (generated): {out:,}")
    print(f"- input tokens (fresh): {fresh_in:,}")
    print(f"- cache-write tokens: {cc:,}")
    print(f"- cache-read tokens: {cr:,}")
    print("- NOTE: cache-read is the same context re-read each turn (the bulk of a long run); counts run "
          "up to ship time — the last few messages aren't in the transcript yet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
