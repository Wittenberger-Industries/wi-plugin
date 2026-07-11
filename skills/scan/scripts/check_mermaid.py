#!/usr/bin/env python3
"""Validate the mermaid diagram(s) in a markdown file (wi architecture diagrams).

Catches the real parse-failure classes WITHOUT needing a browser:
  - unclosed ```mermaid fence
  - missing / malformed flowchart header
  - unbalanced subgraph / end
  - node IDs that collide with a mermaid reserved word (graph, end, ...)  <- the common one
  - node labels with special chars (: / -> + ( )) that aren't quoted

If `mmdc` (mermaid-cli) is on PATH, it ALSO does a true render; that is authoritative.
Otherwise the static checks above are the gate.

Usage:  python3 check_mermaid.py <file.md> [more.md ...]
Exit 0 = all good; non-zero = problems printed (one per line).
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

# Reserved/statement keywords that break a flowchart when used as a node ID.
RESERVED = {
    "graph", "end", "subgraph", "flowchart",
    "class", "classdef", "style", "linkstyle", "click", "direction", "default",
}

_ARROW = re.compile(r"-{2,}>|<-{2,}|-\.->|-\.-|={2,}>|-{3,}|={3,}|~~~|--|==|x--x|o--o")
_NODE_DEF = re.compile(r"(?:^|[\s>|&])([A-Za-z_][A-Za-z0-9_]*)\s*(?:\[\(|\(\(|\[/|\[\\|\[|\(|\{)")


def _mermaid_blocks(md):
    return re.findall(r"```mermaid\n(.*?)```", md, re.S)


def _strip_labels(line):
    """Remove bracketed label payloads so only structure + ids remain."""
    prev = None
    while prev != line:
        prev = line
        for pat in (r"\[\([^\]]*\)\]", r"\[/[^\]]*/\]", r"\[\\[^\]]*\\\]",
                    r"\[\[[^\]]*\]\]", r"\[[^\]]*\]", r"\(\([^)]*\)\)",
                    r"\([^)]*\)", r"\{[^}]*\}", r"\|[^|]*\|"):
            line = re.sub(pat, " ", line)
    return line


def _check_block(src):
    errs = []
    lines = src.splitlines()
    nonempty = [l for l in lines if l.strip()]
    if not nonempty:
        return ["empty mermaid block"]

    head = nonempty[0].strip()
    if not re.match(r"^(flowchart|graph)(\s+(TB|TD|BT|RL|LR))?\b", head):
        errs.append(f"header should be 'flowchart TD' / 'graph LR' etc., got: {head!r}")

    sg = sum(1 for l in lines if re.match(r"^\s*subgraph\b", l))
    en = sum(1 for l in lines if re.match(r"^\s*end\s*$", l))
    if sg != en:
        errs.append(f"subgraph/end unbalanced: {sg} subgraph vs {en} end")

    ids = set()
    for l in lines[1:]:
        if re.match(r"^\s*subgraph\b", l):
            m = re.match(r"^\s*subgraph\s+([A-Za-z_][A-Za-z0-9_]*)", l)
            if m:
                ids.add(m.group(1))
            continue
        if re.match(r"^\s*end\s*$", l):
            continue
        for m in _NODE_DEF.finditer(l):
            ids.add(m.group(1))
        stripped = _strip_labels(l)
        if _ARROW.search(stripped):
            ids.update(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", stripped))

    bad = sorted(i for i in ids if i.lower() in RESERVED)
    if bad:
        errs.append(
            "node ID(s) are mermaid reserved words and WILL NOT PARSE: "
            f"{bad} - rename the id (e.g. graph -> gbuild) and keep the real "
            "name in the quoted label"
        )

    # unquoted labels with special chars
    for l in lines:
        for m in re.finditer(r"\[([^\]]*)\]", l):
            payload = m.group(1).strip()
            if not payload or payload[0] in '"' or payload[:2] in ('("', '/"') or payload[:2] == '[(':
                continue
            if re.search(r"[:/>+()]", payload) and '"' not in payload:
                errs.append(f'unquoted label with special chars: [{payload}] -> wrap as ["{payload}"]')
    return errs


def _mmdc_render(block):
    if not shutil.which("mmdc"):
        return None  # not available
    tmp = tempfile.NamedTemporaryFile("w", suffix=".mmd", delete=False)
    tmp.write(block)
    tmp.close()
    out = tmp.name + ".svg"
    try:
        r = subprocess.run(["mmdc", "-i", tmp.name, "-o", out],
                           capture_output=True, text=True, timeout=60)
    except Exception as e:  # noqa: BLE001
        return f"mmdc error: {e}"
    finally:
        for p in (tmp.name, out):
            try:
                os.unlink(p)
            except OSError:
                pass
    return None if r.returncode == 0 else f"mmdc render FAILED: {r.stderr.strip()[:300]}"


def check_file(path):
    md = open(path, encoding="utf-8").read()
    if "```mermaid" in md and not _mermaid_blocks(md):
        return [f"{path}: unclosed ```mermaid fence"]
    blocks = _mermaid_blocks(md)
    if not blocks:
        return []  # no diagram is fine
    errs = []
    for i, b in enumerate(blocks, 1):
        errs += [f"{path} block {i}: {e}" for e in _check_block(b)]
        rendered = _mmdc_render(b)
        if rendered:
            errs.append(f"{path} block {i}: {rendered}")
    return errs


def main(argv):
    if len(argv) < 2:
        print("usage: check_mermaid.py <file.md> [more.md ...]")
        return 2
    all_errs = []
    for p in argv[1:]:
        all_errs += check_file(p)
    if all_errs:
        print("MERMAID INVALID:")
        for e in all_errs:
            print("  -", e)
        return 1
    rendered = "" if not shutil.which("mmdc") else " (+ mmdc render OK)"
    print(f"mermaid OK{rendered}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
