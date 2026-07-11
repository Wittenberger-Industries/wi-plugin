#!/usr/bin/env python3
"""
now.py: print the OS clock as ISO-8601 with offset, e.g. 2026-07-10T18:23:45+02:00.

The Log-stamp source of truth for progress.md transitions on shells without
`date -Iseconds`. Timestamps are never model-estimated. Stdlib only.
"""
from datetime import datetime

if __name__ == "__main__":
    print(datetime.now().astimezone().isoformat(timespec="seconds"))
