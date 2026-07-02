#!/usr/bin/env python3
"""MoA cross-provider check — wi-code-checker's result-mode independent review (issue #12).

Reads the goal project's `.wi/moa.md` (the MoA model-assignment config), and — when a second
provider is configured — sends the diff + spec context to that model, possibly a different
provider/architecture than the session (e.g. GPT via OPENAI_API_KEY), as wi-code-checker's
result-mode check. Writes the findings to a file. Stdlib only; no third-party deps.

Usage:
    python3 moa_review.py --config .wi/moa.md --diff diff.patch \
        [--context spec.md ...] --out review.md

Exit codes:
    0  review ran, verdict `## REVIEW PASSED`
    1  review ran, verdict `## ISSUES FOUND`
    2  config/usage error (bad file, cross-provider not configured, API failure)
    3  no API key in the configured env var — caller falls back to a
       Claude checker-tier review instead
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

PROVIDER_DEFAULTS = {
    "provider": "openai",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-5",
    "api_key_env": "OPENAI_API_KEY",
    "check_points": "at-finish",
}

REVIEW_SYSTEM_PROMPT = (
    "You are an independent third-party code reviewer (MoA Checker). You did not "
    "write this code and you do not negotiate with its author. Review the diff "
    "against the provided spec/context with repo-level impact in mind: correctness, "
    "necessity (redundant or wasteful changes), alignment with the stated intent, "
    "and regressions it could cause elsewhere in the repo. Return markdown findings, "
    "each with a severity — BLOCKER (would break the goal or the repo), WARNING "
    "(real risk needing a decision), or INFO. Cite file:line or hunk for every "
    "finding. End your reply with exactly one verdict marker on its own last line: "
    "`## REVIEW PASSED` if there are no BLOCKERs, else `## ISSUES FOUND`."
)


def _parse_table(lines):
    """Parse a markdown pipe table into a list of row-cell lists (header skipped)."""
    rows = []
    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and set(cells[0]) <= {"-", " ", ":"}:
            continue  # separator row
        rows.append(cells)
    return rows[1:] if rows else []  # drop the header row


def _section(body, heading):
    """Return the lines of a `## heading` section (until the next heading)."""
    pattern = rf"^##\s+{re.escape(heading)}\s*$(.*?)(?=^##\s|\Z)"
    m = re.search(pattern, body, re.MULTILINE | re.DOTALL)
    return m.group(1).splitlines() if m else []


def parse_moa_config(text):
    """Parse `.wi/moa.md` into {preset, roles, cross_provider, overrides}."""
    preset = "custom"
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            body = parts[2]
            m = re.search(r"^preset:\s*(\S+)", parts[1], re.MULTILINE)
            if m:
                preset = m.group(1)

    roles = {}
    for cells in _parse_table(_section(body, "Roles")):
        if len(cells) >= 2:
            roles[cells[0].strip("*` ")] = cells[1].strip("*` ")

    provider = dict(PROVIDER_DEFAULTS)
    for cells in _parse_table(_section(body, "Cross-provider config")):
        if len(cells) >= 2 and cells[1]:
            provider[cells[0].strip("*` ")] = cells[1].strip("*` ")

    overrides = {}
    for cells in _parse_table(_section(body, "Per-agent overrides")):
        if len(cells) >= 2:
            overrides[cells[0].strip("*` ")] = cells[1].strip("*` ")

    return {
        "preset": preset,
        "roles": roles,
        "cross_provider": provider,
        "overrides": overrides,
    }


def cross_provider_configured(cfg):
    """wi-code-checker's cross-provider result-mode path runs only when a provider is named."""
    provider = (cfg or {}).get("cross_provider", {}).get("provider", "none")
    return provider not in ("", "none", "off", "disabled")


def model_for(agent, cfg):
    """Model for a wi-dispatched agent: per-agent override > its own role > inherit."""
    if not cfg:
        return "inherit"
    if agent in cfg.get("overrides", {}):
        return cfg["overrides"][agent]
    return cfg.get("roles", {}).get(agent, "inherit")


def _call_openai(provider, api_key, system, user):
    req = urllib.request.Request(
        provider["base_url"].rstrip("/") + "/chat/completions",
        data=json.dumps(
            {
                "model": provider["model"],
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            }
        ).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.load(resp)
    return data["choices"][0]["message"]["content"]


def _call_anthropic(provider, api_key, system, user):
    base = provider.get("base_url", "https://api.anthropic.com")
    req = urllib.request.Request(
        base.rstrip("/") + "/v1/messages",
        data=json.dumps(
            {
                "model": provider["model"],
                "max_tokens": 8192,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            }
        ).encode(),
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.load(resp)
    return "".join(b.get("text", "") for b in data["content"])


def run_review(cfg, diff_text, context_blobs, out_path):
    provider = cfg["cross_provider"]
    api_key = os.environ.get(provider["api_key_env"], "")
    if not api_key:
        print(
            f"moa_review: no API key in ${provider['api_key_env']} — "
            "fall back to a Claude checker-tier review",
            file=sys.stderr,
        )
        return 3

    user = "\n\n".join(
        ["## Context\n" + "\n\n".join(context_blobs) if context_blobs else "",
         "## Diff under review\n```diff\n" + diff_text + "\n```"]
    ).strip()

    call = _call_anthropic if provider["provider"] == "anthropic" else _call_openai
    try:
        reply = call(provider, api_key, REVIEW_SYSTEM_PROMPT, user)
    except (urllib.error.URLError, KeyError, json.JSONDecodeError, TimeoutError) as e:
        print(f"moa_review: reviewer API call failed: {e}", file=sys.stderr)
        return 2

    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(reply.rstrip() + "\n")
    print(f"moa_review: findings written to {out_path}")
    return 0 if "## REVIEW PASSED" in reply else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", required=True, help="path to .wi/moa.md")
    ap.add_argument("--diff", required=True, help="path to the diff/patch file")
    ap.add_argument("--context", nargs="*", default=[], help="spec/context files")
    ap.add_argument("--out", required=True, help="findings output file")
    args = ap.parse_args(argv)

    try:
        cfg = parse_moa_config(
            open(args.config, encoding="utf-8", errors="replace").read()
        )
    except OSError as e:
        print(f"moa_review: cannot read config: {e}", file=sys.stderr)
        return 2
    if not cross_provider_configured(cfg):
        print(
            "moa_review: cross-provider not configured — nothing to run",
            file=sys.stderr,
        )
        return 2

    try:
        diff_text = open(args.diff, encoding="utf-8", errors="replace").read()
        blobs = [
            f"### {p}\n" + open(p, encoding="utf-8", errors="replace").read()
            for p in args.context
        ]
    except OSError as e:
        print(f"moa_review: cannot read input: {e}", file=sys.stderr)
        return 2

    return run_review(cfg, diff_text, blobs, args.out)


if __name__ == "__main__":
    sys.exit(main())
