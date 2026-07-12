#!/usr/bin/env python3
"""
check_tokens.py: scaffold and verify a feature's tokens.md ledger.

  check_tokens.py --init PATH   # write the template iff absent (idempotent no-op otherwise)
  check_tokens.py PATH          # verify (the close-out gate)

Verify exits 0 iff the ledger is present and structurally finalized (frontmatter
type: Token Ledger, >=1 integer-token row, Subagents sum filled, the Duration column
present with every row's Duration cell and the Σ-compute/wall-clock totals filled,
Orchestrator resolved: a real figure OR the honest "unavailable" sentinel, NOT the
PENDING placeholder). That five-column format is the only one recognized.
Otherwise exit 1 and print the first failing check. A non-zero exit is the hard guardrail:
ship must not mark Phase=done, so the keep-alive loop keeps working the feature. Stdlib only.
Canonical prose for the ledger discipline ("the ledger rule"):
skills/research/references/wit-directory.md, tokens.md template section.
"""
import argparse
import sys
from pathlib import Path

import _ledger


def run_init(path):
    p = Path(path)
    if p.exists():
        return 0  # idempotent: never touch an existing ledger
    p.parent.mkdir(parents=True, exist_ok=True)
    slug = p.parent.name or "feature"
    p.write_text(_ledger.make_template(slug), encoding="utf-8")
    print("check_tokens: scaffolded {}".format(path))
    return 0


def run_verify(path):
    reason = _ledger.verify(path)
    if reason is None:
        print("check_tokens: OK - {}".format(path))
        return 0
    print("check_tokens: FAIL - {} ({})".format(reason, path), file=sys.stderr)
    return 1


def main():
    ap = argparse.ArgumentParser(description="Scaffold (--init) or verify a feature's tokens.md ledger.")
    ap.add_argument("path", help="path to the feature's tokens.md")
    ap.add_argument("--init", action="store_true", help="write the template iff absent, then exit 0")
    a = ap.parse_args()
    return run_init(a.path) if a.init else run_verify(a.path)


if __name__ == "__main__":
    sys.exit(main())
